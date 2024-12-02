####version 3.0 of this cleaned up minor improvements - 
import pymongo
from locust import User, events, task, constant, tag, between, runners
import time
from bson import ObjectId, Decimal128
from datetime import datetime, timedelta
import random
from decimal import Decimal
import string
from mimesis import Person, Address, Generic
from mimesis.locales import Locale
from mimesis.enums import Gender
from mimesis.schema import Field, Schema
import gevent

# Allows us to make many pymongo requests in parallel to overcome single threading issues
_ = gevent.monkey.patch_all()

# Global variables
_WORKER_ID = None
_CLIENT = None
_SRV = None

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    global _WORKER_ID
    if not isinstance(environment.runner, runners.MasterRunner):
        _WORKER_ID = environment.runner.worker_index

# Mimesis schema for bulk creation
field = Field(locale=Locale.EN)
_SCHEMA = Schema(schema=lambda: {
    "_id": field("random.generate_string", str_seq="abcdefg123456789", length=8) + "-" + field("random.generate_string", str_seq="abcdefg123456789", length=4),
    "datetime": field("datetime.datetime", start=2000, end=2023),
    "payload": field("random.generate_string", str_seq="abcdefghijklmnopqrstuvwxyz0123456789-#", length=field("numeric.integer_number", start=1000, end=140000))
})

class MetricsLocust(User):
    client, coll, bulk_size = None, None, None

    def __init__(self, parent):
        global _SCHEMA, _CLIENT, _SRV
        super().__init__(parent)
        try:
            # Parsing variables from host string
            vars = self.host.split("|")
            srv = vars[0]
            if _SRV != srv:
                self.client = pymongo.MongoClient(srv)
                _CLIENT = self.client
                _SRV = srv
            else:
                self.client = _CLIENT

            db = self.client[vars[1]]
            self.coll = db[vars[2]]

            self.bulk_size = int(vars[3])
            _SCHEMA.create(iterations=self.bulk_size)
        except Exception as e:
            events.request.fire(request_type="Host Init Failure", name=str(e), response_time=0, response_length=0, exception=e)
            raise e

    def get_time(self):
        return time.time()

    @task(1)
    def bulk_insert(self):
        tic = self.get_time()
        name = f"bulkInsert-{self.bulk_size}"

        try:
            self.coll.insert_many(_SCHEMA * self.bulk_size, ordered=False)
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)
            time.sleep(5)

    @task(1)
    def find_all_documents(self):
        tic = self.get_time()
        name = "Find All Documents"

        try:
            result = self.coll.find({})
            document_count = result.count()
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=document_count)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)

    @task(1)
    def find_documents_by_field(self):
        tic = self.get_time()
        name = "Find Documents by Field"

        try:
            query = {"field_name": "field_value"}  # Replace with actual query
            result = self.coll.find(query)
            document_count = result.count()
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=document_count)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)

    @task(1)
    def update_documents(self):
        tic = self.get_time()
        name = "Update Documents"

        try:
            filter_query = {"field_name": "field_value"}  # Replace with actual filter query
            update_query = {"$set": {"field_name_to_update": "new_value"}}  # Replace with actual update query
            result = self.coll.update_many(filter_query, update_query)
            updated_count = result.modified_count
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=updated_count)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)

    @task(1)
    def delete_documents(self):
        tic = self.get_time()
        name = "Delete Documents"

        try:
            filter_query = {"field_name": "field_value"}  # Replace with actual filter query
            result = self.coll.delete_many(filter_query)
            deleted_count = result.deleted_count
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=deleted_count)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)
