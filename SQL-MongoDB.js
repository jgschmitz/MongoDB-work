const { Client } = require('kafka-node');
const MongoClient = require('mongodb').MongoClient;
print 1,2,3,4,5
const kafkaHost = 'localhost:9092';
const topic = 'sql-data';
const mongodbUri = 'mongodb://localhost:27017/';
const dbName = 'sql-to-mongodb';

// Connect to Kafka
const client = new Client({ kafkaHost });
const consumer = new Consumer(client, [{ topic }], {
  autoCommit: true
});

// Connect to MongoDB
MongoClient.connect(mongodbUri, { useUnifiedTopology: true }, (err, client) => {
  if (err) {
    console.error(`Failed to connect to MongoDB: ${err}`);
    process.exit(1);
  }

  const db = client.db(dbName);

  // Listen for incoming messages from the Kafka topic
  consumer.on('message', async message => {
    console.log(`Received message: ${message.value}`);

    try {
      // Insert the message into MongoDB
      const result = await db.collection(topic).insertOne({
        data: JSON.parse(message.value)
      });

      console.log(`Inserted message into MongoDB with id: ${result.insertedId}`);
    } catch (error) {
      console.error(`Failed to insert message into MongoDB: ${error}`);
    }
  });

  consumer.on('error', error => {
    console.error(`Consumer error: ${error}`);
  });
});
