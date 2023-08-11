const AWS = require('aws-sdk');
const MongoClient = require('mongodb').MongoClient;

AWS.config.update({
  accessKeyId: 'YOUR_ACCESS_KEY_ID',
  secretAccessKey: 'YOUR_SECRET_ACCESS_KEY'
});

const s3 = new AWS.S3();
const mongoURI = 'mongodb+srv://<username>:<password>@cluster.mongodb.net/test';
const dbName = 'your_database_name';
const collectionName = 'your_collection_name';

async function fetchDataFromS3() {
  const params = {
    Bucket: 'YOUR_BUCKET_NAME',
    Key: 'path/to/your/file.txt'
  };

  try {
    const s3Data = await s3.getObject(params).promise();
    const dataAsString = s3Data.Body.toString('utf-8');
    return JSON.parse(dataAsString); // Assuming data is in JSON format
  } catch (error) {
    console.error('Error fetching data from S3:', error);
    throw error;
  }
}

async function insertDataIntoMongoDB(data) {
  const client = new MongoClient(mongoURI, { useNewUrlParser: true, useUnifiedTopology: true });

  try {
    await client.connect();
    const db = client.db(dbName);
    const collection = db.collection(collectionName);

    const bulkOps = data.map(item => ({
      insertOne: {
        document: item
      }
    }));

    await collection.bulkWrite(bulkOps);
    console.log('Data inserted successfully into MongoDB');
  } catch (error) {
    console.error('Error inserting data into MongoDB:', error);
  } finally {
    client.close();
  }
}

async function main() {
  try {
    const fetchedData = await fetchDataFromS3();
    await insertDataIntoMongoDB(fetchedData);
  } catch (error) {
    console.error('An error occurred:', error);
  }
}

main();
