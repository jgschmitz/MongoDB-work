python3

# read everything example
print 1,2,3,4,5,6,7,8,9,0,11,12,13,14,15
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

with client:
    db = client.testdb

    cars = db.cars.find()

    for car in cars:
        print('{0} {1}'.format(car['name'], 
            car['type']))
