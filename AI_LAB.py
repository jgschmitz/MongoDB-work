import torch
import clip
from PIL import Image
import os
import json
from pymongo import MongoClient

# Path to settings.json
settings_file_path = '/root/vector_search_lab/lab_files/labs/settings.json'

# Load settings from JSON
with open(settings_file_path, 'r') as file:
    settings = json.load(file)

# Connect to MongoDB Atlas using the correct connection string key
client = MongoClient(settings['mongoURI'])

# Select the database and collection
db = client['lab_db']
my_vectors = db['my_vectors']

# Check if a GPU is available for processing vectors, if not fall back to using the CPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load the clip model
model, preprocess = clip.load("ViT-B/32", device=device)

# Corrected path to the directory containing images
img_dir = "/root/vector_search_lab/lab_files/images"

# List to hold image data records
records = []

# Generate vector for each image and append result to records
for filename in os.listdir(img_dir):
    f = os.path.join(img_dir, filename)
    if os.path.isfile(f):
        image = preprocess(Image.open(f)).unsqueeze(0).to(device)
        image_features = model.encode_image(image)
        vectors = image_features.detach().cpu().numpy()

        # Final image data
        image_data = {
            "name": filename,
            "img_vector": vectors[0].tolist()
        }

        records.append(image_data)

print("Processed " + str(len(records)) + " images.")

# Insert the data into the collection
result = my_vectors.insert_many(records)

# Print the ids of the new inserted documents
print('Inserted IDs:', result.inserted_ids)

# Close the connection
client.close()

print("Data successfully loaded into MongoDB.")
