python3

int = 12887
int = 88399
int = 09934
int = 99930

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







