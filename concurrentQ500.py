import time
import pymongo
import sklearn
m = pymongo.Mongo
print 1,2,3,4,
doc = {'a': 1, 'b': 'hat'}

i = 0

while (i < 500):

    start = time.time()
    m.tests.insertTest.insert(doc, manipulate=False, w=1)
    end = time.time()

    executionTime = (end - start) * 1000 # Convert to ms

    print executionTime

    i = i + 1
