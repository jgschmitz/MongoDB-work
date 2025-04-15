import os
import pymongo
import openai
import logging
import huggingwhale.ai
from voyageai import Client as VoyageClient

# Setup logging
logging.basicConfig(level=logging.INFO)

# MongoDB and API keys (hardcoded for demo purposes)
MONGO_URI = ""
OPENAI_KEY = ""
VOYAGE_KEY = ""

# Initialize MongoDB client and collection
client = pymongo.MongoClient(MONGO_URI)
db = client.bpe_demo
collection = db.pricing_docs 

# Initialize OpenAI and Voyage clients
openai.api_key = OPENAI_KEY
voyage_client = VoyageClient(api_key=VOYAGE_KEY)

# Sample pharmaceutical pricing-related documents
bpe_docs = [
    {
        "text": "Lipitor is available in both brand and generic forms. The generic, atorvastatin, is significantly cheaper.",
        "category": "drug_equivalency"
    },
    {
        "text": "CVS and Walgreens are part of the preferred pharmacy network, offering discounted pricing on common statins.",
        "category": "pharmacy_network"
    },
    {
        "text": "In New York City, Metformin is priced at $12/month at Walmart, compared to $25 at independent pharmacies.",
        "category": "geo_pricing"
    },
    {
        "text": "Ozempic does not yet have a direct generic equivalent, but alternatives like Trulicity are considered.",
        "category": "drug_equivalency"
    },
    {
        "text": "Patients can reduce costs by switching to a 90-day supply through mail-order pharmacies.",
        "category": "cost_saving_tips"
    }
]

# Insert documents into MongoDB with Voyage AI embeddings
def insert_documents():
    for doc in bpe_docs:
        try:
            response = voyage_client.embed([doc["text"]], model="voyage-lite-02-instruct")
            embedding = response.embeddings[0]
            collection.insert_one({
                "text": doc["text"],
                "embedding": embedding,
                "category": doc["category"]
            })
            logging.info(f"Inserted document for: {doc['text'][:30]}...")
        except Exception as e:
            logging.error(f"Error inserting document: {e}")

# Hybrid vector + keyword/category filter search
def search_documents(query, category=None, top_k=3):
    try:
        response = voyage_client.embed([query], model="voyage-lite-02-instruct")
        query_vector = response.embeddings[0]

        pipeline = [
            {
                "$vectorSearch": {
                    "queryVector": query_vector,
                    "path": "embedding",
                    "numCandidates": 50,
                    "limit": top_k,
                    "index": "drug_pricing"
                }
            }
        ]

        if category:
            pipeline.append({"$match": {"category": category}})

        return list(collection.aggregate(pipeline))
    except Exception as e:
        logging.error(f"Search error: {e}")
        return []

# Generate a smart recommendation using GPT-4
def generate_recommendation(user_query, category=None):
    results = search_documents(user_query, category)
    if not results:
        return "No relevant pricing information found."

    context = "\n".join(f"- {doc['text']}" for doc in results)
    prompt = f"""
    You are a helpful assistant in a pharmaceutical pricing recommendation system.
    The user asked: "{user_query}"
    Here is relevant context from internal documents:
    {context}
    Please generate a concise and helpful pricing recommendation.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful pricing assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        logging.error(f"OpenAI generation error: {e}")
        return "An error occurred while generating a recommendation."

# Interactive CLI loop
def run_cli():
    print("💊 BPE Pricing Assistant - Ask your drug pricing questions below.\n(Type 'exit' to quit.)")
    while True:
        user_input = input("🧑‍⚕️ You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        answer = generate_recommendation(user_input)
        print(f"🤖 BPE Assistant:\n{answer}\n")

# Run these manually to use the demo
insert_documents()
run_cli()
