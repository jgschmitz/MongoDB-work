import requests
import pymongo
from sentence_transformers import SentenceTransformer
import json

# Step 1: Initialize MongoDB Atlas Connection
MONGO_URI = "your_mongodb_atlas_connection_string"
client = pymongo.MongoClient(MONGO_URI)
db = client["rag_db"]
collection = db["vector_store"]

# Step 2: Load Embedding Model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Step 3: Insert Documents with Embeddings into MongoDB Atlas
sample_documents = [
    {"text": "MongoDB is a NoSQL database.", "metadata": {"topic": "database"}},
    {"text": "DeepSeek is an LLM model optimized for retrieval-augmented generation.", "metadata": {"topic": "AI"}},
    {"text": "Hybrid search combines text and vector search for better accuracy.", "metadata": {"topic": "search"}}
]

for doc in sample_documents:
    doc["embedding"] = embedding_model.encode(doc["text"]).tolist()
    collection.insert_one(doc)

print("Inserted sample documents with embeddings.")

# Step 4: Querying MongoDB Atlas Vector Store with Hybrid Search
def search_mongodb(query):
    query_embedding = embedding_model.encode(query).tolist()
    
    pipeline = [
        {"$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": query_embedding,
            "numCandidates": 5,
            "limit": 3
        }}
    ]
    
    results = collection.aggregate(pipeline)
    return [doc["text"] for doc in results]

# Step 5: Retrieve Context and Construct LLM Prompt
query = "How does hybrid search work?"
retrieved_docs = search_mongodb(query)

prompt = f"""
Given the following retrieved context:
{json.dumps(retrieved_docs, indent=2)}
Answer the following question:
{query}
"""

# Step 6: Call DeepSeek API
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Replace with real endpoint
DEEPSEEK_API_KEY = "your_deepseek_api_key"

headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",  # Check the correct model name in DeepSeek docs
    "messages": [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": prompt}
    ]
}

response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)

print("DeepSeek Response:", response.json())
