# CP3 MySQL to MongoDB Atlas Migration Workflow

## Scope

This design shows how CP3 can use the **MongoDB Kafka Connector** as the supported path into MongoDB Atlas without assuming Debezium.

The source system is MySQL. The target is MongoDB Atlas. Kafka is used as the transport layer. MongoDB Kafka Connector is used as the **sink connector** that writes final, already-transformed MongoDB documents into Atlas.

> Important: MongoDB Kafka Connector does not read from MySQL. It writes Kafka records to MongoDB Atlas as a sink, or reads MongoDB change streams as a source. For MySQL input, CP3 needs an existing supported MySQL-to-Kafka mechanism such as JDBC Source Connector, an application publisher, a batch extract job, or another customer-approved connector.

---

## High-Level Workflow

```text
MySQL Tables
  ├─ preferences
  ├─ sor_xwalk
  └─ topic / property / audit source tables
        ↓
Customer-supported MySQL → Kafka ingestion
        ↓
Raw Kafka Topics
        ↓
Transformation Layer
  ├─ Apply topicCode exclusion list
  ├─ Exclude canonical records when required
  ├─ Join / lookup sor_xwalk to derive EID
  ├─ Rename fields
  ├─ Convert timestamps to ISO 8601
  ├─ Rebuild nested MongoDB document structure
  └─ Recalculate document-level audit fields
        ↓
Canonical MongoDB Document Kafka Topic
        ↓
MongoDB Kafka Sink Connector
        ↓
MongoDB Atlas
```

---

## Recommended Component Responsibilities

| Component | Responsibility |
|---|---|
| MySQL ingestion into Kafka | Publish source records from MySQL into Kafka. This may be JDBC Source Connector, a custom application, or another customer-approved source mechanism. |
| Raw Kafka topics | Hold table-shaped source events or extracted records. |
| Transformation layer | Apply CP3-specific business rules and produce final MongoDB-shaped documents. |
| MongoDB Kafka Sink Connector | Write final canonical documents from Kafka into MongoDB Atlas. |
| MongoDB Atlas | Store the target `preferences` collection. |

---

## Why Custom Logic Is Required

Kafka Connect Single Message Transforms are useful for simple record-level changes, such as:

- Renaming fields
- Dropping fields
- Adding static fields
- Routing records to topics
- Light format changes

However, CP3's requirements go beyond simple per-record transformation:

1. The migration must exclude topics based on a predefined `topicCode` skip list.
2. The migration may need to exclude an entire canonical document if associated child records are excluded.
3. The migration must enrich `preferences` records with `EID` from `sor_xwalk`.
4. The migration must recalculate document-level audit data after topic exclusions.
5. The MongoDB target document is hierarchical, while the MySQL source is relational.

Because of this, the safest pattern is:

```text
Use SMTs only for lightweight transformations.
Use a custom transformation service for joins, filtering, nesting, and audit recalculation.
Use MongoDB Kafka Sink Connector only after the document is MongoDB-ready.
```

---

## Kafka Topic Design

Example topic layout:

```text
mysql.preferences.raw
mysql.sor_xwalk.raw
mysql.preference_topics.raw
mysql.preference_properties.raw
cp3.preferences.mongo.ready
cp3.preferences.deadletter
```

The `cp3.preferences.mongo.ready` topic should contain one Kafka message per final MongoDB document.

Example message key:

```json
{
  "c360Id": "C360123456"
}
```

Example message value:

```json
{
  "c360Id": "C360123456",
  "eid": "EID987654",
  "topic": [
    {
      "topicCode": "A",
      "topicDescription": "string",
      "property": [
        {
          "propertyCode": "Some String",
          "propertyOption": [
            {
              "optionCode": "string",
              "optionValue": "string"
            }
          ],
          "propertyDescription": "string"
        }
      ],
      "topicAuditType": {
        "topicAuditDateTime": "2018-08-20T14:33:42Z",
        "systemModifiedDateTime": "2026-05-11T14:15:19Z",
        "topicAuditSourceId": null,
        "topicAuditApplicationId": "string"
      }
    }
  ],
  "auditType": {
    "applicationId": "string",
    "auditDateTime": "2018-08-30T18:06:09Z",
    "systemModifiedDateTime": "2026-05-11T14:15:19Z",
    "auditSourceId": null
  },
  "sourceSystemCode": "C360",
  "individualIdentifier": "string"
}
```

---

## Transformation Rules

### 1. Exclude Skipped Topics

Maintain a configurable skip list:

```json
{
  "excludedTopicCodes": ["X", "Y", "Z"]
}
```

Transformation logic:

```text
For each canonical preference document:
  remove topic entries where topic.topicCode is in excludedTopicCodes
```

---

### 2. Exclude Canonical Records

If upstream rules require the canonical record to be excluded when certain related child records are excluded, apply that rule before writing to the MongoDB-ready topic.

Example policy options:

```text
Policy A: Exclude only skipped child topics.
Policy B: Exclude the entire canonical document if all topics are skipped.
Policy C: Exclude the entire canonical document if any upstream exclusion flag applies.
Policy D: Exclude the entire canonical document if a required child record is missing after filtering.
```

The exact policy should be confirmed with CP3 upstream owners.

---

### 3. Derive EID from `sor_xwalk`

Source tables:

```text
preferences.c360Id
sor_xwalk.c360Id
sor_xwalk.eid
```

Transformation logic:

```text
For each preferences record:
  lookup sor_xwalk by c360Id
  add eid to the MongoDB document
```

If no match exists, choose one of these behaviors:

```text
Option 1: Reject the record to the dead-letter topic.
Option 2: Write the document with eid = null.
Option 3: Hold the record until the lookup becomes available.
```

Recommended default: reject to dead-letter topic unless CP3 confirms `eid` is optional.

---

### 4. Convert Date Fields to ISO 8601

Convert these fields during transformation:

```text
topicAuditDateTime
systemModifiedDateTime
auditDateTime
```

Example:

```text
2018-08-30 18:06:09 → 2018-08-30T18:06:09Z
```

The transformation layer should standardize timezone handling. Do not assume local time unless CP3 confirms the source timezone.

---

### 5. Recalculate Document-Level Audit

Do not copy the original document-level audit blindly.

After topic exclusions are applied:

```text
remainingTopics = topics excluding skipped topicCodes
latestTopic = topic with max(topic.topicAuditType.topicAuditDateTime)
document.auditType.auditDateTime = latestTopic.topicAuditType.topicAuditDateTime
document.auditType.systemModifiedDateTime = latestTopic.topicAuditType.systemModifiedDateTime
```

Example:

```text
Original topics: A, B, C, D, E
Topic E has latest audit timestamp
Topic E is skipped
Remaining topics: A, B, C, D
Use the latest audit timestamp from A, B, C, or D
```

If no topics remain, apply the canonical exclusion policy.

---

## Where to Put the Custom Logic

### Preferred Pattern

```text
Raw Kafka Topics
   ↓
Custom Stream Processor / Transformation Service
   ↓
MongoDB-ready Kafka Topic
   ↓
MongoDB Kafka Sink Connector
```

The transformation service can be implemented using:

- Kafka Streams
- Java service using Kafka consumer/producer APIs
- Python service using Kafka consumer/producer APIs
- Spark Structured Streaming
- Flink
- Any CP3-approved stream processing platform

This is preferred because CP3 needs cross-record logic, joins, document assembly, and audit recomputation.

---

## Role of Kafka Connect SMTs

SMTs can still be used, but only for simple transformations at connector boundaries.

Example uses:

```text
- Rename a simple field
- Drop technical columns
- Insert static metadata
- Route invalid messages
- Mask a field
```

SMTs should not be the primary place for:

```text
- Multi-table joins
- Building nested arrays
- Recalculating document-level audit from child topics
- Stateful canonical-record exclusion logic
- Holding records until related rows arrive
```

A custom SMT could technically perform some business logic, but it is not the best fit for stateful, multi-table document construction.

---

## MongoDB Kafka Sink Connector Configuration Example

This connector consumes final MongoDB-ready records from Kafka and writes them to MongoDB Atlas.

```json
{
  "name": "cp3-preferences-mongodb-sink",
  "config": {
    "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
    "tasks.max": "4",
    "topics": "cp3.preferences.mongo.ready",
    "connection.uri": "${file:/opt/kafka/external-configuration/mongodb.properties:connection.uri}",
    "database": "cp3",
    "collection": "preferences",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter.schemas.enable": "false",
    "document.id.strategy": "com.mongodb.kafka.connect.sink.processor.id.strategy.PartialValueStrategy",
    "document.id.strategy.partial.value.projection.list": "c360Id",
    "document.id.strategy.partial.value.projection.type": "AllowList",
    "writemodel.strategy": "com.mongodb.kafka.connect.sink.writemodel.strategy.ReplaceOneDefaultStrategy",
    "max.num.retries": "10",
    "retries.defer.timeout": "5000",
    "errors.tolerance": "all",
    "errors.deadletterqueue.topic.name": "cp3.preferences.deadletter",
    "errors.deadletterqueue.context.headers.enable": "true"
  }
}
```

Notes:

- Use a stable document identifier such as `c360Id` or a composite business key.
- Use replace/upsert behavior for incremental loads where the full canonical document is rebuilt.
- Store the Atlas connection string securely, not directly in the connector config.

---

## Incremental Load Behavior

For incremental loads, the transformation layer should rebuild the affected canonical document whenever any related source record changes.

Examples:

```text
preferences row changes → rebuild document for c360Id
sor_xwalk row changes → rebuild document for affected c360Id
preference topic row changes → rebuild document for c360Id
property row changes → rebuild document for c360Id
```

The sink connector then replaces the existing MongoDB document with the newly rebuilt canonical version.

Recommended write model:

```text
ReplaceOne with upsert semantics
```

This avoids partial-update drift and ensures the MongoDB document always reflects the current transformed state.

---

## Validation Checks

Before enabling production writes, validate:

```text
1. Count of eligible canonical records after exclusions
2. Count of excluded topic records by topicCode
3. Count of excluded canonical records
4. Count of records missing EID
5. Audit timestamp recalculation accuracy
6. Date format consistency
7. MongoDB document shape
8. Idempotent reprocessing behavior
9. Dead-letter topic volume and causes
```

---

## Recommended Answer to CP3

The MongoDB Kafka Connector can be used as the supported sink into MongoDB Atlas, but the CP3-specific customization should be implemented before the sink connector receives the message.

The recommended design is to publish MySQL data into Kafka using the customer-supported MySQL ingestion mechanism, process the raw table events through a custom transformation layer, and emit final MongoDB-ready canonical documents to a Kafka topic. The MongoDB Kafka Sink Connector then writes those documents into Atlas.

This keeps the connector configuration simple and supportable while placing CP3-specific business logic—topic exclusions, canonical exclusions, EID enrichment, date conversion, field renaming, document nesting, and audit recalculation—in a dedicated transformation layer where it can be tested and validated.
