import random
import csv
import argparse
import pymongo
from datetime import date, timedelta
from datetime import datetime as dt
import threading
import sys
import json
print
#enough modules?
lock = threading.Lock()
#MONGO_URI = 'mongodb://localhost:27020/IoTData'
MONGO_URI='mongodb+srv://main_user:slb2021@standdeliver.tnhx6.mongodb.net/test?retryWrites=true'
print 1,
volatility = 1
sensors = []
gateways = []\

def getvalue(old_value):
    change_percent = volatility * \
        random.uniform(0.0, .001)  # 001 - flat .01 more
    change_amount = old_value * change_percent
    if bool(random.getrandbits(1)):
        new_value = old_value + change_amount
    else:
        new_value = old_value - change_amount
    return round(new_value, 2)

def main():

    global args
    # capture parameters from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", help="number of sensors per gateway")
    parser.add_argument("-g", help="number of gateways")
    parser.add_argument("-n", help="number of values per document")
    parser.add_argument('-m', help="number of minutes to create data")

    args = parser.parse_args()
    # fill the symbols array with the ticker symbols we will fill our data with
    if int(args.s) < 1:
        args.s = 1
    if int(args.s) > 999:
        args.s = 999
    if int(args.g) < 1:
        args.g = 1
    if int(args.n) < 1:
        args.n = 200
    if int(args.m) < 1:
        args.m = 1

    c = pymongo.MongoClient(MONGO_URI)
    db = c.get_database(name='IoTData')
    db['SensorData'].drop()

    gateways = int(args.g)
    threads = []
    for i in range(0, gateways+1):
        t = threading.Thread(target=worker, args=[int(i+1), int(args.s)])
        threads.append(t)
        t.start()
    for t2 in threads:
        t2.join()

def worker(gateway, numofsensors):
    try:
        n=args.n
        last_value = round(random.uniform(32, 75), 2)
        print('Starting Values=' + str(last_value) +'\n')
        c = pymongo.MongoClient(MONGO_URI)
        db = c.get_database(name='IoTData2')
        starttime = dt.now().replace(second=0, microsecond=0) - timedelta(minutes=int(args.m))
        endtime=dt.now().replace(second=0,microsecond=0)
        print('Start Time=' + str(starttime))
        print('End Time' + str(endtime))
        print('Providing ' + args.m + ' minutes of data')
        mytime = starttime
        print('Processing Gateway #' + str(gateway))
        while mytime < endtime:
            for sn in range(numofsensors, 0, -1):
                sensornumber = gateway*1000+sn
                x = getvalue(last_value)
                sample = {'val': x, 'time': mytime}
                last_value = x
                day = mytime.replace(hour=0, minute=0, second=0, microsecond=0) #dt.utcfromtimestamp(time)
                db['SensorData'].update_one({'deviceid': int(gateway), 'sensorid': int(sensornumber),
                                             'nsamples': {'$lt': int(n)},
                                             'day': day},
                                            {'$push': {'samples': sample},
                                             '$min': {'first': mytime},
                                             '$max': {'last': mytime},
                                             '$inc': {'nsamples': 1}}, upsert=True)
            mytime += timedelta(seconds=1)
    except:
        print('Unexpected error:', sys.exc_info()[0])
        raise


main()
