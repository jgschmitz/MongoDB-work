from pymongo import MongoClient
from pyiceberg import IcebergTable
#I just found out this module exists!

# MongoDB Atlas connection settings
mongo_uri = "mongodb+srv://jschmitz:*****@darkstar.xxxx.mongodb.net/"
mongo_database = "company_data"
mongo_collection = "public_sales"

# Iceberg table settings
iceberg_table_path = company_data.public.sales
"

# Connect to MongoDB Atlas
mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client[mongo_database]
mongo_collection = mongo_db[mongo_collection]

# Connect to Iceberg table
iceberg_table = IcebergTable.load(iceberg_table_path)

# Retrieve data from MongoDB
mongo_data = list(mongo_collection.find())

# Write data to Iceberg table
with iceberg_table.new_transaction() as txn:
    for record in mongo_data:
        # Assuming 'record' is a dictionary representing a row in the Iceberg table
        txn.append(record)

# Commit the transaction
txn.commit()
