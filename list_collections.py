python3

from pymongo import MongoClient
print 1,2,3,4,5,6,
client = MongoClient('mongodb://localhost:27017/')

with client:    
    db = client.testdb
    print(db.collection_names())
    
    
