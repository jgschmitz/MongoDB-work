#break up your dataset for easier training in 🤗 100 rows at a time
from datasets import load_dataset

# Load the dataset from Hugging Face
dataset = load_dataset('your dataset here')

# Total number of rows
total_rows = len(dataset['train'])

# Define chunk size (e.g., 100,000 rows at a time)
chunk_size = 100000

# Split the dataset into smaller chunks and process them
for i in range(0, total_rows, chunk_size):
    # Select a chunk of data
    chunk = dataset['train'].select(range(i, min(i + chunk_size, total_rows)))

    print(f"Processing chunk {i // chunk_size + 1}")

    # Process 'source' column in the chunk
    chunk = chunk.class_encode_column('source')

    # Optionally push each chunk to Hugging Face, or save it locally
    chunk.push_to_hub(f"Schmitz005/kaggle-recipe-categorized-chunk-{i // chunk_size + 1}")
