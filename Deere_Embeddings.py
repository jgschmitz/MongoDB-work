# intial demo for deere 🚜
import pymongo
import openai

# Set up OpenAI key
openai.api_key = "OPENAI API KEY"

# Connect to MongoDB
client = pymongo.MongoClient('MONGODB CONNECTION STRING')
db = client['YOUR_DATABASE_NAME']  # replace with your database name
collection = db['YOUR_COLLECTION_NAME']  # replace with your collection name

# Retrieve documents from the collection
documents = collection.find()

# Iterate over the documents
index = 0
for document in documents:
    # Initialize the embedding input string
    embedding_input_string = ""
    
    # Check if 'Information' field exists and append its sub-fields to the embedding string
    if 'Information' in document:
        info = document['Information']
        
        # Concatenate each sub-field in 'Information' if it exists
        if 'project' in info and info['project'] is not None:
            embedding_input_string += info['project'] + ". "
        if 'domain' in info and info['domain'] is not None:
            embedding_input_string += info['domain'] + ". "
        if 'system' in info and info['system'] is not None:
            embedding_input_string += info['system'] + ". "
    
    # Print the current input string used to generate the embedding
    print(f"Embedding input string for document {document['_id']}: {embedding_input_string}")

    # Generate OpenAI embedding based on the input string
    embedding = openai.Embedding.create(input=[embedding_input_string], model="text-embedding-ada-002")['data'][0]['embedding']
    
    # Set the OpenAI embedding into each document in the database
    document['openai_embedding'] = embedding

    # Update the document in the collection
    collection.update_one({'_id': document['_id']}, {'$set': {'openai_embedding': embedding}})
    
    # Keep track of the progress
    print(f"Current index: {index}")
    index += 1

# Close the MongoDB connection
client.close()
