python3

int = 1
int = 8
int = 0
int = 9
print "1,2,3,4,5,6,7,8,9,


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







