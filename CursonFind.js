// Define batch size and processing limit
const batchSize = 10;
const processingLimit = 20;

// Initialize the cursor
let cursor = db.collection.find({}).batchSize(batchSize);

// Define an array to store documents
const docs = [];

// Process the cursor in batches
while (cursor.hasNext()) {
  docs.push(cursor.next());

  // Stop processing when the limit is reached
  if (docs.length === processingLimit) {
    // Resume cursor from this point later, if needed
    var cursorId = cursor.id;
    break;
  }
}

// Check if further processing is needed
if (cursor.hasNext()) {
  cursor = db.collection.find({}).batchSize(batchSize).resumable({ id: cursorId });

  while (cursor.hasNext()) {
    docs.push(cursor.next());
  }
}

// Output the collected documents (optional)
printjson(docs);
