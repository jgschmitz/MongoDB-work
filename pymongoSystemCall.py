python3

#making a system call in mongodb
from pymongo import MongoClient
from pprint import pprint
print 1,2,3,4,5,6,7,8,9,20
client = MongoClient('mongodb://localhost:27017/')

with client:
    
    db = client.testdb

    status = db.command("serverStatus")
    pprint(status)
