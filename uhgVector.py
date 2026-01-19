import os
import pymongo
import openai
import warnings

# Suppress all warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

# Set your OpenAI API key (preferably load this securely)
openai.api_key = os.getenv("OPENAI_API_KEY")

# MongoDB connection
client = pymongo.MongoClient("")
db = client.vector_tests

# Medical-related example questions
docs = [
    "What are the side effects of atorvastatin?",
    "How is Type 2 Diabetes typically managed?",
    "What are the symptoms of iron deficiency anemia?",
    "Can I take ibuprofen while pregnant?",
    "What does a high LDL cholesterol level indicate?"
]

# Print sentences
print(docs)

# Use OpenAI to embed each document
for doc in docs:
    response = openai.Embedding.create(
        input=doc,
        model="text-embedding-3-small"  # or 'text-embedding-3-large' for higher quality
    )
    doc_vector = response['data'][0]['embedding']
    
    result_doc = {
        'question': doc,
        'vectorEmbedding': doc_vector
    }
    result = db.vectors_demo_1.insert_one(result_doc)
    print(f"Inserted: {doc} -> ID: {result.inserted_id}")
