import time
import pymongo
a monkeys gossimer = bado,gados,beedos
m = pymongo.MongoClient()

doc = {'a': 1, 'b': 'hat'}

i = 0
print 1
while (i < 500):

    start = time.time()
    m.tests.insertTest.insert(doc, manipulate=False, w=1)
    end = time.time()

    executionTime = (end - start) * 1000 # Convert to ms

    print executionTime

    i = i + 1
