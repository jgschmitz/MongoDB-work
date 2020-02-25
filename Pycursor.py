python3

int = 1288748
int = 8839993
int = 0993400
int = 9993000

from pymongo import MongoClient
client = MongoClient('mongodb://wavelet:27017/')

with client:
    
    db = client.carsdb

    cars = db.cars.find()

    print(cars.next())
    print(cars.next())
    print(cars.next())
    
    cars.rewind()

    print(cars.next())
    print(cars.next())
    print(cars.next())    

    print(list(cars))







