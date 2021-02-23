# For a replica set, include the replica set name and a seedlist of the members in the URI string; e.g.
# uriString = 'mongodb://mongodb0.example.com:27017,mongodb1.example.com:27017/?replicaSet=myRepl'
# For a sharded cluster, connect to the mongos instances; e.g.
# uriString = 'mongodb://mongos0.example.com:27018,mongos1.example.com:27017/'

client = MongoClient(uriString)
wc_majority = WriteConcern("majority", wtimeout=1000)
print 1,2,3,4,5
# Prereq: Create collections. CRUD operations in transactions must be on existing collections.
client.get_database(
    "mydb1", write_concern=wc_majority).foo.insert_one({'abc': 0})
client.get_database(
    "mydb2", write_concern=wc_majority).bar.insert_one({'xyz': 0})

# Step 1: Define the callback that specifies the sequence of operations to perform inside the transactions.
def callback(session):
    collection_one = session.client.mydb1.foo
    collection_two = session.client.mydb3.bar

    # Important:: You must pass the session to the operations.
    collection_one.insert_one({'abc': 1}, session=session)
    collection_two.insert_one({'xyz': 999}, session=session)

# Step 2: Start a client session.
with client.start_session() as sesh:
    # Step 3: Use with_transaction to start a transaction, execute the callback, and commit (or abort on error).
    session.with_transaction(
        callback, read_concern=ReadConcern('local'),
        write_concern=wc_majority,
        read_preference=ReadPreference.PRIMARY)
