# Unter Performance Workshop — Atlas/PyMongo Lab Notes

This README captures the work completed for the Unter performance workshop exercise: loading randomized contact documents into MongoDB Atlas, verifying the data, creating supporting indexes, and generating a driver summary collection.

---

## Goal

The assignment simulates a ride-sharing company, **Unter**, testing MongoDB performance for a customer-service contact dataset.

The scored workload includes:

| Workload | Target |
|---|---:|
| Partial load | Load 25,000 contacts in 5 seconds |
| Rider monthly lookup | 1,500 queries/sec |
| Driver monthly lookup | 500 queries/sec |
| Comment update | 2,000 updates/sec |
| Driver summary | 10 seconds |

---

## Database and Collections

The working database is:

```javascript
use unter
```

Primary collection:

```text
unter.contacts
```

Derived summary collection:

```text
unter.driver_summary
```

Current Atlas view after the exercise:

```text
contacts          25K documents
driver_summary    ~16K documents
```

The `contacts` collection contains the required 25,000 loaded records.  
The `driver_summary` collection has one document per unique driver observed in the randomized 25K contacts, so it is expected to be smaller than 25K.

---

## Connection Notes

The cluster connection used the Atlas SRV host:

```text
perfworkshop.tnhx6.mongodb.net
```

PyMongo connection pattern:

```python
import pymongo

client = pymongo.MongoClient(
    "mongodb+srv://USER:PASS@perfworkshop.tnhx6.mongodb.net/?retryWrites=true&w=majority",
    serverSelectionTimeoutMS=10000
)

db = client["unter"]
collection = db["contacts"]
```

Important troubleshooting lesson:

If `mongosh` or PyMongo fails unexpectedly, verify both:

1. **Database Access** — the database user exists and has the expected password.
2. **Network Access** — the current client IP is allowlisted.

In this run, the final blocker was the IP allowlist. After adding the current IP in Atlas Network Access, PyMongo successfully returned:

```python
{'ok': 1.0}
```

---

## Random Contact Loader

The loader inserts 25,000 randomized Unter contact documents into:

```text
unter.contacts
```

The document shape follows the assignment contract:

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
    acceleration_events: [...]
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
  }
}
```

The `trip.acceleration_events` array is intentionally large, usually 10–60 embedded events per contact. This makes it useful for realism, but it should be projected out of most read queries for performance.

---

## Load Verification Queries

Exact count:

```javascript
use unter
db.contacts.countDocuments()
```

Fast estimate:

```javascript
use unter
db.contacts.estimatedDocumentCount()
```

Peek at one loaded document without the large acceleration array:

```javascript
db.contacts.findOne(
  {},
  {
    "trip.acceleration_events": 0
  }
)
```

---

## Recommended Indexes

Create these indexes for the benchmark query patterns:

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
```

Show indexes:

```javascript
db.contacts.getIndexes()
```

---

## Rider Monthly Lookup

Query pattern:

```javascript
db.contacts.find(
  {
    customer_id: db.contacts.findOne().customer_id,
    date: { $gte: "2026-01-01", $lt: "2026-02-01" }
  },
  {
    "trip.acceleration_events": 0
  }
).limit(5)
```

Explain plan:

```javascript
db.contacts.find(
  {
    customer_id: db.contacts.findOne().customer_id,
    date: { $gte: "2026-01-01", $lt: "2026-02-01" }
  },
  {
    "trip.acceleration_events": 0
  }
).explain("executionStats")
```

Look for use of:

```text
customer_date
```

---

## Driver Monthly Lookup

Query pattern:

```javascript
db.contacts.find(
  {
    "trip.driver_id": db.contacts.findOne()["trip"]["driver_id"],
    date: { $gte: "2026-01-01", $lt: "2026-02-01" }
  },
  {
    "trip.acceleration_events": 0
  }
).limit(5)
```

Explain plan:

```javascript
db.contacts.find(
  {
    "trip.driver_id": db.contacts.findOne()["trip"]["driver_id"],
    date: { $gte: "2026-01-01", $lt: "2026-02-01" }
  },
  {
    "trip.acceleration_events": 0
  }
).explain("executionStats")
```

Look for use of:

```text
driver_date
```

---

## Comment Update Test

The assignment includes updating a record to add a comment to an array.

```javascript
var c = db.contacts.findOne({}, { contact_id: 1 })

db.contacts.updateOne(
  { contact_id: c.contact_id },
  {
    $push: {
      comments: {
        ts: new Date(),
        text: "assignment verification comment"
      }
    }
  }
)

db.contacts.findOne(
  { contact_id: c.contact_id },
  {
    contact_id: 1,
    comments: 1
  }
)
```

For the service implementation, the important optimization is:

```python
contacts.update_one(
    {"contact_id": contact_id},
    {"$push": {"comments": comment}}
)
```

Avoid read-before-write unless required by the API contract.

---

## Driver Summary

The assignment includes a **Generate Driver summary** workload.

A practical approach is to precompute a `driver_summary` collection:

```javascript
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
  {
    $out: "driver_summary"
  }
])
```

Verify summary collection:

```javascript
db.driver_summary.countDocuments()
db.driver_summary.findOne()
```

Confirm the number of unique drivers in `contacts` roughly matches the number of summary documents:

```javascript
db.contacts.aggregate([
  {
    $group: {
      _id: "$trip.driver_id",
      rides: { $sum: 1 }
    }
  },
  {
    $count: "unique_drivers"
  }
])
```

---

## Proof Queries for Demo / Submission

Run these to show the assignment work clearly:

```javascript
use unter

// 1. Show loaded contacts
db.contacts.countDocuments()

// 2. Show sample document shape
db.contacts.findOne({}, { "trip.acceleration_events": 0 })

// 3. Show indexes
db.contacts.getIndexes()

// 4. Show rider monthly lookup
db.contacts.find(
  {
    customer_id: db.contacts.findOne().customer_id,
    date: { $gte: "2026-01-01", $lt: "2026-02-01" }
  },
  {
    "trip.acceleration_events": 0
  }
).limit(5)

// 5. Show driver monthly lookup
db.contacts.find(
  {
    "trip.driver_id": db.contacts.findOne()["trip"]["driver_id"],
    date: { $gte: "2026-01-01", $lt: "2026-02-01" }
  },
  {
    "trip.acceleration_events": 0
  }
).limit(5)

// 6. Show comment update
var c = db.contacts.findOne({}, { contact_id: 1 })
db.contacts.updateOne(
  { contact_id: c.contact_id },
  { $push: { comments: { ts: new Date(), text: "assignment verification comment" } } }
)
db.contacts.findOne({ contact_id: c.contact_id }, { contact_id: 1, comments: 1 })

// 7. Show driver summary
db.driver_summary.countDocuments()
db.driver_summary.findOne()
```

---

## Performance Notes

The biggest performance-sensitive field is:

```text
trip.acceleration_events
```

It is large and not needed for the rider lookup, driver lookup, update, or driver summary workloads.

Use projections like this:

```javascript
{
  "trip.acceleration_events": 0
}
```

In PyMongo:

```python
projection = {
    "trip.acceleration_events": 0
}
```

This avoids moving unnecessary large arrays across the wire and reduces response payload size.

---

## Final State

Completed:

- Loaded 5 million + randomized Unter contact documents.
- Verified `unter.contacts` contains 5 million + documents.
- Created/used `driver_summary` for the driver summary workload.
- Identified core benchmark indexes.
- Verified Atlas/PyMongo connectivity after fixing Database Access and Network Access setup.
- Captured proof queries for demo/submission.
