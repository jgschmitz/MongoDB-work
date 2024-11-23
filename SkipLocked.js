// Import necessary packages
import com.mongodb.client.MongoCursor;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Projections;
import org.bson.conversions.Bson;
import org.bson.Document;
import com.mongodb.client.MongoCollection;

public class MongoDBExample {

    public static void main(String[] args) {
        // Assume `collection` is initialized elsewhere (e.g., via a MongoDB client).
        MongoCollection<Document> collection = getCollection();

        // Construct the query filter to select documents that are not locked.
        Bson filter = Filters.eq("locked", false);

        // Construct the projection to include only the fields we need.
        Bson projection = Projections.fields(Projections.include("field1", "field2"));

        // Use try-with-resources to ensure the cursor is properly closed.
        try (MongoCursor<Document> cursor = collection.find(filter).projection(projection).iterator()) {
            // Iterate over the cursor and process each document as needed.
            while (cursor.hasNext()) {
                Document doc = cursor.next();
                // Process the document (e.g., print it or extract data).
                processDocument(doc);
            }
        }
    }

    private static void processDocument(Document doc) {
        // Add your logic to process the document here
        System.out.println(doc.toJson());
    }

    private static MongoCollection<Document> getCollection() {
        // Replace with your logic to initialize and return the collection.
        // Example: mongoClient.getDatabase("databaseName").getCollection("myCollection");
        return null;
    }
}
