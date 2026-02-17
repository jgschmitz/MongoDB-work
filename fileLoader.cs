using MongoDB.Driver;
using MongoDB.Bson;
using MongoDB.Bson.IO;
using System.Globalization;

const string connectionUri =
  "mongodb+srv://<db_username>:<db_password>@darkstar.tnhx6.mongodb.net/?appName=DarkStar";

var settings = MongoClientSettings.FromConnectionString(connectionUri);
settings.ServerApi = new ServerApi(ServerApiVersion.V1);

var client = new MongoClient(settings);

try
{
    var result = client.GetDatabase("admin")
        .RunCommand<BsonDocument>(new BsonDocument("ping", 1));
    Console.WriteLine("Pinged your deployment. You successfully connected to MongoDB!");
}
catch (Exception ex)
{
    Console.WriteLine(ex);
    return;
}

// ---- CONFIG ----
string dbName = "DarkStarDb";
string collectionName = "flatfile_import";
string filePath = args.Length > 0 ? args[0] : @"C:\data\input.csv";  // or .jsonl
int batchSize = 1000;

// Optional: choose how to handle duplicates if your docs have an "_id"
bool continueOnDuplicateKey = true;

// ---- LOAD ----
var db = client.GetDatabase(dbName);
var collection = db.GetCollection<BsonDocument>(collectionName);

Console.WriteLine($"Importing: {filePath}");
Console.WriteLine($"Target: {dbName}.{collectionName}");

if (filePath.EndsWith(".csv", StringComparison.OrdinalIgnoreCase))
{
    await ImportCsvAsync(collection, filePath, batchSize, continueOnDuplicateKey);
}
else if (filePath.EndsWith(".jsonl", StringComparison.OrdinalIgnoreCase) ||
         filePath.EndsWith(".ndjson", StringComparison.OrdinalIgnoreCase))
{
    await ImportJsonLinesAsync(collection, filePath, batchSize, continueOnDuplicateKey);
}
else
{
    Console.WriteLine("Unsupported file type. Use .csv or .jsonl/.ndjson");
}

// ----------------- Helpers -----------------

static async Task ImportCsvAsync(
    IMongoCollection<BsonDocument> collection,
    string path,
    int batchSize,
    bool continueOnDuplicateKey)
{
    using var reader = new StreamReader(path);

    string? headerLine = await reader.ReadLineAsync();
    if (string.IsNullOrWhiteSpace(headerLine))
        throw new InvalidOperationException("CSV is empty or missing headers.");

    var headers = SplitCsvLine(headerLine).ToArray();

    var buffer = new List<BsonDocument>(batchSize);
    long total = 0;

    while (!reader.EndOfStream)
    {
        var line = await reader.ReadLineAsync();
        if (string.IsNullOrWhiteSpace(line)) continue;

        var values = SplitCsvLine(line).ToArray();
        var doc = new BsonDocument();

        for (int i = 0; i < headers.Length; i++)
        {
            string key = headers[i];

            string raw = i < values.Length ? values[i] : "";
            doc[key] = InferBsonValue(raw);
        }

        buffer.Add(doc);

        if (buffer.Count >= batchSize)
        {
            total += await InsertBatchAsync(collection, buffer, continueOnDuplicateKey);
            Console.WriteLine($"Inserted: {total:n0}");
            buffer.Clear();
        }
    }

    if (buffer.Count > 0)
    {
        total += await InsertBatchAsync(collection, buffer, continueOnDuplicateKey);
        Console.WriteLine($"Inserted: {total:n0}");
    }
}

static async Task ImportJsonLinesAsync(
    IMongoCollection<BsonDocument> collection,
    string path,
    int batchSize,
    bool continueOnDuplicateKey)
{
    var buffer = new List<BsonDocument>(batchSize);
    long total = 0;

    foreach (var line in File.ReadLines(path))
    {
        if (string.IsNullOrWhiteSpace(line)) continue;

        // Parses JSON into BsonDocument. The JSON line should represent a single object.
        var doc = BsonDocument.Parse(line);

        buffer.Add(doc);

        if (buffer.Count >= batchSize)
        {
            total += await InsertBatchAsync(collection, buffer, continueOnDuplicateKey);
            Console.WriteLine($"Inserted: {total:n0}");
            buffer.Clear();
        }
    }

    if (buffer.Count > 0)
    {
        total += await InsertBatchAsync(collection, buffer, continueOnDuplicateKey);
        Console.WriteLine($"Inserted: {total:n0}");
    }
}

static async Task<int> InsertBatchAsync(
    IMongoCollection<BsonDocument> collection,
    List<BsonDocument> batch,
    bool continueOnDuplicateKey)
{
    try
    {
        // IsOrdered=false continues inserting even if some documents fail (e.g., duplicate key)
        await collection.InsertManyAsync(batch, new InsertManyOptions { IsOrdered = false });
        return batch.Count;
    }
    catch (MongoBulkWriteException<BsonDocument> ex) when (continueOnDuplicateKey)
    {
        // Count successful inserts even when some failed.
        // Most common: duplicate key error on _id.
        int inserted = ex.Result?.InsertedCount ?? 0;

        // If you want, print a short summary of failures:
        var dupes = ex.WriteErrors.Count(w => w.Category == ServerErrorCategory.DuplicateKey);
        Console.WriteLine($"Bulk write had errors. Inserted {inserted}, duplicate key errors: {dupes}");

        return inserted;
    }
}

// Very small CSV splitter with quotes support.
// Handles: a,b,"c,d","e""f"  -> c,d and e"f
static IEnumerable<string> SplitCsvLine(string line)
{
    if (line == null) yield break;

    bool inQuotes = false;
    var sb = new System.Text.StringBuilder();

    for (int i = 0; i < line.Length; i++)
    {
        char c = line[i];

        if (c == '"')
        {
            // Double quote inside quoted field -> literal quote
            if (inQuotes && i + 1 < line.Length && line[i + 1] == '"')
            {
                sb.Append('"');
                i++;
            }
            else
            {
                inQuotes = !inQuotes;
            }
        }
        else if (c == ',' && !inQuotes)
        {
            yield return sb.ToString().Trim();
            sb.Clear();
        }
        else
        {
            sb.Append(c);
        }
    }

    yield return sb.ToString().Trim();
}

// Simple type inference (optional).
// Empty -> BsonNull. numbers/bool/date -> typed. otherwise string.
static BsonValue InferBsonValue(string raw)
{
    if (raw == null) return BsonNull.Value;

    raw = raw.Trim();

    if (raw.Length == 0) return BsonNull.Value;

    // boolean
    if (bool.TryParse(raw, out bool b)) return b;

    // integer
    if (long.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out long l))
    {
        // store as Int32 when safe
        if (l >= int.MinValue && l <= int.MaxValue) return (int)l;
        return l;
    }

    // floating point
    if (double.TryParse(raw, NumberStyles.Float, CultureInfo.InvariantCulture, out double d))
        return d;

    // datetime (ISO-like or common formats)
    if (DateTime.TryParse(raw, CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal, out var dt))
        return dt;

    return raw; // string
}
