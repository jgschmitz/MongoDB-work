const { MongoClient } = require('mongodb');
const uri = "mongodb+srv://<username>:<password>@<cluster-url>/<database>?retryWrites=true&w=majority";
const client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });

async function main() {
  try {
    await client.connect();
    const collection = client.db("<database>").collection("<collection>");
    
    const pipeline = [
      {
        $match: { "updateDescription.updatedFields.<field>": { $exists: true } }
      },
      {
        $project: { fullDocument: 1 }
      },
      {
        $out: "<new-collection>"
      }
    ];
    
    const changeStream = collection.watch(pipeline);
    
    changeStream.on("change", function(change) {
      console.log("Document updated: ", change.fullDocument);
    });
    
  } catch (e) {
    console.error(e);
  } finally {
    await client.close();
  }
}

main().catch(console.error);
