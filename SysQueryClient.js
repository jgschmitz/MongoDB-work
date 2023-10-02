const { MongoClient } = require('mongodb');

// Connection URL and database name
const url = 'mongodb://<your-mongodb-uri>';
const dbName = 'yourDatabaseName'; // Replace with your database name

// Create a new MongoClient
const client = new MongoClient(url, { useNewUrlParser: true });

// Use async/await to run the query
async function runQuery() {
  try {
    // Connect to the server
    await client.connect();

    // Get a reference to the database
    const db = client.db(dbName);

    // Define the time frame for the query
    const start = new Date();
    start.setHours(start.getHours() - 2); // 2 hours ago
    const end = new Date();

    // Perform the query
    const result = await db.collection('system.profile').countDocuments({
      ts: { $gte: start, $lte: end },
      op: 'query',
      ns: 'database_name.Collection_name',
      planSummary: 'COLLSCAN',
    });

    console.log(`Total matching documents: ${result}`);
  } finally {
    // Close the client connection
    await client.close();
  }
}

// Run the query
runQuery().catch(console.error);
