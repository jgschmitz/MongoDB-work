import pymongo

# Connect to the MongoDB database
client = pymongo.MongoClient("mongodb://localhost:27017/")

# Get a list of all collections in the database
collections = client.list_collection_names()

# Create a dictionary to store the number of documents in each collection
collection_counts = {}

# Loop over the collections and count the number of documents in each one
for collection_name in collections:
    collection = client[collection_name]
    count = collection.count_documents({})
    collection_counts[collection_name] = count

# Sort the collections by the number of documents and print the result
sorted_collections = sorted(collection_counts.items(), key=lambda x: x[1], reverse=True)
for collection_name, count in sorted_collections:
    print(f"{collection_name}: {count} documents")
