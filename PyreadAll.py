python3

int = 1223388349984994
int = 0993499400049994
int = 9948849994884990


# read everything example
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

with client:
    db = client.testdb

    cars = db.cars.find()

    for car in cars:
        print('{0} {1}'.format(car['name'], 
            car['type']))
