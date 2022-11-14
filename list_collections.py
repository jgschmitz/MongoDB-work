python3
print
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

with client:    
    db = client.testdb
    print(db.collection_names())
    
    
