import pymongo
import openai

# === Azure OpenAI Configuration ===
openai.api_type = "azure"
openai.api_base = "https://r1vlfek6j0bpopenai.openai.azure.com/"  # Replace with your actual Azure endpoint
openai.api_version = "2024-04-01-preview"
openai.api_key = "sk-..."  # Replace with your actual Azure OpenAI API key

# === MongoDB Connection ===
mongo = pymongo.MongoClient("mongodb+srv://adminDBUser:yourPassword@darkstar.tnhx6.mongodb.net/?retryWrites=true&w=majority")
db = mongo.vector_tests

# === Sample Documents to Embed ===
docs = [
    "The students studied for their exams.",
    "Studying hard, the students prepared for their exams.",
    "The chef cooked a delicious meal.",
    "The chef cooked the chicken with the vegetables.",
    "Known for its power and aggression, Mike Tyson's boxing style was feared by many."
]

# === Function to Get Azure OpenAI Embedding ===
def get_embedding(text, engine="magnus-va-text-embedding-ada-002"):
    response = openai.Embedding.create(
        input=[text],
        engine=engine
    )
    return response["data"][0]["embedding"]

# === Insert Embeddings into MongoDB ===
for doc in docs:
    doc_vector = get_embedding(doc)
    result_doc = {
        'sentence': doc,
        'vectorEmbedding': doc_vector
    }
    result = db.vectors_demo_1.insert_one(result_doc)
    print(f"Inserted: {result.inserted_id}")
