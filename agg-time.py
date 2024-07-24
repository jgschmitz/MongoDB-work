from pymongo import MongoClient

# Initialize MongoDB client
client = MongoClient('mongodb://atlas_uri:27017/')
db = client['your_database']

# Collection references
regular_collection = db['regular_collection']
time_series_collection = db['time_series_collection']

# Aggregation pipeline for the regular collection
regular_pipeline = [
    {"$match": {"status": "active"}},
    {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}}
]

# Aggregation pipeline for the time-series collection
time_series_pipeline = [
    {"$match": {"timestamp": {"$gte": ISODate("2024-01-01T00:00:00Z")}}},
    {"$group": {"_id": "$category", "average": {"$avg": "$value"}}}
]

# Execute aggregations
regular_results = list(regular_collection.aggregate(regular_pipeline))
time_series_results = list(time_series_collection.aggregate(time_series_pipeline))

# Combine results
combined_results = []
for reg_doc in regular_results:
    for ts_doc in time_series_results:
        if reg_doc['_id'] == ts_doc['_id']:
            combined_doc = {
                "category": reg_doc['_id'],
                "total": reg_doc['total'],
                "average": ts_doc['average']
            }
            combined_results.append(combined_doc)

# Print combined results
for doc in combined_results:
    print(doc)
