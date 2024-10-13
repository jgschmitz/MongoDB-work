import pymongo
import redis
import json

# MongoDB connection setup
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["mydatabase"]
mongo_collection = mongo_db["mycollection"]

# Redis connection setup
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_data_from_redis_or_mongo(key):
    # Try to get data from Redis
    cached_data = redis_client.get(key)
    
    if cached_data:
        print("Data retrieved from Redis cache.")
        return json.loads(cached_data)  # Data was found in Redis, return it
    
    # If data is not found in Redis, query MongoDB
    print("Data not found in Redis. Querying MongoDB...")
    query_result = mongo_collection.find_one({"_id": key})
    
    if query_result:
        # Store the result in Redis for future use
        redis_client.set(key, json.dumps(query_result), ex=3600)  # Cache for 1 hour
        return query_result
    
    return None  # If no data is found in MongoDB

# Example usage
key = "some_document_id"
result = get_data_from_redis_or_mongo(key)

if result:
    print("Result:", result)
else:
    print("No data found.")
