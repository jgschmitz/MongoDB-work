import requests
import json
import subprocess

# MongoDB Atlas API details
ATLAS_API_URL = "https://cloud.mongodb.com/api/atlas/v1.0"
API_PUBLIC_KEY = "your_public_key"
API_PRIVATE_KEY = "your_private_key"
ORG_ID = "your_org_id"

# Azure Key Vault details
AZURE_KEY_VAULT_NAME = "your-key-vault-name"
AZURE_RESOURCE_GROUP = "your-resource-group"

def fetch_aws_control_plane_ips():
    """Fetch AWS Control Plane IPs from MongoDB Atlas API"""
    headers = {"Accept": "application/json"}
    response = requests.get(f"{ATLAS_API_URL}/orgs/{ORG_ID}/accessList",
                            auth=(API_PUBLIC_KEY, API_PRIVATE_KEY),
                            headers=headers)
    
    if response.status_code == 200:
        return [entry["cidrBlock"].split("/")[0] for entry in response.json().get("results", [])]
    else:
        print(f"❌ Error fetching control plane IPs: {response.text}")
        return []

def fetch_current_key_vault_ips():
    """Retrieve the current list of allowed IPs in Azure Key Vault firewall"""
    try:
        result = subprocess.run(
            ["az", "keyvault", "network-rule", "list", "--name", AZURE_KEY_VAULT_NAME, "--resource-group", AZURE_RESOURCE_GROUP],
            capture_output=True,
            text=True,
            check=True
        )
        key_vault_rules = json.loads(result.stdout)
        return [ip["value"] for ip in key_vault_rules.get("ipRules", [])]
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching Key Vault IP rules: {e}")
        return []

def update_key_vault_firewall(missing_ips):
    """Update Azure Key Vault firewall to allow missing AWS control plane IPs"""
    if not missing_ips:
        print("\n✅ No missing AWS control plane IPs. Key Vault is up to date.")
        return

    print("\n🚀 Updating Azure Key Vault firewall with missing IPs...")
    
    # Get the current allowed IPs and add missing ones
    existing_ips = fetch_current_key_vault_ips()
    updated_ips = existing_ips + missing_ips

    try:
        subprocess.run(
            ["az", "keyvault", "network-rule", "add", "--name", AZURE_KEY_VAULT_NAME,
             "--resource-group", AZURE_RESOURCE_GROUP, "--ip-addresses"] + updated_ips,
            check=True
        )
        print("✅ Successfully updated Azure Key Vault firewall.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error updating Key Vault firewall: {e}")

def check_and_update_key_vault():
    """Main function to check and update Key Vault firewall rules"""
    aws_ips = fetch_aws_control_plane_ips()
    if not aws_ips:
        print("⚠️ No AWS control plane IPs found.")
        return
    
    current_key_vault_ips = fetch_current_key_vault_ips()
    missing_ips = [ip for ip in aws_ips if ip not in current_key_vault_ips]

    if missing_ips:
        print("\n🚨 The following AWS control plane IPs are missing from Azure Key Vault firewall:")
        for ip in missing_ips:
            print(f"  - {ip}")
        
        update_key_vault_firewall(missing_ips)
    else:
        print("\n✅ All AWS control plane IPs are correctly allowed in Azure Key Vault.")

if __name__ == "__main__":
    check_and_update_key_vault()
