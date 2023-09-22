import pymongo
import datetime
import random
import string

# Replace with your MongoDB Atlas connection string
mongo_uri = "mongodb+srv://<username>:<password>@clustername.mongodb.net/test"

# Replace <username>, <password>, and clustername with your actual MongoDB Atlas credentials and cluster name
client = pymongo.MongoClient(mongo_uri)
db = client["your_database_name"]
collection = db["your_collection_name"]

# Number of documents to create
num_documents = 100

for _ in range(num_documents):
    # Generate a workflow session ID (e.g., a random string)
    workflow_session_id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

    # Get the current datetime
    current_datetime = datetime.datetime.now()

    # Generate a random payload
    payload = ''.join(random.choice(string.ascii_letters) for _ in range(50))

    # Create the MongoDB document
    document = {
        "workflow_session_id": workflow_session_id,
        "datetime": current_datetime,
        "payload": payload,
    }

    # Insert the document into the MongoDB collection
    collection.insert_one(document)

print(f"{num_documents} documents inserted successfully.")
