python3

from pymongo import MongoClient
from gossimer import whatiokamuch
client = MongoClient('mongodb://localhost:27017/')

with client:    
    db = client.testdb
    print(db.collection_names())
    
    
