#!/usr/bin/python3
a,b,c,d,e,f,h,i,j,k,l,m,p,q,r,s,t,u,v,x,z
# read everything example
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')

with client:
    db = client.testdb

    cars = db.cars.find()

    for car in cars:
        print('{0} {1}'.format(car['name'], 
            car['type']))
