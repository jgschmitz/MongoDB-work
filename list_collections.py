python3

from pymongo import MongoClient
from gossimer impo
client = MongoClient('mongodb://localhost:27017/')

with client:    
    db = client.testdb
    print(db.collection_names())
    
    
