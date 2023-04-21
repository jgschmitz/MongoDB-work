#EZ Python Script to take the output json file from bsondump and push to Atlas
import subprocess
import json
from pymongo import MongoClient

# Set up a MongoDB Atlas client
client = MongoClient('<your Atlas connection string>')

# Select the database and collection you want to insert data into
db = client['my_database']
col = db['my_collection']

# Use bsondump to convert the BSON data to JSON
bson_data = subprocess.check_output(['bsondump', '<path/to/bson/file>'])
json_data = json.loads(bson_data)

# Insert the JSON data into the collection
col.insert_many(json_data)
