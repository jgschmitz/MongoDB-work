# main.py
import os, time, datetime, requests
from google.cloud import storage

ATLAS_PUBLIC_KEY = os.environ["ATLAS_PUBLIC_KEY"]
ATLAS_PRIVATE_KEY = os.environ["ATLAS_PRIVATE_KEY"]
GROUP_ID = os.environ["ATLAS_GROUP_ID"]          # projectId
CLUSTER_NAME = os.environ["ATLAS_CLUSTER_NAME"]  # e.g., Cluster0
HOSTNAME = os.environ["ATLAS_HOSTNAME"]          # e.g., shard-00-00.abc.mongodb.net
LOG_NAME = "mongodb.gz"                          # or "mongodb-audit-log.gz"
GCS_BUCKET = os.environ["GCS_BUCKET"]

def run_job(request=None):
    # Time window (last 10 minutes)
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(minutes=10)
    params = {
        "startDate": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endDate": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "logName": LOG_NAME,
    }
    # v2 Admin API – download logs for a cluster/host
    url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{GROUP_ID}/clusters/{CLUSTER_NAME}/logs/mongodb/{HOSTNAME}"
    r = requests.get(url, params=params, auth=(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY), timeout=60)
    r.raise_for_status()

    blob_path = f"atlas-logs/{CLUSTER_NAME}/{HOSTNAME}/{end:%Y/%m/%d/%H}/" \
                f"{LOG_NAME.replace('.gz','')}-{start:%Y%m%dT%H%M%S}-{end:%Y%m%dT%H%M%S}.gz"
    storage.Client().bucket(GCS_BUCKET).blob(blob_path).upload_from_string(r.content)
    return ("ok", 200)
