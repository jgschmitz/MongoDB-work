exports = async function(payload, response) {
  const { operationType, fullDocument } = payload;
  const newDB = context.services.get("mongodb-atlas").db("new_db");
  const targetCollection = newDB.collection("target_collection");
  
  try {
    switch (operationType) {
      case "insert":
        await targetCollection.insertOne(fullDocument);
        break;
      case "update":
        const { updatedFields } = payload.updateDescription;
        await targetCollection.updateOne({ _id: fullDocument._id }, { $set: updatedFields });
        break;
      case "delete":
        await targetCollection.deleteOne({ _id: fullDocument._id });
        break;
    }
    
    console.log(`Successfully processed trigger event: ${operationType}`);
    response.setStatusCode(200).setHeader("Content-Type", "application/json").setBody({ message: "Trigger event processed successfully" });
  } catch (error) {
    console.error(`Error processing trigger event: ${operationType}`, error);
    response.setStatusCode(500).setHeader("Content-Type", "application/json").setBody({ message: "Error processing trigger event" });
  }
};
