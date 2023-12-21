import pymongo
from datetime import datetime

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["your_database_name"]
collection = db["query_logs"]

def log_query(query, success, details=""):
    log_entry = {
        "timestamp": datetime.now(),
        "query": query,
        "success": success,
        "details": details
    }
    collection.insert_one(log_entry)

# Example usage
try:
    # Execute your query here
    result = your_database.your_collection.find({})
    log_query("your_database.your_collection.find({})", success=True)
except Exception as e:
    log_query("your_database.your_collection.find({})", success=False, details=str(e))
