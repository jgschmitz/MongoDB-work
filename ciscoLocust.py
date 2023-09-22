#!/usr/bin/env python

'''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!   NOTE: THIS SAMPLE IS BUILT USING MIMESIS 11.1.0.
!   IF YOU ARE USING A SCRIPT THAT USES AN OLDER VERSION,
!   YOU NEED TO EITHER UPGRADE YOUR CODE TO MATCH THIS TEMPLATE
!   OR GO INTO THE REQUIREMENTS FILE AND CHANGE THE MIMESIS VERSION
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''

########################################################################
# 
# This is an example Locust file that use Mimesis to help generate
# dynamic documents. Mimesis is more performant than Faker
# and is the recommended solution. After you build out your tasks,
# you need to test your file in mLocust to confirm how many
# users each worker can support, e.g. confirm that the worker's CPU
# doesn't exceed 90%. Once you figure out the user/worker ratio,
# you should be able to figure out how many total workers you'll need
# to satisfy your performance requirements.
#
# These Mimesis locust files can be multi-use, 
# saturating a database with data or demonstrating standard workloads.
#
########################################################################

# Allows us to make many pymongo requests in parallel to overcome the single threaded problem
import gevent
_ = gevent.monkey.patch_all()

########################################################################
# TODO Add any additional imports here.
# TODO But make sure to include in requirements.txt
########################################################################
import pymongo
from bson import json_util
from bson.json_util import loads
from bson import ObjectId
from bson.decimal128 import Decimal128
from locust import User, events, task, constant, tag, between, runners
import time
from pickle import TRUE
from datetime import datetime, timedelta
import random
from decimal import Decimal
import string
from mimesis import Field, Fieldset, Schema
from mimesis.enums import Gender, TimestampFormat
from mimesis.locales import Locale

# Global vars
# We can use this var to track the seq index of the worker in case we want to use it for generating unique seq keys in mimesis
_WORKER_ID = None
# Store the client conn globally so we don't create a conn pool for every user
# Track the srv globally so we know if we need to reinit the client
_CLIENT = None
_SRV = None

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    global _WORKER_ID
    if not isinstance(environment.runner, runners.MasterRunner):
        _WORKER_ID = environment.runner.worker_index

# Mimesis global vars
# TODO Change the locale if needed
_ = Field(locale=Locale.EN)
_FS = Fieldset(locale=Locale.EN)
_SCHEMA = None

class MetricsLocust(User):
    ########################################################################
    # Class variables. 
    # The values are initialized with None
    # till they get set from the actual locust exeuction 
    # when the host param is passed in.
    # DO NOT HARDCODE VARS! PASS THEM IN VIA HOST PARAM.
    # TODO Do you have more than 20 tasks? If so, change the array init below.
    ########################################################################
    client, coll, bulk_size = None, None, None

    def __init__(self, parent):
        global _, _FS, _SCHEMA, _WORKER_ID, _CLIENT, _SRV

        super().__init__(parent)

        try:
            vars = self.host.split("|")
            srv = vars[0]
            print("SRV:",srv)

            isInit = (_SRV != srv)
            if isInit:
                self.client = pymongo.MongoClient(srv)
                _CLIENT = self.client
                _SRV = srv
            else:
                self.client = _CLIENT

            db = self.client[vars[1]]
            self.coll = db[vars[2]]

            # docs to insert per batch insert
            self.bulk_size = int(vars[3])
            print("Batch size from Host:",self.bulk_size)

            # init schema once
            if isInit:
                ########################################################################
                # mimesis schema for bulk creation
                # The zoneKey is a great way to demonstrate zone sharding,
                # e.g. all docs created by worker1 goes into shard1
                # and all docs created by worker2 goes into shard2
                # Note that increment doesn't maintain unique sequence numbers 
                # if you are running multiple mlocust users in parallel on the same worker
                # Not every api func has been used. The full api can be found here. https://mimesis.name/en/master/api.html
                # TODO Only use what you need. The more logic you have the slower your schema generation will be.
                ########################################################################
                # TODO modify how much you want to offset the increment by using the worker id
                # BUILT USING MIMESIS 11.1.0
                _SCHEMA = Schema(
                    schema=lambda: {                      
                        "_id": _("random.generate_string", str_seq="abcdefg123456789", length=8)+"-"+_("random.generate_string", str_seq="abcdefg123456789", length=4),
    "datetime": _("datetime.datetime", start=2000, end=2023),
    "payload": _("random.generate_string", str_seq="abcdefghijklmnopqrstuvwxyz0123456789-#", length=_("numeric.integer_number", start=1000, end=140000))
                    },                    
                    iterations=self.bulk_size
                )
        except Exception as e:
            # If an exception is caught, Locust will show a task with the error msg in the UI for ease
            events.request.fire(request_type="Host Init Failure", name=str(e), response_time=0, response_length=0, exception=e)
            raise e

    ################################################################
    # Example helper function that is not a Locust task.
    # All Locust tasks require the @task annotation
    ################################################################
    def get_time(self):
        return time.time()

    ################################################################
    # Since the loader is designed to be single threaded with 1 user
    # There's no need to set a weight to the task.
    # Do not create additional tasks in conjunction with the loader
    # If you are testing running queries while the loader is running
    # deploy 2 clusters in mLocust with one running faker and the
    # other running query tasks
    # The reason why we don't want to do both loads and queries is
    # because of the simultaneous users and wait time between
    # requests. The bulk inserts can take longer than 1s possibly
    # which will cause the workers to fall behind.
    ################################################################
    @task(1)
    def _bulkinsert(self):
        global _SCHEMA 

        # Note that you don't pass in self despite the signature above
        tic = self.get_time();
        name = "bulkInsert";
 
        try:
            # If you want to do an insert_one, you need to grab the first array element of schema, e.g. (schema*1)[0]
            self.coll.insert_many(_SCHEMA.create(), ordered=False)

            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time()-tic)*1000, response_length=0)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time()-tic)*1000, response_length=0, exception=e)
            # Add a sleep so we don't overload the system with exceptions
            time.sleep(5)
