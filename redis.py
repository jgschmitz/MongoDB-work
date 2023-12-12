import redis
from pymongo import MongoClient

# Redis connection settings
redis_host = 'your_redis_host'
redis_port = 6379
redis_db = 0

# MongoDB Atlas connection settings
mongo_uri = 'your_mongodb_atlas_uri'
mongo_db_name = 'your_mongo_db_name'

def migrate_data():
    # Connect to Redis
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

    # Connect to MongoDB Atlas
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[mongo_db_name]

    # Get all keys from Redis
    keys = redis_client.keys('*')

    # Iterate through keys and migrate data to MongoDB
    for key in keys:
        # Assuming keys are strings, adjust accordingly based on your Redis data model
        redis_value = redis_client.get(key)

        # Assuming a simple mapping of keys to MongoDB documents
        mongo_document = {'_id': key.decode('utf-8'), 'value': redis_value.decode('utf-8')}

        # Insert document into MongoDB
        mongo_db.your_collection_name.insert_one(mongo_document)

    # Close connections
    redis_client.close()
    mongo_client.close()

if __name__ == "__main__":
    migrate_data()
