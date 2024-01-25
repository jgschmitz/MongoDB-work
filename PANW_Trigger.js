const { MongoClient } = require('mongodb');

exports = async function() {
  try {
    const uri = "your_mongodb_atlas_uri";
    const client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });

    await client.connect();

    const sourceCollection = client.db("your_database_name").collection("source_collection");
    const targetCollection = client.db("your_database_name").collection("target_collection");

    const filter = { /* your filter criteria here */ };

    const documentsToMove = await sourceCollection.find(filter).toArray();

    if (documentsToMove.length > 0) {
      await targetCollection.insertMany(documentsToMove);
      console.log(`Inserted ${documentsToMove.length} documents into target collection.`);
    } else {
      console.log('No documents to insert.');
    }

    await client.close();

    console.log('Trigger executed successfully.');
  } catch (error) {
    console.error('Error executing trigger:', error);
  }
};
