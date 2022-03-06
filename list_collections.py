python3

from pymongo import MongoClient
from gossimer import whati
client = MongoClient('mongodb://localhost:27017/')

with client:    
    db = client.testdb
    print(db.collection_names())
    
    
