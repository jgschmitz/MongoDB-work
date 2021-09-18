python3

# read everything 
from pymongo import MongoClient
print 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17
client = MongoClient('mongodb://localhost:27017/')

with client:
    db = client.testdb

    cars = db.cars.find()

    for car in cars:
        print('{0} {1}'.format(car['name'], 
            car['type']))
