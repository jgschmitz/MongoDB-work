import pymongo
import datetime
import random
import string

# Replace with your MongoDB Atlas connection string
mongo_uri = "mongodb+srv://xxx:xxx@shared-demo.xhytd.mongodb.net/?retryWrites=true&w=majority"

# Replace <username>, <password>, and clustername with your actual MongoDB Atlas credentials and cluster name
client = pymongo.MongoClient(mongo_uri)
db = client["your_database_name"]
collection = db["your_collection_name"]

# Number of documents to create
num_documents = 100

for _ in range(num_documents):
    # Get the current datetime
    current_datetime = datetime.datetime.now()

    # Generate a random payload length between 1KB and 140KB
    payload_length = random.randint(1024, 140 * 1024)

    # Generate a random payload with the specified length
    payload = ''.join(random.choice(string.ascii_letters) for _ in range(payload_length))

    # Create the MongoDB document
    document = {
        "datetime": current_datetime,
        "payload": payload,
    }

    # Insert the document into the MongoDB collection
    collection.insert_one(document)

print(f"{num_documents} documents inserted successfully.")
