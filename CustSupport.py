import pymongo
from voyageai import Client as VoyageClient
import openai
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize MongoDB connection
client = pymongo.MongoClient("")
db = client.uhg_demo  # Database
collection = db.vectors_demo_rag  # Collection for lead qualification & customer support

# Initialize AI clients
voyage_client = VoyageClient(api_key="")
openai.api_key = ""

# Step 1: Preload Data - Embedding Lead Qualification & FAQ Documents
documents = [
    {"text": "Our enterprise solution offers secure data storage with built-in compliance for healthcare and finance.", "category": "lead_qualification"},
    {"text": "We offer a free 14-day trial with full access to all features, no credit card required.", "category": "lead_qualification"},
    {"text": "To reset your password, go to the settings page and click 'Forgot Password'.", "category": "customer_support"},
    {"text": "Our cloud platform ensures 99.99% uptime and automatic backups for all enterprise customers.", "category": "customer_support"},
    {"text": "MongoDB Atlas supports multi-cloud clusters across AWS, Azure, and Google Cloud.", "category": "technical_info"}
]

# Insert documents with embeddings
for doc in documents:
    response = voyage_client.embed([doc["text"]], model="voyage-lite-02-instruct")
    embedding = response.embeddings[0]
    
    result = collection.insert_one({
        "text": doc["text"],
        "embedding": embedding,
        "category": doc["category"]
    })
    logging.info(f"Inserted document ID: {result.inserted_id}")

# Step 2: Hybrid Search (Vector + Metadata Filtering + Keyword)
def search_similar_docs(query_embedding, keyword=None, category=None, top_k=3):
    pipeline = [
        {
            "$vectorSearch": {
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": 50,
                "limit": top_k,
                "index": "default"
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

# Step 3: Intelligent Assistant for Lead Qualification & Customer Support
def generate_assistant_response(user_query, category=None, user_profile=None):
    try:
        # Embed the query
        query_response = voyage_client.embed([user_query], model="voyage-lite-02-instruct")
        query_embedding = query_response.embeddings[0]

        # Retrieve relevant documents
        retrieved_docs = search_similar_docs(query_embedding, category=category)

        # If no vector match, fall back to keyword search
        if not retrieved_docs:
            logging.info("No vector match found. Trying keyword search...")
            retrieved_docs = search_similar_docs(query_embedding, keyword=user_query, category=category)

        # If still no results, return a default response
        if not retrieved_docs:
            return "I'm sorry, I couldn't find relevant information. Would you like to speak with a representative?"

        # Extract retrieved texts
        retrieved_texts = [doc["text"] for doc in retrieved_docs]
        retrieved_summary = "\n".join([f"- {text}" for text in retrieved_texts])

        # Build prompt with context awareness
        prompt = f"""
        You are an intelligent assistant specialized in {category if category else 'business solutions'}.
        The user ({user_profile if user_profile else 'guest'}) asked: "{user_query}"

        Relevant knowledge:
        {retrieved_summary}

        Generate a professional, helpful, and concise response.
        """

        # Generate a response using OpenAI GPT-4
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a smart assistant for business inquiries and support."},
                      {"role": "user", "content": prompt}],
            max_tokens=200
        )

        return response.choices[0].message['content'].strip()

    except Exception as e:
        logging.error(f"Error generating assistant response: {e}")
        return "An error occurred while processing your request."

# Step 4: Test Scenarios
lead_qualification_question = "Do you offer a free trial?"
customer_support_question = "How do I reset my password?"

lead_answer = generate_assistant_response(lead_qualification_question, category="lead_qualification", user_profile="Prospective Customer")
support_answer = generate_assistant_response(customer_support_question, category="customer_support", user_profile="Existing Customer")

print(f"Lead Qualification Response:\n{lead_answer}\n")
print(f"Customer Support Response:\n{support_answer}\n")
