import requests

# Replace these with your actual API settings
API_ENDPOINT = "https://cloud.mongodb.com/api/atlas/v1.0"
PUBLIC_KEY = "your-public-key"
PRIVATE_KEY = "your-private-key"
PROJECT_ID = "your-project-id"
CLUSTER_NAME = "your-cluster-name"

# Construct the URL for fetching cluster information
url = f"{API_ENDPOINT}/groups/{PROJECT_ID}/clusters/{CLUSTER_NAME}"

# Set up the headers for authentication
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Digest {PUBLIC_KEY}:{PRIVATE_KEY}"
}

# Send the GET request to fetch cluster information
response = requests.get(url, headers=headers)

if response.status_code == 200:
    cluster_info = response.json()
    
    # Extract and print relevant health information
    cluster_health = cluster_info.get("stateName")
    print(f"Cluster Health: {cluster_health}")
    
else:
    print(f"Failed to fetch cluster information. Status code: {response.status_code}")
