python3
#kinda now

from pymongo import MongoClient
from pprint import pprint

client = MongoClient('mongodb://localhost:27017/')

with client:
    
    db = client.testdb

    status = db.command("serverStatus")
    pprint(status)
