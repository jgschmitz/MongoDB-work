# Unter Performance Workshop — Atlas + PyMongo Submission Notes

This README documents the completed Unter performance workshop exercise: loading a 5M-contact ride-support dataset into MongoDB Atlas, creating benchmark indexes, validating query plans, building a materialized driver summary, and measuring QPS.

> Credentials are intentionally omitted. Replace `USER:PASS` with a valid Atlas database user before running scripts.

---

## Executive Summary

The assignment was to optimize MongoDB performance for a ride-sharing company, **Unter**, using a customer-service contact dataset.

| Benchmark Area | Assignment Goal |
|---|---:|
| Partial load | Load 25,000 contacts |
| Full historic load | Load 5M contacts |
| Rider monthly lookup | Retrieve 1 month of rides by rider |
| Driver monthly lookup | Retrieve 1 month of rides by driver |
| Comment update | Add a comment to an array on one contact |
| Driver summary | Generate summary statistics by driver |

Completed work:

- Loaded the dataset into `unter.contacts`.
- Scaled Atlas storage and cluster tier to support the full load.
- Built benchmark indexes for rider lookup, driver lookup, and contact update.
- Generated `unter.driver_summary` as a materialized summary collection.
- Verified lookup/update paths with `explain("executionStats")`.
- Measured concurrent QPS from a local PyMongo benchmark.
- Captured shell proof queries and submission artifacts.

---

## Architecture

```mermaid
flowchart LR
    Laptop["Local Laptop<br/>Python / mongosh / Compass"] --> Atlas["MongoDB Atlas<br/>perfworkshop.tnhx6.mongodb.net"]

    Atlas --> Contacts["unter.contacts<br/>5M contact documents"]
    Atlas --> Summary["unter.driver_summary<br/>25K driver docs"]

    Contacts --> Index1["customer_date<br/>{ customer_id: 1, date: 1 }"]
    Contacts --> Index2["driver_date<br/>{ trip.driver_id: 1, date: 1 }"]
    Contacts --> Index3["contact_id_unique<br/>{ contact_id: 1 } unique"]

    Contacts --> Agg["Aggregation<br/>group by trip.driver_id"]
    Agg --> Summary
    Summary --> Index4["rides_desc<br/>{ rides: -1 }"]

    Bench["qps_benchmark.py<br/>concurrent PyMongo"] --> Atlas
```

---

## Environment Used

The original lab expected an EC2 instance and Atlas cluster provisioned together. In this run, the implementation was done locally.

| Component | Used |
|---|---|
| Client | Local laptop |
| Tools | Python, PyMongo, mongosh, Compass |
| Database | MongoDB Atlas |
| Cluster host | `perfworkshop.tnhx6.mongodb.net` |
| Database | `unter` |
| Primary collection | `contacts` |
| Summary collection | `driver_summary` |

Important setup items:

- Atlas database user had to be created for the new cluster.
- Local laptop IP had to be allowlisted in Atlas Network Access.
- Disk was scaled up to support the 5M full load.
- Cluster was scaled up to M140 during the full load to improve throughput.

---

## Data Model

Each document in `unter.contacts` follows the Unter contact contract:

```javascript
{
  contact_id,
  timestamp,
  date,
  customer_id,
  trip: {
    trip_id,
    vehicle_id,
    vehicle_type,
    driver_id,
    start_location_id,
    end_location_id,
    city,
    trip_length_minutes,
    trip_distance_miles,
    fare_amount,
    surge_multiplier,
    acceleration_events: [
      { ts, x, y, z, lat, lon }
    ]
  },
  contact: {
    channel,
    reason,
    status,
    resolution,
    response_time_minutes,
    sentiment
  },
  star_rating,
  driver_rating: {
    driver_id,
    rating,
    driver_lifetime_avg_rating,
    driver_total_trips
  },
  comments
}
```

The largest field is:

```text
trip.acceleration_events
```

Most benchmark queries project this field out because it is not needed for rider lookup, driver lookup, update, or driver summary.

---

## PyMongo Connection Pattern

```python
import pymongo

client = pymongo.MongoClient(
    "mongodb+srv://USER:PASS@perfworkshop.tnhx6.mongodb.net/?retryWrites=true&w=majority",
    serverSelectionTimeoutMS=10000,
    maxPoolSize=300,
)

db = client["unter"]
contacts = db["contacts"]
driver_summary = db["driver_summary"]
```

Connectivity sanity check:

```python
print(client.admin.command("ping"))
```

Expected result:

```python
{'ok': 1.0}
```

---

## Loader

The loader generated randomized Unter contact documents and inserted them into:

```text
unter.contacts
```

For the partial benchmark:

```python
TOTAL_DOCS = 25_000
```

For the full historic load:

```python
TOTAL_DOCS = 5_000_000
```

Recommended loader settings after scaling Atlas:

```python
BATCH_SIZE = 10_000
```

Recommended progress logging:

```python
if inserted % 100_000 == 0:
    print(f"Inserted {inserted:,}/{TOTAL_DOCS:,}")
```

---

## Database Objects

Expected collections after completion:

```text
unter.contacts
unter.driver_summary
```

Expected full-load state:

```text
unter.contacts          ~5,000,000 documents
unter.driver_summary       25,000 documents
```

`driver_summary` has one document per unique driver. With 5M contacts randomly distributed across 25K drivers, all 25K drivers appeared.

---

## Benchmark Indexes

Create these after the full load if possible:

```javascript
use unter

db.contacts.createIndex(
  { customer_id: 1, date: 1 },
  { name: "customer_date" }
)

db.contacts.createIndex(
  { "trip.driver_id": 1, date: 1 },
  { name: "driver_date" }
)

db.contacts.createIndex(
  { contact_id: 1 },
  { name: "contact_id_unique", unique: true }
)

db.driver_summary.createIndex(
  { rides: -1 },
  { name: "rides_desc" }
)
```

Verify:

```javascript
db.contacts.getIndexes()
db.driver_summary.getIndexes()
```

---

## Driver Summary Generation

The driver summary was implemented as a materialized summary collection.

```mermaid
flowchart TD
    A["unter.contacts<br/>5M docs"] --> B["$project<br/>driver_id, fare, distance, minutes, rating"]
    B --> C["$group by driver_id"]
    C --> D["rides<br/>total_fare<br/>total_distance<br/>avg_rating<br/>avg_trip_minutes"]
    D --> E["$out: driver_summary"]
```

Aggregation:

```javascript
use unter

db.contacts.aggregate([
  {
    $project: {
      driver_id: "$trip.driver_id",
      fare_amount: "$trip.fare_amount",
      trip_distance_miles: "$trip.trip_distance_miles",
      trip_length_minutes: "$trip.trip_length_minutes",
      star_rating: 1
    }
  },
  {
    $group: {
      _id: "$driver_id",
      rides: { $sum: 1 },
      total_fare: { $sum: "$fare_amount" },
      total_distance: { $sum: "$trip_distance_miles" },
      avg_rating: { $avg: "$star_rating" },
      avg_trip_minutes: { $avg: "$trip_length_minutes" }
    }
  },
  { $out: "driver_summary" }
])
```

Verify:

```javascript
db.driver_summary.countDocuments()
db.driver_summary.findOne()
```

Expected count:

```text
25000
```

Materialized-view note:

> The first pass generated `driver_summary` as a materialized summary from `contacts`, which fits the benchmark step. A later improvement would be updating driver stats during the load path so summary reads are instant and do not need to rescan `contacts`.

---

## Proof Queries

### Show Contacts Loaded

```javascript
use unter
db.contacts.countDocuments()
```

Fast estimate:

```javascript
db.contacts.estimatedDocumentCount()
```

### Show Document Shape Without Heavy Array

```javascript
db.contacts.findOne(
  {},
  {
    "trip.acceleration_events": 0
  }
)
```

### Rider Monthly Lookup

```javascript
var sample = db.contacts.findOne({}, { customer_id: 1, date: 1 })

db.contacts.find(
  {
    customer_id: sample.customer_id,
    date: {
      $gte: sample.date.substring(0, 7) + "-01",
      $lt: sample.date.substring(0, 7) === "2026-12"
        ? "2027-01-01"
        : "2026-" + String(Number(sample.date.substring(5, 7)) + 1).padStart(2, "0") + "-01"
    }
  },
  {
    _id: 0,
    contact_id: 1,
    date: 1,
    customer_id: 1,
    "trip.trip_id": 1,
    "trip.driver_id": 1,
    "trip.city": 1,
    "trip.trip_distance_miles": 1,
    "trip.fare_amount": 1,
    "contact.reason": 1,
    "contact.status": 1,
    star_rating: 1
  }
).hint("customer_date").limit(5)
```

### Driver Monthly Lookup

```javascript
var sample = db.contacts.findOne({}, { "trip.driver_id": 1, date: 1 })

db.contacts.find(
  {
    "trip.driver_id": sample.trip.driver_id,
    date: {
      $gte: sample.date.substring(0, 7) + "-01",
      $lt: sample.date.substring(0, 7) === "2026-12"
        ? "2027-01-01"
        : "2026-" + String(Number(sample.date.substring(5, 7)) + 1).padStart(2, "0") + "-01"
    }
  },
  {
    _id: 0,
    contact_id: 1,
    date: 1,
    customer_id: 1,
    "trip.trip_id": 1,
    "trip.driver_id": 1,
    "trip.city": 1,
    "trip.trip_distance_miles": 1,
    "trip.fare_amount": 1,
    "contact.reason": 1,
    "contact.status": 1,
    star_rating: 1
  }
).hint("driver_date").limit(5)
```

### Comment Update

```javascript
var sample = db.contacts.findOne({}, { contact_id: 1 })

db.contacts.updateOne(
  { contact_id: sample.contact_id },
  {
    $push: {
      comments: {
        ts: new Date(),
        text: "x"
      }
    }
  },
  { hint: "contact_id_unique" }
)
```

### Driver Summary Read

```javascript
db.driver_summary.find(
  {},
  {
    _id: 1,
    rides: 1,
    total_fare: 1,
    total_distance: 1,
    avg_rating: 1,
    avg_trip_minutes: 1
  }
).sort({ rides: -1 }).hint("rides_desc").limit(10)
```

---

## Explain Plan Results

### Rider Lookup Explain

Observed result:

```text
stage: IXSCAN
indexName: customer_date
executionTimeMillis: 0
nReturned: 2
totalKeysExamined: 2
totalDocsExamined: 2
```

### Driver Lookup Explain

Observed result:

```text
stage: IXSCAN
indexName: driver_date
executionTimeMillis: 0
nReturned: 11
totalKeysExamined: 11
totalDocsExamined: 11
```

### Comment Update Explain

Observed result:

```text
stage: UPDATE
inputStage: IXSCAN
indexName: contact_id_unique
isUnique: true
executionTimeMillis: 0
totalKeysExamined: 1
totalDocsExamined: 1
nMatched: 1
nWouldModify: 1
```

---

## QPS Benchmark Results

The first serial `mongosh` loop was misleading because it measured one blocking round trip at a time from a laptop to Atlas. The QPS benchmark was changed to use concurrent PyMongo requests.

```text
╔════════════════════════════════════╗
║    UNTER PERFORMANCE SCOREBOARD    ║
╚════════════════════════════════════╝
Workload                            QPS     Target              Score  Verdict
──────────────────────────────────────────────────────────────────────────────────
Rider monthly lookup                410      1,500    27.3% of target     TUNE
Driver monthly lookup               375        500    75.1% of target    CLOSE
Comment update                      878      2,000    43.9% of target     TUNE
Driver summary read                 252        n/a                n/a     INFO
──────────────────────────────────────────────────────────────────────────────────
Notes:
  IXSCAN verified for rider, driver, and update paths.
  Shell/Compass serial loops are not valid QPS benchmarks.
  This benchmark uses concurrent PyMongo client requests.
```

Interpretation:

- Database-side query plans are good.
- Lookups and update all use the intended indexes.
- The measured QPS includes local laptop network latency and client overhead.
- Better numbers would likely come from an in-region client, the official test harness, or a service running near Atlas.

---

## Suggested Submission Package

```text
README.md
contractCranker.py
qps_benchmark.py
setup_indexes_and_summary.js
results.txt
screenshots/
```

Suggested `setup_indexes_and_summary.js`:

```javascript
use unter

db.contacts.createIndex({ customer_id: 1, date: 1 }, { name: "customer_date" })
db.contacts.createIndex({ "trip.driver_id": 1, date: 1 }, { name: "driver_date" })
db.contacts.createIndex({ contact_id: 1 }, { name: "contact_id_unique", unique: true })
db.driver_summary.createIndex({ rides: -1 }, { name: "rides_desc" })

db.contacts.aggregate([
  {
    $project: {
      driver_id: "$trip.driver_id",
      fare_amount: "$trip.fare_amount",
      trip_distance_miles: "$trip.trip_distance_miles",
      trip_length_minutes: "$trip.trip_length_minutes",
      star_rating: 1
    }
  },
  {
    $group: {
      _id: "$driver_id",
      rides: { $sum: 1 },
      total_fare: { $sum: "$fare_amount" },
      total_distance: { $sum: "$trip_distance_miles" },
      avg_rating: { $avg: "$star_rating" },
      avg_trip_minutes: { $avg: "$trip_length_minutes" }
    }
  },
  { $out: "driver_summary" }
])
```

---

## Final Notes

This implementation focused on the main benchmark strategy:

- Keep the primary contact shape intact.
- Avoid returning large `acceleration_events` arrays.
- Use targeted compound indexes for the lookup paths.
- Use a unique `contact_id` index for updates.
- Use a materialized `driver_summary` collection for driver summary reads.
- Validate performance with `explain("executionStats")`.

The important database-side result is that the benchmark paths all use efficient index scans:

```text
Rider lookup  -> customer_date index   -> IXSCAN
Driver lookup -> driver_date index     -> IXSCAN
Update        -> contact_id_unique     -> IXSCAN
Summary read  -> driver_summary        -> materialized result
```
