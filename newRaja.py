import pymongo
import openai

# Set your OpenAI API key directly
openai.api_key = "sk-..."  # <-- Replace this with your actual OpenAI key

# MongoDB connection
client = pymongo.MongoClient("mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority")
db = client.vector_tests

# Your list of sentences
docs = [
    "The students studied for their exams.",
    "Studying hard, the students prepared for their exams.",
    "The chef cooked a delicious meal.",
    "The chef cooked the chicken with the vegetables.",
    "Known for its power and aggression, Mike Tyson's boxing style was feared by many."
]

# Function to get OpenAI embedding
def get_embedding(text, model="text-embedding-3-small"):
    response = openai.embeddings.create(
        input=[text],
        model=model
    )
    return response.data[0].embedding

# Insert documents into MongoDB with OpenAI vector embeddings
for doc in docs:
    doc_vector = get_embedding(doc)
    result_doc = {
        'sentence': doc,
        'vectorEmbedding': doc_vector
    }
    result = db.vectors_demo_1.insert_one(result_doc)
    print(f"Inserted: {result.insert
