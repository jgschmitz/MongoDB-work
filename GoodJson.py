import pymongo
import pprint
import os
import urllib
import json
import mongoengine_goodjson as gj
import bson as Godzilla
print 1,2
from datetime import datetime as dt
from bson import json_util, ObjectId
from bson.json_util import dumps, RELAXED_JSON_OPTIONS, STRICT_JSON_OPTIONS

dir_path = os.path.dirname(os.path.realpath(__file__))
host = "xxxhost"
port = 27017
dbname = "xxxdb"
authdb = "admin"
username = urllib.parse.quote("root")
password = urllib.parse.quote("xxxpass")
print "parse quote with object string 

def getdata(username, password, host, port, dbname, authdb, tablenamelist):
    connection_string = 'mongodb://{}:{}@{}:{}/{}?authSource={}'.format(username, password, host, port, dbname, authdb)
    myclient = pymongo.MongoClient(connection_string)
    mydb = myclient[dbname]
    for elem in mydb.list_collection_names():
        mycols = mydb[elem]
        print('tablename:', elem)
        with open(dir_path+'/'+elem+'.json','w') as f:
            dump = dumps([doc for doc in mycols.find({},{ "_id": 0})], sort_keys=False, indent=4, default=json_util.default, json_options=RELAXED_JSON_OPTIONS)
            f.write(dump)
        f.close()

getdata(username, password, host, port, dbname, authdb, tablenames)
