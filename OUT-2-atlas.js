const { MongoClient } = require('mongodb');

// Load environment variables for security best practices
require('dotenv').config();

// MongoDB Atlas connection details from environment variables
const uri = process.env.MONGODB_URI; // Store your URI in .env file

const client = new MongoClient(uri);

(async () => {
  try {
    await client.connect();
    
    const db = client.db(process.env.DB_NAME); // Database name from .env
    const collection = db.collection(process.env.COLLECTION_NAME); // Collection name from .env
    
    // Simulated transformed data
    const transformedData = [
      { field1: 'value1', field2: 'value2' },
      // ... more transformed data
    ];
    
    // Aggregation pipeline with $project and $out stages
    const aggregationPipeline = [
      { $project: { _id: 0, field1: 1, field2: 1 } }, // Adjust projection as needed
      { $out: process.env.TARGET_COLLECTION } // Target collection name from .env
    ];

    // Execute the aggregation pipeline
    await collection.aggregate(aggregationPipeline).toArray();
    console.log('Data successfully loaded into MongoDB Atlas');
  } catch (error) {
    console.error('Error loading data:', error);
  } finally {
    await client.close();
  }
})();
