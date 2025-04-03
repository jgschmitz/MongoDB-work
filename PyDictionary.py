from pymongo import MongoClient
from collections import defaultdict
import pandas as pd
import datetime

# ---- CONFIG ----
MONGO_URI = "mongodb+srv://<your-username>:<your-password>@<cluster>.mongodb.net"
DB_NAME = "your_db_name"
SAMPLE_SIZE = 1000
OUTPUT_FORMAT = "csv"  # "csv" or "md"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def infer_type(value):
    if isinstance(value, dict):
        return "object"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, bool):
        return "bool"
    elif value is None:
        return "null"
    else:
        return type(value).__name__

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, infer_type(v)))
    return dict(items)

schema_summary = []

for collection_name in db.list_collection_names():
    collection = db[collection_name]
    field_types = defaultdict(set)
    
    print(f"Sampling {SAMPLE_SIZE} docs from '{collection_name}'...")
    for doc in collection.aggregate([{ "$sample": { "size": SAMPLE_SIZE } }]):
        flat_doc = flatten_dict(doc)
        for field, field_type in flat_doc.items():
            field_types[field].add(field_type)

    for field, types in field_types.items():
        schema_summary.append({
            "collection": collection_name,
            "field": field,
            "types": ', '.join(sorted(types))
        })

# ---- Export ----
df = pd.DataFrame(schema_summary)
timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d")

if OUTPUT_FORMAT == "csv":
    df.to_csv(f"mongo_schema_{timestamp}.csv", index=False)
elif OUTPUT_FORMAT == "md":
    with open(f"mongo_schema_{timestamp}.md", "w") as f:
        f.write(df.to_markdown(index=False))

print("✅ Schema export complete.")
