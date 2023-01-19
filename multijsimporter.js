const MongoClient = require('mongodb').MongoClient;
const fs = require('fs');

// Connection URL
const url = 'mongodb://localhost:27017';

// Database Name
const dbName = 'mydatabase';

// Create a new MongoClient
const client = new MongoClient(url);

// Use connect method to connect to the Server
client.connect(function(err) {
  if (err) {
    console.log(err);
    return;
  }
  console.log("Connected successfully to server");

  const db = client.db(dbName);

  // Read data from file
  fs.readFile('data.json', 'utf8', function(err, data) {
    if (err) {
      console.log(err);
      return;
    }
    const jsonData = JSON.parse(data);
    
    // Insert data into MongoDB
    db.collection('mycollection').insertMany(jsonData, function(err, result) {
      if (err) {
        console.log(err);
        return;
      }
      console.log(`Inserted ${result.insertedCount} documents into the collection`);
      client.close();
    });
  });
});



