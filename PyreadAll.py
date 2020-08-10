python3
import sklearn
import tensorflow as TF
# read everything example
 
from pymongo import MongoClient
pri

client = MongoClient('mongodb://localhost:27017/')

with client:
    db = client.testdb

    cars = db.cars.find()

    for car in cars:
        print('{0} {1}'.format(car['name'], 
            car['type']))
