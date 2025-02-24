import pymongo
from voyageai import Client  # Import the VoyageAI client

# MongoDB connection - Database renamed to uhg_demo
client = pymongo.MongoClient("mongodb+srv://jschmitz:xxx@xxx.xxxxx.mongodb.net/?retryWrites=true&w=majority")
db = client.uhg_demo  # Changed database name

# Initialize VoyageAI client using your API key
voyage_client = Client(api_key="ADD KEY HERE")

# List of healthcare-related questions a patient might ask
docs = [
    "What are the side effects of my medication?",
    "How often should I schedule a physical exam?",
    "What are the symptoms of high blood pressure?",
    "Can I continue my exercise routine after surgery?",
    "What should I eat if I have high cholesterol?",
    "How do I manage stress to improve my heart health?",
    "When should I get my next flu shot?",
    "Is it safe to take this medication with my current prescriptions?",
    "What are the treatment options for chronic back pain?",
    "How can I improve my sleep habits for better health?"
]

# Generate embeddings using VoyageAI
result_doc = {}
for doc in docs:
    response = voyage_client.embed([doc], model="voyage-lite-02-instruct")  # Get embeddings
    doc_vector = response.embeddings[0]  # Extract the embedding from the response
    result_doc['sentence'] = doc
    result_doc['vectorEmbedding'] = doc_vector
    result = db.vectors_demo_1.insert_one(result_doc.copy())
    print(f"Inserted document ID: {result.inserted_id}")
