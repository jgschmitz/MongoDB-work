# End-to-End Streaming Migration Workflow: MySQL → Kafka Connect/Debezium → Custom SMT → MongoDB Atlas

## Purpose

This document describes how CP3 can implement a streaming migration from MySQL to MongoDB Atlas using:

- **Debezium MySQL Source Connector** for initial snapshot and ongoing CDC.
- **Kafka topics** as the durable event backbone.
- **Kafka Connect Single Message Transforms (SMTs)** for lightweight field-level changes.
- **Custom Kafka Connect SMT logic** for CP3-specific filtering and enrichment.
- **MongoDB Kafka Sink Connector** to write final canonical documents into MongoDB Atlas.

The goal is to support the full workflow, including:

1. Incremental data load from MySQL.
2. Exclusion of predefined `topicCode` values.
3. Exclusion of associated canonical records when required by upstream rules.
4. Renaming columns/fields.
5. Joining or enriching records with `EID` from `sor_xwalk`.
6. Converting audit timestamps to ISO 8601.
7. Recalculating document-level audit data after skipped topics are removed.
8. Writing final records into MongoDB Atlas.

---

## 1. Recommended Architecture

```text
MySQL
  ├── preferences
  ├── sor_xwalk
  ├── topic tables
  └── exclusion/reference tables
        │
        ▼
Debezium MySQL Source Connector
  - Initial snapshot
  - CDC/binlog streaming
  - Optional incremental snapshots
        │
        ▼
Kafka Topics
  - mysql.cp3.preferences
  - mysql.cp3.sor_xwalk
  - mysql.cp3.preference_topic
  - mysql.cp3.exclusion_rules
        │
        ▼
Kafka Connect SMT Layer
  - Built-in SMTs for simple rename/drop/route
  - Custom SMT for CP3-specific logic
        │
        ▼
Optional Stateful Aggregation Layer
  - Kafka Streams / Flink / custom consumer
  - Needed when building full canonical MongoDB documents from multiple rows/topics
        │
        ▼
MongoDB Kafka Sink Connector
        │
        ▼
MongoDB Atlas
  - preferences collection
```

---

## 2. Important Design Decision

Kafka Connect SMTs are best for **single-record transformations**. They can rename fields, mask fields, route topics, filter records, and modify individual messages.

However, CP3 requirements include **multi-row and cross-table logic**, such as:

- Looking up `EID` from `sor_xwalk`.
- Rebuilding a canonical document from multiple topic rows.
- Recalculating document-level audit data after excluded topics are removed.
- Excluding a canonical record based on child-record rules.

Those requirements are **stateful**. A custom SMT can implement some of this if it uses an external lookup/cache, but the safer architecture is:

```text
Built-in SMTs + Custom SMT for lightweight validation/filtering/enrichment
Kafka Streams/Flink/custom aggregation for document assembly
MongoDB Kafka Sink Connector for final writes
```

Use a custom SMT only when the transformation can be done from the current event plus a small cached reference dataset. Use Kafka Streams or a custom processor when the target MongoDB document depends on multiple related events.

---

## 3. Source Tables

Example MySQL source tables:

```text
preferences
  - c360Id
  - sourceSystemCode
  - auditDateTime
  - systemModifiedDateTime
  - other preference-level columns

preference_topic
  - c360Id
  - topicCode
  - topicAuditDateTime
  - systemModifiedDateTime
  - topicDescription
  - other topic-level columns

preference_property
  - c360Id
  - topicCode
  - propertyCode
  - optionCode
  - optionValue

sor_xwalk
  - c360Id
  - eid

topic_exclusion
  - topicCode
  - activeFlag

canonical_exclusion
  - c360Id
  - reasonCode
  - activeFlag
```

---

## 4. Target MongoDB Shape

Example MongoDB document:

```json
{
  "_id": "C360-123",
  "c360Id": "C360-123",
  "eid": "EID-999",
  "sourceSystemCode": "C360",
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
        "systemModifiedDateTime": "2026-05-11T14:15:19Z"
      }
    }
  ],
  "auditType": {
    "applicationId": "string",
    "auditDateTime": "2018-08-20T14:33:42Z",
    "systemModifiedDateTime": "2026-05-11T14:15:19Z"
  }
}
```

---

## 5. Incremental Load Strategy

### 5.1 Initial Snapshot

Configure Debezium to snapshot the existing MySQL data.

```json
{
  "name": "cp3-mysql-source",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "database.hostname": "mysql-host",
    "database.port": "3306",
    "database.user": "${file:/opt/connect/secrets/mysql.properties:user}",
    "database.password": "${file:/opt/connect/secrets/mysql.properties:password}",
    "database.server.id": "184054",
    "topic.prefix": "mysql.cp3",
    "database.include.list": "cp3",
    "table.include.list": "cp3.preferences,cp3.preference_topic,cp3.preference_property,cp3.sor_xwalk,cp3.topic_exclusion,cp3.canonical_exclusion",
    "snapshot.mode": "initial",
    "include.schema.changes": "false",
    "schema.history.internal.kafka.bootstrap.servers": "kafka:9092",
    "schema.history.internal.kafka.topic": "schemahistory.cp3"
  }
}
```

### 5.2 Ongoing CDC

After the snapshot completes, Debezium continues reading MySQL binlog changes and emits inserts, updates, and deletes into Kafka.

### 5.3 Incremental Snapshots for Reloads

Use Debezium incremental snapshots when CP3 needs to backfill or reload selected tables without stopping the CDC stream.

Example signaling table:

```sql
CREATE TABLE cp3.debezium_signal (
  id VARCHAR(64) PRIMARY KEY,
  type VARCHAR(32) NOT NULL,
  data VARCHAR(2048) NULL
);
```

Example signal:

```sql
INSERT INTO cp3.debezium_signal (id, type, data)
VALUES (
  UUID(),
  'execute-snapshot',
  '{"data-collections":["cp3.preferences","cp3.preference_topic"]}'
);
```

---

## 6. Kafka Topic Design

Recommended topic layout:

```text
mysql.cp3.preferences
mysql.cp3.preference_topic
mysql.cp3.preference_property
mysql.cp3.sor_xwalk
mysql.cp3.topic_exclusion
mysql.cp3.canonical_exclusion
```

Recommended keying:

```text
preferences:          c360Id
preference_topic:     c360Id + topicCode
preference_property:  c360Id + topicCode + propertyCode
sor_xwalk:            c360Id
topic_exclusion:      topicCode
canonical_exclusion:  c360Id
```

Use compacted topics for reference/lookup data:

```text
mysql.cp3.sor_xwalk
mysql.cp3.topic_exclusion
mysql.cp3.canonical_exclusion
```

This allows the custom SMT or aggregation layer to maintain a local cache of lookup records.

---

## 7. Transformation Responsibilities

| Requirement | Recommended Implementation |
|---|---|
| Rename fields | Built-in SMT or custom SMT |
| Convert timestamps to ISO 8601 | Custom SMT or aggregation layer |
| Exclude topicCodes | Custom SMT or aggregation layer |
| Exclude canonical records | Aggregation layer recommended |
| Add EID from `sor_xwalk` | Aggregation layer recommended; custom SMT possible with cache |
| Recalculate document audit fields | Aggregation layer strongly recommended |
| Build nested MongoDB document | Aggregation layer strongly recommended |
| Write to MongoDB Atlas | MongoDB Kafka Sink Connector |

---

## 8. Built-In SMT Examples

Built-in SMTs can handle simple operations before CP3 custom logic runs.

Example: unwrap Debezium envelope and route topic names.

```json
{
  "transforms": "unwrap,route",
  "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
  "transforms.unwrap.drop.tombstones": "false",
  "transforms.unwrap.delete.handling.mode": "rewrite",

  "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
  "transforms.route.regex": "mysql.cp3.(.*)",
  "transforms.route.replacement": "cp3.$1"
}
```

Example: rename fields.

```json
{
  "transforms": "renameFields",
  "transforms.renameFields.type": "org.apache.kafka.connect.transforms.ReplaceField$Value",
  "transforms.renameFields.renames": "C360_ID:c360Id,SOURCE_SYSTEM_CODE:sourceSystemCode"
}
```

---

## 9. Custom SMT Design

### 9.1 Purpose

The custom SMT can perform CP3-specific record-level customization:

- Drop records with excluded `topicCode`.
- Normalize timestamps.
- Rename or restructure fields.
- Add derived metadata.
- Optionally enrich `preferences` records with `eid` using a local cache.
- Mark records that require canonical deletion or recomputation.

### 9.2 Configuration Example

```json
{
  "transforms": "unwrap,cp3Transform",
  "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
  "transforms.unwrap.drop.tombstones": "false",
  "transforms.unwrap.delete.handling.mode": "rewrite",

  "transforms.cp3Transform.type": "com.company.cp3.kafka.Cp3PreferenceTransform",
  "transforms.cp3Transform.excluded.topic.codes": "X01,X02,X03",
  "transforms.cp3Transform.timestamp.fields": "topicAuditDateTime,systemModifiedDateTime,auditDateTime",
  "transforms.cp3Transform.timestamp.output.format": "ISO_OFFSET_DATE_TIME",
  "transforms.cp3Transform.eid.cache.topic": "cp3.sor_xwalk",
  "transforms.cp3Transform.canonical.exclusion.topic": "cp3.canonical_exclusion",
  "transforms.cp3Transform.drop.canonical.when.excluded": "true"
}
```

### 9.3 Custom SMT Pseudocode

```java
public class Cp3PreferenceTransform<R extends ConnectRecord<R>> implements Transformation<R> {

    private Set<String> excludedTopicCodes;
    private Map<String, String> c360ToEidCache;
    private Set<String> excludedCanonicalIds;

    @Override
    public R apply(R record) {
        if (record.value() == null) {
            return record;
        }

        Struct value = (Struct) record.value();

        String c360Id = getString(value, "c360Id");
        String topicCode = getString(value, "topicCode");

        // Rule 1: Drop canonical record if upstream canonical exclusion says so.
        if (c360Id != null && excludedCanonicalIds.contains(c360Id)) {
            return null;
        }

        // Rule 2: Drop skipped topic records.
        if (topicCode != null && excludedTopicCodes.contains(topicCode)) {
            return null;
        }

        // Rule 3: Enrich with EID if available.
        if (c360Id != null) {
            String eid = c360ToEidCache.get(c360Id);
            if (eid != null) {
                value = putField(value, "eid", eid);
            }
        }

        // Rule 4: Convert timestamp fields to ISO 8601.
        value = normalizeTimestamp(value, "topicAuditDateTime");
        value = normalizeTimestamp(value, "auditDateTime");
        value = normalizeTimestamp(value, "systemModifiedDateTime");

        // Rule 5: Rename fields as required by MongoDB schema.
        value = renameField(value, "source_system_code", "sourceSystemCode");

        return record.newRecord(
            record.topic(),
            record.kafkaPartition(),
            record.keySchema(),
            record.key(),
            value.schema(),
            value,
            record.timestamp()
        );
    }

    @Override
    public ConfigDef config() {
        return new ConfigDef()
            .define("excluded.topic.codes", ConfigDef.Type.LIST, ConfigDef.Importance.HIGH, "Topic codes to exclude")
            .define("timestamp.fields", ConfigDef.Type.LIST, ConfigDef.Importance.MEDIUM, "Timestamp fields to normalize")
            .define("eid.cache.topic", ConfigDef.Type.STRING, ConfigDef.Importance.MEDIUM, "Compacted EID lookup topic");
    }

    @Override
    public void configure(Map<String, ?> configs) {
        // Load excluded topic codes.
        // Initialize lookup caches from compacted Kafka topics or external store.
    }

    @Override
    public void close() {
        // Close cache clients and resources.
    }
}
```

### 9.4 Important SMT Limitation

A custom SMT processes one Kafka record at a time. It should not be the primary place to build the entire nested MongoDB document if that document requires multiple child rows. Use Kafka Streams, Flink, or a custom aggregation consumer for that.

---

## 10. Stateful Aggregation Layer

Because CP3 needs to recalculate audit fields after exclusions, a stateful processor is recommended.

### 10.1 Responsibilities

The aggregation layer should:

1. Consume `preferences`, `preference_topic`, `preference_property`, `sor_xwalk`, and exclusion topics.
2. Maintain state stores keyed by `c360Id`.
3. Remove excluded topics.
4. Remove excluded canonical records.
5. Join `c360Id` to `eid`.
6. Build the nested MongoDB document.
7. Recalculate document-level audit fields using only remaining valid topics.
8. Emit final documents to a Kafka topic consumed by the MongoDB Sink Connector.

Recommended output topic:

```text
cp3.preferences.mongo.final
```

### 10.2 Audit Recalculation Logic

Given topics A, B, C, D, and E:

```text
A topicAuditDateTime = 2018-08-20T14:33:42Z
B topicAuditDateTime = 2018-08-30T18:06:09Z
C topicAuditDateTime = 2018-08-15T09:00:00Z
D topicAuditDateTime = 2018-08-10T11:00:00Z
E topicAuditDateTime = 2020-01-01T00:00:00Z
```

If topic E is excluded, do not use E for document-level audit.

The recalculated document-level audit timestamp should be:

```text
2018-08-30T18:06:09Z
```

because topic B is the latest remaining valid topic.

Pseudocode:

```java
List<Topic> validTopics = allTopics.stream()
    .filter(topic -> !excludedTopicCodes.contains(topic.getTopicCode()))
    .toList();

Optional<Instant> latestAudit = validTopics.stream()
    .map(topic -> topic.getTopicAuditDateTime())
    .filter(Objects::nonNull)
    .max(Comparator.naturalOrder());

document.auditType.auditDateTime = latestAudit.orElse(null);
```

---

## 11. MongoDB Kafka Sink Connector

The MongoDB Sink Connector writes the final assembled documents into MongoDB Atlas.

Example connector configuration:

```json
{
  "name": "cp3-mongodb-sink",
  "config": {
    "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
    "topics": "cp3.preferences.mongo.final",
    "connection.uri": "${file:/opt/connect/secrets/mongodb.properties:connection.uri}",
    "database": "cp3",
    "collection": "preferences",

    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter.schemas.enable": "false",

    "document.id.strategy": "com.mongodb.kafka.connect.sink.processor.id.strategy.ProvidedInValueStrategy",
    "document.id.strategy.overwrite.existing": "true",
    "writemodel.strategy": "com.mongodb.kafka.connect.sink.writemodel.strategy.ReplaceOneDefaultStrategy",

    "max.num.retries": "5",
    "retries.defer.timeout": "5000"
  }
}
```

The final event should include `_id` so the sink connector can upsert/replace the correct MongoDB document:

```json
{
  "_id": "C360-123",
  "c360Id": "C360-123",
  "eid": "EID-999",
  "topic": [],
  "auditType": {}
}
```

---

## 12. Handling Deletes and Exclusions

### 12.1 Topic-Level Exclusion

If a topic is excluded:

```text
Drop the topic from the document.
Recalculate document-level audit from remaining topics.
Emit a replacement document to MongoDB.
```

### 12.2 Canonical-Level Exclusion

If a canonical record must be excluded:

```text
Emit a delete/tombstone event for that c360Id,
or emit an instruction event consumed by the MongoDB Sink Connector using a delete write model strategy.
```

Recommended control event:

```json
{
  "_id": "C360-123",
  "__operation": "delete",
  "reason": "UPSTREAM_EXCLUSION"
}
```

If delete semantics are difficult with the sink connector configuration, route delete events to a separate custom consumer that performs:

```javascript
db.preferences.deleteOne({ _id: "C360-123" })
```

---

## 13. Deployment Workflow

### Step 1: Prepare MySQL

- Confirm primary keys exist on all source tables.
- Enable MySQL binlog.
- Create a Debezium user with required replication permissions.
- Create signaling table if incremental snapshots are needed.
- Create or confirm exclusion/reference tables.

### Step 2: Deploy Kafka Connect

Install plugins:

```text
Debezium MySQL Connector
MongoDB Kafka Connector
Custom CP3 SMT JAR
Any required converters
```

Example plugin path:

```text
/opt/kafka/plugins/debezium-mysql
/opt/kafka/plugins/mongodb-kafka
/opt/kafka/plugins/cp3-custom-smt
```

Restart Kafka Connect after installing the custom SMT JAR.

### Step 3: Register Debezium MySQL Source Connector

Register `cp3-mysql-source` using the configuration shown above.

### Step 4: Validate Kafka Topics

Confirm records are arriving:

```bash
kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic mysql.cp3.preference_topic \
  --from-beginning \
  --max-messages 5
```

### Step 5: Deploy Custom SMT

Attach the custom SMT to the connector where the logic should run.

For source-side filtering:

```text
MySQL → Debezium → SMT → Kafka
```

For sink-side filtering/enrichment:

```text
Kafka → SMT → MongoDB Sink
```

Source-side filtering reduces Kafka volume. Sink-side filtering preserves raw data in Kafka. For auditability, CP3 should usually keep raw CDC topics and apply CP3 transformations downstream.

### Step 6: Deploy Aggregation Processor

Deploy Kafka Streams/Flink/custom service to create final canonical MongoDB documents.

Input topics:

```text
mysql.cp3.preferences
mysql.cp3.preference_topic
mysql.cp3.preference_property
mysql.cp3.sor_xwalk
mysql.cp3.topic_exclusion
mysql.cp3.canonical_exclusion
```

Output topic:

```text
cp3.preferences.mongo.final
```

### Step 7: Register MongoDB Sink Connector

Register `cp3-mongodb-sink`.

### Step 8: Validate MongoDB Atlas

Check:

```javascript
db.preferences.findOne({ _id: "C360-123" })
```

Validate:

- Excluded topic codes are absent.
- Excluded canonical records are absent.
- `eid` is populated.
- Audit timestamps are ISO 8601.
- Document-level audit reflects the latest remaining valid topic.
- Updates in MySQL are reflected in MongoDB.

---

## 14. Testing Scenarios

| Scenario | Expected Result |
|---|---|
| New preference inserted in MySQL | New MongoDB document created |
| Existing preference updated | MongoDB document replaced or updated |
| Topic with excluded `topicCode` inserted | Topic not included in MongoDB |
| Latest topic is excluded | Document audit timestamp uses next latest valid topic |
| `sor_xwalk` row added or updated | `eid` is added/updated in final MongoDB document |
| Canonical record added to exclusion table | MongoDB document is deleted or not written |
| Incremental snapshot triggered | Selected source rows are re-emitted and reconciled |
| MySQL delete event received | MongoDB document or nested child is removed according to delete policy |

---

## 15. Recommended Final Pattern

For CP3, the recommended production pattern is:

```text
1. Debezium captures MySQL snapshot + CDC.
2. Raw CDC events are retained in Kafka.
3. Built-in SMTs unwrap/route/rename simple fields.
4. Custom CP3 SMT filters obvious invalid records and normalizes simple fields.
5. Kafka Streams/Flink/custom processor builds canonical MongoDB documents.
6. Processor recalculates audit data after applying exclusion rules.
7. Processor emits final documents to `cp3.preferences.mongo.final`.
8. MongoDB Kafka Sink Connector upserts final documents into Atlas.
```

This provides:

- Replayability from raw CDC topics.
- Clear separation of source capture, transformation, aggregation, and persistence.
- Support for incremental loads.
- Support for child/canonical exclusion rules.
- Deterministic audit recalculation.
- A clean MongoDB Atlas target schema.

---

## 16. Operational Notes

### Observability

Track:

- Connector task status.
- Debezium lag.
- Kafka consumer lag.
- Dead letter queue records.
- MongoDB sink write errors.
- Aggregation processor state-store size.
- Count reconciliation between MySQL and MongoDB.

### Error Handling

Recommended DLQ configuration:

```json
{
  "errors.tolerance": "all",
  "errors.deadletterqueue.topic.name": "cp3.migration.dlq",
  "errors.deadletterqueue.context.headers.enable": "true",
  "errors.log.enable": "true",
  "errors.log.include.messages": "true"
}
```

### Reprocessing

Because raw CDC events are retained, CP3 can rebuild final MongoDB documents by replaying Kafka topics into a new aggregation app or output topic.

---

## 17. References

- MongoDB Kafka Connector documentation: https://www.mongodb.com/docs/kafka-connector/current/
- Kafka Connect SMT reference: https://docs.confluent.io/kafka-connectors/transforms/current/overview.html
- Debezium MySQL Connector documentation: https://debezium.io/documentation/reference/stable/connectors/mysql.html
- Debezium signaling and incremental snapshots: https://debezium.io/documentation/reference/stable/configuration/signalling.html
