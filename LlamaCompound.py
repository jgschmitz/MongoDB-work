from pymongo import MongoClient
import numpy as np
from llamaindex import LlamaIndex

# Connect to MongoDB
client = MongoClient("mongodb://Atlas Connection string goes here")
db = client["your_database"]
collection = db["your_collection"]

# Fetch documents and extract vector fields
documents = collection.find()

# Function to create a compound vector from two vector fields
def create_compound_vector(doc):
    vector1 = np.array(doc.get("field1_vector", []))
    vector2 = np.array(doc.get("field2_vector", []))
    compound_vector = np.concatenate((vector1, vector2))
    return compound_vector

# Create a list of compound vectors and their corresponding document IDs
vectors = []
document_ids = []
for doc in documents:
    # Ensure both fields are present and have valid vectors
    if "field1_vector" in doc and "field2_vector" in doc:
        compound_vector = create_compound_vector(doc)
        vectors.append(compound_vector)
        document_ids.append(doc["_id"])

# Initialize LlamaIndex and create the index
llama_index = LlamaIndex()
llama_index.add_vectors(vectors, document_ids)

# Save the index
llama_index.save("compound_vector_index")

print("Compound vector index created and saved.")
