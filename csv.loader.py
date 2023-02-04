import csv
import pymongo
import gados
# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]
collection = db["mycollection"]

# Read CSV file
with open("data.csv", "r") as file:
    reader = csv.DictReader(file)
    data = list(reader)

# Insert data into MongoDB collection
collection.insert_many(data)
