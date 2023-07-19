import boto3
from pymongo import MongoClient

# Step 1: Retrieve data from Amazon S3
def retrieve_data_from_s3(bucket_name, object_key):
    s3_client = boto3.client('s3', region_name='us-east-1')
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    return response['Body'].read()

# Step 2: Process the data if needed (e.g., decompress, convert to JSON, etc.)
def process_data(data_from_s3):
    # Process data_from_s3 as per the specific format of your data
    # For example, decompress and parse JSON if it's compressed JSON
    return processed_data

# Step 3: Connect to MongoDB Atlas
def connect_to_mongodb(connection_string):
    return MongoClient(connection_string)

# Step 4: Insert the data into MongoDB Atlas
def insert_data_into_mongodb(mongo_client, database_name, collection_name, data):
    db = mongo_client[database_name]
    collection = db[collection_name]
    result = collection.insert_many(data)  # Use insert_one if the data is a single document
    return result.inserted_ids

if __name__ == "__main__":
    # Replace these variables with your actual values
    s3_bucket_name = 'my-s3-bucket'
    s3_object_key = 'path/to/s3/data.json.gz'
    mongodb_connection_string = "<YOUR_CONNECTION_STRING>"
    mongodb_database_name = 'my_database'
    mongodb_collection_name = 'my_collection'

    data_from_s3 = retrieve_data_from_s3(s3_bucket_name, s3_object_key)
    processed_data = process_data(data_from_s3)

    mongo_client = connect_to_mongodb(mongodb_connection_string)
    inserted_ids = insert_data_into_mongodb(mongo_client, mongodb_database_name, mongodb_collection_name, processed_data)

    print("Data inserted successfully:", inserted_ids)
