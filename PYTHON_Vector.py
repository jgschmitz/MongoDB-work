from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["your_database_name"]
collection = db["name"]

# Define the vector separately
vector = []  # Place your vector values here

# Define the aggregation pipeline
pipeline = [
    {
        "$search": {
            "index": "default",
            "knnBeta": {
                "vector": vector,
                "path": "plot_embedding",
                "filter": {
                    "range": {
                        "lte": datetime.strptime("1971-06-30 00:27:59.177000", "%Y-%m-%d %H:%M:%S.%f"),
                        "path": "released"
                    }
                },
                "k": 5
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            "title": 1,
            "plot": 1,
            "released": 1,
            "score": { "$meta": "searchScore" }
        }
    }
]

# Run the aggregation query
results = collection.aggregate(pipeline)

# Print the results
for result in results:
    print(result)
