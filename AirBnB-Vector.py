import pymongo
import openai

#Set up openai key
openai.api_key = "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"

# Connect to MongoDB
client = pymongo.MongoClient('mongodb+srv://jschmitz:slb2021@darkstar.tnhx6.mongodb.net/?retryWrites=true&w=majority')
db = client['sample_airbnb']
collection = db['listingsAndReviews']

# Retrieve documents from the collection
documents = collection.find()

# Iterate over the documents
index = 0
for document in documents:
    # print(document)

    #append various data fields in the database entry, assuming they are not null, to the input string used to generate the embedding
    embedding_input_string = ""
    if document['name']!=None:
        embedding_input_string+=document["name"]+". "
    if document['summary']!=None:
        embedding_input_string+=document['summary']+". "
    if document['space']!=None:
        embedding_input_string+=document['space']+". "
    if document['description']!=None:
        embedding_input_string+=document['description']+". "
    if document['transit']!=None:
        embedding_input_string+=document['transit']+". "
    if document['price']!=None:
        embedding_input_string+="Price per night: "+str(document['price'])+'. '
    
    #print the current input string used to generate the embedding
    print(embedding_input_string)

    #generate openai embedding based on input string
    embedding = openai.Embedding.create(input = [embedding_input_string], model="text-embedding-ada-002")['data'][0]['embedding']

    #Set corresponding openai_embedding into each document in the database
    document['openai_embedding'] = embedding

    #keep track of index to display progress in terminal
    print("Current index: {}".format(index)) #to keep track of progress
    index+=1


    # Update the document in the collection
    collection.update_one({'_id': document['_id']}, {'$set': document})

# Close the MongoDB connection
client.close()
