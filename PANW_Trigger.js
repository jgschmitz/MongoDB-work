exports = async function() {
  try {
    const orders = context.services.get("mongodb-atlas").db("your_database_name").collection("source_collection");
    const reports = context.services.get("mongodb-atlas").db("your_database_name").collection("target_collection");

    const filter = { /* your filter criteria here */ };

    const documentsToMove = await orders.find(filter).toArray();

    if (documentsToMove.length > 0) {
      await reports.insertMany(documentsToMove);
      console.log(`Inserted ${documentsToMove.length} documents into target collection.`);
    } else {
      console.log('No documents to insert.');
    }

    console.log('Trigger executed successfully.');
  } catch (error) {
    console.error('Error executing trigger:', error);
  }
};

