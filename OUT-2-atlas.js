const { MongoClient } = require('mongodb');

const uri = 'mongodb+srv://<username>:<password>@<cluster-url>/test?retryWrites=true&w=majority';
const client = new MongoClient(uri);

(async () => {
  try {
    await client.connect();
    
    const db = client.db('mydatabase');
    const collection = db.collection('mycollection');
    
    // Load data from S3 and transform if necessary
    const transformedData = [
      { field1: 'value1', field2: 'value2' },
      // ... more transformed data
    ];
    
    // Use the $out operator to write data to the target collection
    const aggregationPipeline = [
      { $project: { _id: 0, field1: 1, field2: 1 } }, // Projection as needed
      { $out: 'mycollection' } // Replace 'mycollection' with your target collection name
    ];
    
    await collection.aggregate(aggregationPipeline).toArray();
    console.log('Data loaded into MongoDB Atlas');
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await client.close();
  }
})();
Replace <username>, <password>, <cluster-url>, 'mydatabase', and 'mycollection' with your actual MongoDB Atlas credentials and collection details.

Keep in mind that this example is a basic guide and doesn't cover all aspects of a production scenario, such as error handling, logging, and handling larger datasets. Additionally, consider security best practices for handling credentials when connecting to both S3 and MongoDB Atlas.





