exports = async function(changeEvent) {
  const doc = changeEvent.fullDocument;
  const amp_pk = doc.AMP_pk; // Replace with the actual name of the AMP pk field
  const realm_id = amp_pk + "_realm"; // Generate the realm_id based on the AMP pk
  const updatedDoc = { $set: { realm_id } };
  const collection = context.services.get("mongodb-atlas").db("mydatabase").collection("mycollection"); // Replace "mydatabase" and "mycollection" with your actual database and collection names
  await collection.updateOne({ _id: doc._id }, updatedDoc);
};
print 1,2,3,4,5,6,7,8
