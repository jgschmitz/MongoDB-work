import subprocess
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Function to run Nmap and detect MongoDB instances
def run_nmap_scan(subnet):
    print(f"[+] Running Nmap scan on {subnet}...")
    try:
        result = subprocess.run(
            ["nmap", "-p", "27017", "--open", subnet],
            capture_output=True,
            text=True
        )
        # Regex to extract IP addresses with port 27017 open
        ips = re.findall(r"(\d+\.\d+\.\d+\.\d+)", result.stdout)
        hosts = [f'mongodb://{ip}:27017' for ip in set(ips)]
        print(f"[+] Found MongoDB instances: {hosts}")
        return hosts
    except Exception as e:
        print(f"[-] Error running Nmap scan: {e}")
        return []

# Function to check for enterprise-only features
def check_mongodb_features(uri):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.server_info()  # Force connection to check if host is reachable
        
        db = client.admin
        
        # Attempt to detect LDAP/Kerberos (Enterprise-only features)
        auth_mechanisms = db.command({'getParameter': 1, 'authenticationMechanisms': 1})
        has_ldap = any(mech in auth_mechanisms.get('authenticationMechanisms', []) for mech in ['PLAIN', 'GSSAPI'])
        
        # Attempt to detect auditing
        try:
            audit_log = db.command({'getParameter': 1, 'auditLog': 1})
            has_audit = 'auditLog' in audit_log
        except OperationFailure:
            has_audit = False
        
        # Attempt to detect encryption at rest (Enterprise-only feature)
        try:
            encryption_info = db.command({'getParameter': 1, 'encryptionAtRestMode': 1})
            has_encryption = encryption_info.get('encryptionAtRestMode', None) is not None
        except OperationFailure:
            has_encryption = False
        
        # Infer edition
        if has_ldap or has_audit or has_encryption:
            edition = 'Likely Enterprise Edition'
        else:
            edition = 'Likely Community Edition'
        
        print(f"[+] {uri}: {edition}")
        print(f"    LDAP: {has_ldap}, Audit: {has_audit}, Encryption: {has_encryption}")
    except ConnectionFailure:
        print(f"[-] Could not connect to {uri}")
    except OperationFailure as e:
        print(f"[-] Operation failed on {uri}: {e}")
    except Exception as e:
        print(f"[-] Unexpected error on {uri}: {e}")

# Main execution logic
def main():
    subnet = input("Enter the subnet to scan (e.g., 192.168.1.0/24 or 'localhost' for local scan): ")
    if subnet.lower() in ["localhost", "127.0.0.1"]:
        hosts = ['mongodb://127.0.0.1:27017']
    else:
        hosts = run_nmap_scan(subnet)
    
    if hosts:
        print("[+] Starting MongoDB Edition Checks...")
        for host in hosts:
            check_mongodb_features(host)
    else:
        print("[-] No MongoDB instances detected.")

if __name__ == "__main__":
    main()
