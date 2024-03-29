import time
import datetime
from timeit import default_timer as timer
from pymongo import MongoClient
from faker import Faker
from bson.decimal128 import Decimal128

fake = Faker()

####
# Start script
####
startTs = time.gmtime()
start = timer()
print("================================")
print("   Generating Sample IoT Data   ")
print("================================")
print("\nStarting " + time.strftime("%Y-%m-%d %H:%M:%S", startTs) + "\n")

####
# Main start function
####
def main():
    print('NUM DOCS TO GENERATE: ' + str(NUM_DOCS))

    mongo_client = MongoClient(MDB_CONNECTION)
    db = mongo_client[MDB_DATABASE]
    my_collection = db[MDB_COLLECTION]

    for index in range(int(NUM_DOCS)):
        # create timestamp
        fake_timestamp = fake.date_this_year()

        # Define IoT Document
        my_iot_document = {
            "username": fake.user_name(),
            "remote_ipv4": fake.ipv4(),
            "httpMethod": fake.http_method(),
            "hostName": fake.hostname(),
            "portNum": fake.port_number(),
            "location": {
                    "type": "Point",
                    "coordinates": [
                        Decimal128(fake.longitude()),
                        Decimal128(fake.latitude())
                    ]
            },
            "dateAccessed": datetime.datetime(fake_timestamp.year, fake_timestamp.month, fake_timestamp.day)
        }
        print(my_iot_document)
        my_collection.insert_one(my_iot_document)

####
# Constants loaded from .env file
####
#MDB_CONNECTION = "mongodb+srv://jschmitz:xxxxx@bakerhughes.tnhx6.mongodb.net/"
MDB_DATABASE = test
##MDB_COLLECTION = my_collection
MDB_DATABASE = test
##MDB_COLLECTION = my_collection
NUM_DOCS = 100000000

####
# Main
####
if __name__ == '__main__':
    main()

###
# Indicate end of script
####
end = timer()
endTs = time.gmtime()
print("\nEnding " + time.strftime("%Y-%m-%d %H:%M:%S", endTs))
print('===============================')
print('Total Time Elapsed (in seconds): ' + str(end - start))
print('===============================')

