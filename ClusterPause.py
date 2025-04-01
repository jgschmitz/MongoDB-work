import sys
import requests
from requests.auth import HTTPDigestAuth

# Hardcoded credentials for demo use (⚠️ avoid in production)
ATLAS_PUBLIC_KEY = ""
ATLAS_PRIVATE_KEY = ""
ATLAS_GROUP_ID = ""
ATLAS_CLUSTER_NAME = ""

# Read action (pause/resume)
ACTION = sys.argv[1].lower() if len(sys.argv) > 1 else "pause"

# Atlas REST API URL
URL = f"https://cloud.mongodb.com/api/atlas/v1.0/groups/{ATLAS_GROUP_ID}/clusters/{ATLAS_CLUSTER_NAME}"
HEADERS = {"Content-Type": "application/json"}

def pause_resume_cluster(action):
    body = '{"paused": true}' if action == "pause" else '{"paused": false}'
    response = requests.patch(
        URL,
        headers=HEADERS,
        data=body,
        auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
        timeout=10
    )
    if response.status_code in (200, 202):
        print(f"✅ Cluster {action}d successfully.")
    else:
        print(f"❌ Failed to {action} cluster: {response.status_code}")
        print(response.json())

if ACTION not in ["pause", "resume"]:
    print("Usage: python ClusterPause.py [pause|resume]")
else:
    pause_resume_cluster(ACTION)
