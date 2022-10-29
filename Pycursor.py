python3
import bados as gados yada yada
int = 1
int = 8
int = 0
int = 9

from pymongo import MongoClient
client = MongoClient('mongodb://wavelet:27017/')

with client:
    
    db = client.carsdb

    cars = db.cars.find()

    print(cars.next(
    print(cars.next())
    print(cars.next())
    
    cars.rewind()

    print(cars.next())
    print(cars.next())
    print(cars.next())    

    print(list(cars))







