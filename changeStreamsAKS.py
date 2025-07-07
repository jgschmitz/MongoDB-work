from pymongo import MongoClient
from pymongo.errors import PyMongoError
import pprint

# Step 1: Connect to both clusters
source_client = MongoClient("mongodb://source-host:27017")
target_client = MongoClient("mongodb://target-host:27017")

source_coll = source_client["appdb"]["claims"]
target_coll = target_client["appdb"]["claims"]

# Step 2: Set up the change stream — optionally filtered by tenantId
pipeline = [
    {
        "$match": {
            "fullDocument.tenantId": "xyz"  # only sync this tenant's changes
        }
    }
]

try:
    print("Watching changes for tenantId = xyz...")
    with source_coll.watch(pipeline=pipeline, full_document="updateLookup") as stream:
        for change in stream:
            pprint.pprint(change)
            
            operation = change["operationType"]
            doc = change["fullDocument"]

            if operation in ("insert", "replace"):
                target_coll.replace_one({ "_id": doc["_id"] }, doc, upsert=True)

            elif operation == "update":
                target_coll.replace_one({ "_id": doc["_id"] }, doc, upsert=True)

            elif operation == "delete":
                target_coll.delete_one({ "_id": change["documentKey"]["_id"] })

except PyMongoError as e:
    print(f"Error in change stream: {e}")
