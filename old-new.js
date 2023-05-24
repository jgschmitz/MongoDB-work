exports = async function(payload, response) {
  // Get the changed document from the trigger event
  const changedDocument = payload.fullDocument;
  
  // Connect to the "new_db" in the MongoDB Atlas cluster
  const newDB = context.services.get("mongodb-atlas").db("new_db");
  
  try {
    // Determine the type of operation (INSERT/UPDATE/DELETE)
    const operationType = payload.operationType;
    
    if (operationType === "insert") {
      // Handle INSERT operation
      await newDB.collection("target_collection").insertOne(changedDocument);
    } else if (operationType === "update") {
      // Handle UPDATE operation
      const updatedDocument = payload.updateDescription.updatedFields;
      await newDB.collection("target_collection").updateOne({_id: changedDocument._id}, {$set: updatedDocument});
    } else if (operationType === "delete") {
      // Handle DELETE operation
      await newDB.collection("target_collection").deleteOne({_id: changedDocument._id});
    }
    
    // Log a success message
    console.log(`Successfully processed trigger event: ${operationType}`);
    
    // Set the response status
    response.setStatusCode(200);
    response.setHeader("Content-Type", "application/json");
    response.setBody({message: "Trigger event processed successfully"});
  } catch (error) {
    // Log an error message
    console.error(`Error processing trigger event: ${operationType}`, error);
    
    // Set the response status
    response.setStatusCode(500);
    response.setHeader("Content-Type", "application/json");
    response.setBody({message: "Error processing trigger event"});
  }
};
