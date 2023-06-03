from pymongo import MongoClient

# Connect to the MongoDB server
client = MongoClient('mongodb://localhost:27017')

# Access the database and collection
db = client['your_database_name']
collection = db['your_collection_name']

# Define the query you want to analyze
query = {
    'field': 'value'
}

# Run the query with explain
explain_result = collection.find(query).explain()

# Print the explain plan
print(explain_result)
