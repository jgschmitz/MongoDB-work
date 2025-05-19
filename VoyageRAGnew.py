#this demo assumes paid keys 

import pymongo
from voyageai import Client as VoyageClient
import openai
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize MongoDB connection
client = pymongo.MongoClient("mongodb+srv://<username>:<password>@cluster0.abcd1.mongodb.net/<database>?retryWrites=true&w=majority")
db = client.voyagenew  # Database
collection = db.demo_rag  # Collection for RAG pipeline

# Initialize API clients
voyage_client = VoyageClient(api_key="") #add your key here
openai.api_key = "" #add your key here

# Step 1: Embed and insert healthcare documents into MongoDB with categories
health_docs = [
    {"text": "High blood pressure often presents with symptoms like headaches, dizziness, and blurred vision.", "category": "hypertension"},
    {"text": "A healthy diet for heart disease includes fruits, vegetables, whole grains, and lean protein.", "category": "nutrition"},
    {"text": "Regular exercise helps maintain healthy cholesterol levels and lowers the risk of heart disease.", "category": "exercise"},
    {"text": "Symptoms of diabetes include frequent urination, excessive thirst, and unexplained weight loss.", "category": "diabetes"},
    {"text": "Managing stress through meditation and breathing exercises can improve overall mental health.", "category": "mental_health"}
]

# Insert documents with embeddings
for doc in health_docs:
    response = voyage_client.embed([doc["text"]], model="voyage-lite-02-instruct")
    embedding = response.embeddings[0]

    result = collection.insert_one({
        "text": doc["text"],
        "embedding": embedding,
        "category": doc["category"]
    })
    logging.info(f"Inserted document ID: {result.inserted_id}")

# Step 2: Hybrid Search - Vector + Keyword Filtering
def search_similar_docs(query_embedding, keyword=None, category=None, top_k=3):
    pipeline = [
        {
            "$vectorSearch": {
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": 50,
                "limit": top_k,
                "index": "vector_index"
            }
        }
    ]

    # If filtering by keyword or category, add an extra stage
    if keyword or category:
        match_filter = {}
        if keyword:
            match_filter["text"] = {"$regex": keyword, "$options": "i"}
        if category:
            match_filter["category"] = category
        pipeline.append({"$match": match_filter})

    try:
        return list(collection.aggregate(pipeline))
    except Exception as e:
        logging.error(f"Error during hybrid search: {e}")
        return []

# Step 3: Full RAG response generation function using GPT-4 with summarization
def generate_rag_response(user_query, keyword=None, category=None):
    try:
        # Get the query embedding
        query_response = voyage_client.embed([user_query], model="voyage-lite-02-instruct")
        query_embedding = query_response.embeddings[0]

        # Retrieve top matching documents using Hybrid Search
        retrieved_docs = search_similar_docs(query_embedding, keyword, category)

        if not retrieved_docs:
            return "No relevant information found. Please try rephrasing your question."

        # Extract text and metadata from results
        retrieved_texts = [doc["text"] for doc in retrieved_docs]
        retrieved_summary = "\n".join([f"- {text}" for text in retrieved_texts])

        # Construct enhanced prompt for OpenAI GPT-4
        prompt = f"""
        You are a healthcare assistant providing accurate, well-structured responses.
        The user asked: "{user_query}"

        Relevant information from the database:
        {retrieved_summary}

        Please generate a concise yet informative response.
        """

        # Generate response using OpenAI GPT-4
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful healthcare assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )

        return response.choices[0].message['content'].strip()

    except Exception as e:
        logging.error(f"Error generating RAG response: {e}")
        return "An error occurred while processing your request."

# Step 4: Test the RAG pipeline
user_question = "What are some healthy foods for heart health?"
answer = generate_rag_response(user_question, keyword="heart", category="nutrition")
print(f"Generated Answer:\n{answer}")
