import openai

# Set your OpenAI API key
openai.api_key = "your-openai-api-key"

# Example log entries
log_entries = [
    # Existing logs
    "Oct 20 10:12:34 firewall01 PAN-OS: threat log - High severity - Detected malicious IP traffic from source IP 192.168.1.100 to destination IP 203.0.113.5 on port 443 (SSL).",
    "Oct 20 11:05:22 firewall01 PAN-OS: system log - Warning - Interface eth1/2 experiencing high packet loss, possible network congestion.",
    "Oct 20 11:48:19 firewall01 PAN-OS: system log - Error - Failed to update antivirus signatures. Last successful update was 24 hours ago.",
    
    # Additional log entries
    "Oct 21 09:33:10 firewall01 PAN-OS: threat log - Medium severity - Attempted brute force login from IP 192.168.2.50.",
    "Oct 21 10:45:55 firewall02 PAN-OS: system log - Error - Configuration sync failed between primary and secondary firewall.",
    "Oct 21 12:20:05 firewall01 PAN-OS: system log - Warning - High CPU usage detected on management interface.",
    "Oct 21 14:15:30 firewall03 PAN-OS: threat log - High severity - Detected ransomware traffic from source IP 10.0.0.5.",
    "Oct 21 15:55:45 firewall01 PAN-OS: system log - Error - Failed to establish VPN tunnel with remote site.",
    "Oct 21 16:22:12 firewall02 PAN-OS: system log - Warning - DHCP server experiencing high latency.",
    "Oct 21 18:40:00 firewall01 PAN-OS: threat log - Critical severity - Multiple port scans detected from IP 198.51.100.10.",
    "Oct 21 20:00:00 firewall02 PAN-OS: system log - Error - License activation failed due to network timeout.",
    "Oct 21 21:25:33 firewall03 PAN-OS: system log - Warning - Interface eth0/1 down due to cable disconnection.",
    "Oct 21 22:10:00 firewall01 PAN-OS: threat log - Medium severity - Unusual outbound traffic patterns detected, possible data exfiltration.",
]

def categorize_log_entry(log_entry):
    prompt = f"Categorize the following firewall log entry into one of these categories: Security Issue, Performance Warning, Error.\n\nLog Entry: \"{log_entry}\"\n\nCategory:"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that categorizes firewall log entries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        n=1,
        stop=None,
        temperature=0.3,
    )
    
    # Strip any existing "Category:" from the model response
    category = response.choices[0].message['content'].strip()
    if category.lower().startswith("category:"):
        category = category[len("category:"):].strip()
    
    return category

# Loop through log entries and categorize them
for log_entry in log_entries:
    category = categorize_log_entry(log_entry)
    print(f"Log Entry: {log_entry}\nCategory: {category}\n")
