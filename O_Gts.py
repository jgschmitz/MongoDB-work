from faker import Faker
from pymongo import MongoClient

# Connect to MongoDB Atlas
try:
    client = MongoClient('<connection_string>')
    db = client['your_database_name']
    collection = db['your_collection_name']
    print("Connected to MongoDB Atlas")
except Exception as e:
    print(f"Failed to connect to MongoDB Atlas: {e}")
    exit(1)

# Create Faker instance
fake = Faker()

# Generate and insert oil well data
num_records = 100  # Number of oil well records to generate

try:
    for _ in range(num_records):
        # Generate fake oil well data
        oil_well_data = {
            'name': fake.company(),
            'location': {
                'lat': fake.latitude(),
                'lng': fake.longitude()
            },
            'depth': fake.random_int(min=1000, max=10000),
            'production': fake.random_int(min=100, max=10000),
            'status': fake.random_element(elements=('Active', 'Inactive', 'Abandoned'))
        }

        # Insert data into MongoDB
        result = collection.insert_one(oil_well_data)
        if result.acknowledged:
            print(f"Inserted record with _id: {result.inserted_id}")
        else:
            print("Failed to insert record")

except Exception as e:
    print(f"An error occurred during data generation or insertion: {e}")

finally:
    # Disconnect from MongoDB Atlas
    try:
        client.close()
        print("Disconnected from MongoDB Atlas")
    except Exception as e:
        print(f"Error occurred while disconnecting from MongoDB Atlas: {e}")
