import pymongo
from locust import User, events, task, constant, tag, between, runners
import time
from bson import ObjectId
from bson.decimal128 import Decimal128
from datetime import datetime, timedelta
import random
from decimal import Decimal
import string
from mimesis import Person
from mimesis.locales import Locale
from mimesis.enums import Gender
from mimesis import Address
from mimesis import Generic
from mimesis.schema import Field, Schema

# Allows us to make many pymongo requests in parallel to overcome the single threaded problem
import gevent
_ = gevent.monkey.patch_all()

# Global vars
_WORKER_ID = None
_CLIENT = None
_SRV = None

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    global _WORKER_ID
    if not isinstance(environment.runner, runners.MasterRunner):
        _WORKER_ID = environment.runner.worker_index

# Mimesis schema for bulk creation
_ = Field(locale=Locale.EN)
_SCHEMA = Schema(schema=lambda: {
    "_id": _("random.generate_string", str_seq="abcdefg123456789", length=8)+"-"+_("random.generate_string", str_seq="abcdefg123456789", length=4),
    "datetime": _("datetime.datetime", start=2000, end=2023),
    "payload": _("random.generate_string", str_seq="abcdefghijklmnopqrstuvwxyz0123456789-#", length=_("numeric.integer_number", start=1000, end=140000))
})

class MetricsLocust(User):
    client, coll, bulk_size = None, None, None

    def __init__(self, parent):
        global _SCHEMA, _CLIENT, _SRV

        super().__init__(parent)

        try:
            vars = self.host.split("|")
            srv = vars[0]
            print("SRV:", srv)
            if _SRV != srv:
                self.client = pymongo.MongoClient(srv)
                _CLIENT = self.client
                _SRV = srv
            else:
                self.client = _CLIENT

            db = self.client[vars[1]]
            self.coll = db[vars[2]]

            self.bulk_size = int(vars[3])
            print("Batch size from Host:", self.bulk_size)
            _SCHEMA.create(iterations=self.bulk_size)
        except Exception as e:
            events.request.fire(request_type="Host Init Failure", name=str(e), response_time=0, response_length=0, exception=e)
            raise e

    def get_time(self):
        return time.time()

    @task(1)
    def _bulkinsert(self):
        global _SCHEMA 

        tic = self.get_time()
        name = "bulkInsert-" + str(self.bulk_size);

        try:
            self.coll.insert_many(_SCHEMA*self.bulk_size, ordered=False)
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time()-tic)*1000, response_length=0)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time()-tic)*1000, response_length=0, exception=e)
            time.sleep(5)

    @task(1)
    def _find_all_documents(self):
        tic = self.get_time()
        name = "Find All Documents"

        try:
            result = self.coll.find({})
            document_count = result.count()
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=document_count)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)

    @task(1)
    def _find_documents_by_field(self):
        tic = self.get_time()
        name = "Find Documents by Field"

        try:
            query = {"field_name": "field_value"}  # Replace with your query
            result = self.coll.find(query)
            document_count = result.count()
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=document_count)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)

    @task(1)
    def _update_documents(self):
        tic = self.get_time()
        name = "Update Documents"

        try:
            filter_query = {"field_name": "field_value"}  # Replace with your filter query
            update_query = {"$set": {"field_name_to_update": "new_value"}}  # Replace with your update query
            result = self.coll.update_many(filter_query, update_query)
            updated_count = result.modified_count
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=updated_count)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)

    @task(1)
    def _delete_documents(self):
        tic = self.get_time()
        name = "Delete Documents"

        try:
            filter_query = {"field_name": "field_value"}  # Replace with your filter query
            result = self.coll.delete_many(filter_query)
            deleted_count = result.deleted_count
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=deleted_count)
        except Exception as e:
            events.request.fire(request_type="mlocust", name=name, response_time=(self.get_time() - tic) * 1000, response_length=0, exception=e)
