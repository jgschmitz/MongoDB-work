import pymongo
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic as vertex_ai

# Set up MongoDB connection
client = pymongo.MongoClient('MONGODB CONNECTION STRING')
db = client['sample_airbnb']
collection = db['listingsAndReviews']

# Set up Vertex AI
PROJECT_ID = 'your-project-id'
REGION = 'us-central1'  # Change to your preferred region
EMBEDDING_MODEL_NAME = 'your-model-name'

aiplatform.init(project=PROJECT_ID, location=REGION)
embedding_client = vertex_ai.PredictionServiceClient()

# Function to generate embeddings
def generate_embeddings(input_string):
    endpoint = f'projects/{PROJECT_ID}/locations/{REGION}/endpoints/{EMBEDDING_MODEL_NAME}'
    instance = vertex_ai.ExamplePayload(text_snippet={'content': input_string})
    response = embedding_client.predict(endpoint=endpoint, instances=[instance])
    embedding = response.predictions[0]['embedding']
    return embedding

# Retrieve documents from the collection
documents = collection.find()

# Iterate over the documents
index = 0
for document in documents:
    embedding_input_string = ""
    if document.get('name'):
        embedding_input_string += document["name"] + ". "
    if document.get('summary'):
        embedding_input_string += document['summary'] + ". "
    if document.get('space'):
        embedding_input_string += document['space'] + ". "
    if document.get('description'):
        embedding_input_string += document['description'] + ". "
    if document.get('transit'):
        embedding_input_string += document['transit'] + ". "
    if document.get('price'):
        embedding_input_string += f"Price per night: {document['price']}. "

    print(embedding_input_string)

    # Generate embedding
    embedding = generate_embeddings(embedding_input_string)

    # Set the corresponding embedding into each document in the database
    document['vertex_ai_embedding'] = embedding

    print(f"Current index: {index}")
    index += 1

    # Update the document in the collection
    collection.update_one({'_id': document['_id']}, {'$set': document})

# Close the MongoDB connection
client.close()
