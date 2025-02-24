import pymongo
from voyageai import Client as VoyageClient
import openai

# Initialize MongoDB connection
client = pymongo.MongoClient("mongodb+srv://jschmitz:xxxx@darkstar.tnhx6.mongodb.net/?retryWrites=true&w=majority")
db = client.uhg_demo  # Using the previously created database
collection = db.vectors_demo_rag  # New collection for RAG pipeline

# Initialize API clients
voyage_client = VoyageClient(api_key="your_voyage_api_key")
openai.api_key = "your_openai_api_key"

# Step 1: Embed and insert healthcare documents into MongoDB
health_docs = [
    "High blood pressure often presents with symptoms like headaches, dizziness, and blurred vision.",
    "A healthy diet for heart disease includes fruits, vegetables, whole grains, and lean protein.",
    "Regular exercise helps maintain healthy cholesterol levels and lowers the risk of heart disease.",
    "Symptoms of diabetes include frequent urination, excessive thirst, and unexplained weight loss.",
    "Managing stress through meditation and breathing exercises can improve overall mental health."
]

# Insert documents with embeddings
for doc in health_docs:
    response = voyage_client.embed([doc], model="voyage-lite-02-instruct")
    embedding = response.embeddings[0]
    result = collection.insert_one({
        "text": doc,
        "embedding": embedding
    })
    print(f"Inserted document ID: {result.inserted_id}")

# Step 2: Function for performing vector search in MongoDB
def search_similar_docs(query_embedding, top_k=3):
    pipeline = [
        {
            "$vectorSearch": {
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": 10,
                "limit": top_k,
                "index": "default"  # Make sure your MongoDB collection has a vector index
            }
        }
    ]
    return list(collection.aggregate(pipeline))

# Step 3: Full RAG response generation function using GPT-4
def generate_rag_response(user_query):
    # Get the query embedding
    query_response = voyage_client.embed([user_query], model="voyage-lite-02-instruct")
    query_embedding = query_response.embeddings[0]

    # Retrieve top matching documents from MongoDB
    retrieved_docs = search_similar_docs(query_embedding)

    # Prepare context for the LLM
    retrieved_texts = "\n\n".join([doc["text"] for doc in retrieved_docs])
    prompt = f"Using the following healthcare information, answer the patient's question:\n\n{retrieved_texts}\n\nQuestion: {user_query}"

    # Generate response using OpenAI GPT-4
    response = openai.ChatCompletion.create(
        model="gpt-4",  # You can switch to "gpt-3.5-turbo" for a cheaper alternative
        messages=[
            {"role": "system", "content": "You are a helpful healthcare assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response.choices[0].message['content'].strip()

# Step 4: Test the RAG pipeline
user_question = "What are common symptoms of diabetes?"
answer = generate_rag_response(user_question)
print(f"Generated Answer:\n{answer}")
