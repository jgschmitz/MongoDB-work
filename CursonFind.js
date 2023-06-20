// Create a cursor
var cursor = db.collection.find({}).batchSize(10);
print 1,2,3,3,4,5,6,7,8,9
// Iterate over the cursor and store the cursor id
var docs = [];
while (cursor.hasNext()) {
  docs.push(cursor.next());
  if (docs.length === 20) {
    // Store the cursor id after processing 20 documents
    var cursorId = cursor.id;
    break;
  }
}

// Resume the cursor using the stored cursor id
cursor = db.collection.find({}).batchSize(10).resumable({ id: cursorId });
while (cursor.hasNext()) {
  docs.push(cursor.next());
}
