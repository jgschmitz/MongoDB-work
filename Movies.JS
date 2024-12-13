#shorted version 2.o

const { MongoClient } = require('mongodb');

const uri = 'mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority';

(async () => {
  const client = new MongoClient(uri);
  await client.connect();
  const db = client.db('sample_mflix');
  const movies = await db.collection('movies').find().toArray();
  console.log(movies);
  await client.close();
})();
