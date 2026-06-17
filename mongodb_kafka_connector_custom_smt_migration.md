# CP3 Streaming Migration Pattern: MongoDB Kafka Connector with SMTs and Custom Logic

## Purpose

This document shows how CP3 can implement a streaming migration from MySQL to MongoDB Atlas using Kafka Connect, the MongoDB Kafka Sink Connector, built-in Single Message Transforms (SMTs), and a custom SMT for CP3-specific rules.

The customization covers:

- Incremental data load from MySQL.
- Topic-level filtering using a predefined `topicCode` skip list.
- Exclusion of canonical records when business rules require parent records to be dropped.
- Renaming source fields to target MongoDB field names.
- Deriving `EID` from the `sor_xwalk` table.
- Converting audit timestamps to ISO 8601.
- Recalculating document-level audit fields after skipped child/topic records are removed.

---

## Recommended Architecture

```text
MySQL
  |
  |  Debezium MySQL Source Connector
  v
Kafka topics
  |
  |  Kafka Connect SMT chain
  |  - built-in SMTs for simple field cleanup
  |  - custom CP3 SMT for business rules
  v
MongoDB Kafka Sink Connector
  |
  v
MongoDB Atlas collections
```

The key design decision is to avoid treating the migration as a simple table copy. The MongoDB document should be assembled only after filtering, enrichment, and audit recalculation rules have been applied.

---

## When SMTs Are Appropriate

SMTs are useful when the transformation can be applied one record at a time as the record moves through Kafka Connect.

Good SMT candidates:

- Rename fields.
- Drop fields.
- Convert simple values.
- Route topics.
- Filter individual records.
- Apply deterministic business rules using values already present in the Kafka record.

Use Kafka Streams, Flink, Spark, or a custom stream processor instead when the logic requires heavy joins, stateful aggregation, long-running lookups, or complex parent-child assembly across many messages.

For CP3, a practical pattern is:

- Use Debezium to capture MySQL table changes.
- Ensure the Kafka event contains the data needed by the custom SMT.
- Use the custom SMT to apply CP3-specific filtering and shaping.
- Use the MongoDB Sink Connector to upsert into Atlas.

---

## Source Data Assumptions

Example source tables:

```text
preferences
- c360Id
- topicCode
- topicAuditDateTime
- systemModifiedDateTime
- propertyCode
- propertyOption
- additional preference fields

sor_xwalk
- c360Id
- eid
```

Target MongoDB collection:

```text
preferences
```

Target document shape, simplified:

```json
{
  "c360Id": "C360123",
  "eid": "EID456",
  "topic": [
    {
      "topicCode": "A",
      "topicAuditType": {
        "topicAuditDateTime": "2026-05-11T14:15:19Z",
        "systemModifiedDateTime": "2026-05-11T14:15:19Z"
      },
      "property": []
    }
  ],
  "auditType": {
    "auditDateTime": "2026-05-11T14:15:19Z",
    "systemModifiedDateTime": "2026-05-11T14:15:19Z"
  }
}
```

---

## Important Constraint: Enrichment from `sor_xwalk`

An SMT should not make remote database calls for every record. That can slow down Kafka Connect, create failure coupling, and make replay behavior unpredictable.

Preferred options for deriving `EID`:

### Option A: Add `EID` before the SMT

Create a source-side view or query that joins `preferences` with `sor_xwalk` before records are published to Kafka.

```sql
SELECT
  p.c360Id,
  x.eid,
  p.topicCode,
  p.topicAuditDateTime,
  p.systemModifiedDateTime,
  p.propertyCode,
  p.propertyOption
FROM preferences p
LEFT JOIN sor_xwalk x
  ON p.c360Id = x.c360Id;
```

Then the custom SMT can simply copy `eid` into the MongoDB document.

### Option B: Use a compacted lookup topic

Publish `sor_xwalk` into a compacted Kafka topic keyed by `c360Id`. Then use Kafka Streams or another stream-processing layer to enrich `preferences` events before they reach the MongoDB Sink Connector.

### Option C: Maintain a local in-memory map in a custom SMT

This is usually not recommended unless the mapping is small, static, and loaded from connector configuration or a local file. It should not be the default design for CP3 unless the mapping is truly stable.

---

## Connector Flow

```text
1. Debezium captures MySQL changes.
2. Events are published to Kafka topics.
3. Built-in SMTs perform simple changes such as unwrap, rename, or drop fields.
4. CP3 custom SMT applies migration business rules.
5. MongoDB Sink Connector writes valid transformed records to MongoDB Atlas.
```

---

## Example Debezium MySQL Source Connector

```json
{
  "name": "cp3-mysql-source",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "database.hostname": "mysql-host",
    "database.port": "3306",
    "database.user": "${file:/opt/connect/secrets.properties:mysql_user}",
    "database.password": "${file:/opt/connect/secrets.properties:mysql_password}",
    "database.server.id": "184054",
    "topic.prefix": "cp3.mysql",
    "database.include.list": "cp3",
    "table.include.list": "cp3.preferences,cp3.sor_xwalk",
    "schema.history.internal.kafka.bootstrap.servers": "kafka:9092",
    "schema.history.internal.kafka.topic": "schemahistory.cp3",
    "include.schema.changes": "false"
  }
}
```

Notes:

- The source connector captures incremental changes from MySQL.
- Initial snapshot behavior should be configured based on cutover strategy.
- If `EID` is required in the same event, prefer a source-side view or an enrichment topic/process before the MongoDB sink.

---

## Example MongoDB Sink Connector with SMT Chain

```json
{
  "name": "cp3-preferences-mongodb-sink",
  "config": {
    "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
    "topics": "cp3.mysql.cp3.preferences.enriched",
    "connection.uri": "${file:/opt/connect/secrets.properties:mongodb_uri}",
    "database": "cp3",
    "collection": "preferences",

    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter.schemas.enable": "false",

    "writemodel.strategy": "com.mongodb.kafka.connect.sink.writemodel.strategy.ReplaceOneBusinessKeyStrategy",
    "document.id.strategy": "com.mongodb.kafka.connect.sink.processor.id.strategy.PartialValueStrategy",
    "document.id.strategy.partial.value.projection.type": "AllowList",
    "document.id.strategy.partial.value.projection.list": "c360Id",
    "delete.on.null.values": "true",

    "transforms": "unwrap,cp3Rules",

    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
    "transforms.unwrap.drop.tombstones": "false",
    "transforms.unwrap.delete.handling.mode": "rewrite",

    "transforms.cp3Rules.type": "com.cp3.kafka.transforms.Cp3PreferenceTransform$Value",
    "transforms.cp3Rules.excluded.topic.codes": "E,DNC,LEGACY_SKIP",
    "transforms.cp3Rules.drop.canonical.when.no.valid.topics": "true",
    "transforms.cp3Rules.timestamp.fields": "topicAuditDateTime,systemModifiedDateTime,auditDateTime",
    "transforms.cp3Rules.audit.output.timezone": "UTC"
  }
}
```

Notes:

- `unwrap` removes the Debezium envelope and exposes the latest row value.
- `cp3Rules` is the custom SMT that applies CP3 migration rules.
- `delete.on.null.values=true` allows the SMT to intentionally return a tombstone/null value when a canonical record should be excluded.
- Exact MongoDB Sink Connector write strategy should be validated against CP3's desired upsert semantics.

---

## Custom SMT Responsibilities

The CP3 custom SMT should perform these operations in order:

```text
Input Kafka record
  |
  v
1. Read source value
2. Validate required fields
3. Drop excluded topicCode values
4. Drop canonical record if all topics are excluded or if parent exclusion rule applies
5. Rename fields to target MongoDB names
6. Convert timestamp fields to ISO 8601
7. Add derived fields already present in the event, such as eid
8. Recalculate document-level audit from remaining valid topics
9. Return transformed record to MongoDB Sink Connector
```

---

## Example Transformation Logic

### Business Rule 1: Exclude skipped topics

```text
If topic.topicCode is in excluded.topic.codes, remove it from the outgoing MongoDB document.
```

### Business Rule 2: Recalculate document-level audit

```text
After skipped topics are removed:
- Sort remaining topics by topicAuditType.topicAuditDateTime.
- Pick the latest valid timestamp.
- Use that topic's audit fields to populate auditType at the document level.
```

### Business Rule 3: Exclude canonical records

```text
If no valid topics remain, or if upstream exclusion rules say the parent/canonical record must be excluded:
- Return null/tombstone from the SMT, or route the record to a dead-letter / skipped topic depending on the desired auditability.
```

---

## Example Custom SMT Java Skeleton

```java
package com.cp3.kafka.transforms;

import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.connect.connector.ConnectRecord;
import org.apache.kafka.connect.transforms.Transformation;
import org.apache.kafka.connect.data.Struct;
import org.apache.kafka.connect.errors.DataException;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class Cp3PreferenceTransform<R extends ConnectRecord<R>> implements Transformation<R> {

    public static class Value<R extends ConnectRecord<R>> extends Cp3PreferenceTransform<R> {}

    private Set<String> excludedTopicCodes;
    private boolean dropCanonicalWhenNoValidTopics;

    @Override
    public void configure(Map<String, ?> props) {
        String excluded = String.valueOf(props.getOrDefault("excluded.topic.codes", ""));
        this.excludedTopicCodes = new HashSet<>();
        for (String code : excluded.split(",")) {
            if (!code.trim().isEmpty()) {
                this.excludedTopicCodes.add(code.trim());
            }
        }

        this.dropCanonicalWhenNoValidTopics = Boolean.parseBoolean(
            String.valueOf(props.getOrDefault("drop.canonical.when.no.valid.topics", "true"))
        );
    }

    @Override
    public R apply(R record) {
        if (record == null || record.value() == null) {
            return record;
        }

        Object value = record.value();

        if (!(value instanceof Map)) {
            throw new DataException("Cp3PreferenceTransform expects schemaless JSON Map values");
        }

        Map<String, Object> source = new LinkedHashMap<>((Map<String, Object>) value);

        String c360Id = asString(source.get("c360Id"));
        String eid = asString(source.get("eid"));
        String topicCode = asString(source.get("topicCode"));

        if (c360Id == null || c360Id.isBlank()) {
            throw new DataException("Missing required c360Id");
        }

        if (topicCode != null && excludedTopicCodes.contains(topicCode)) {
            // Returning null can be interpreted by the sink as a tombstone/delete
            // depending on connector configuration.
            if (dropCanonicalWhenNoValidTopics) {
                return record.newRecord(
                    record.topic(),
                    record.kafkaPartition(),
                    record.keySchema(),
                    record.key(),
                    null,
                    null,
                    record.timestamp()
                );
            }
        }

        Map<String, Object> topicAuditType = new LinkedHashMap<>();
        topicAuditType.put("topicAuditDateTime", toIso8601(source.get("topicAuditDateTime")));
        topicAuditType.put("systemModifiedDateTime", toIso8601(source.get("systemModifiedDateTime")));

        Map<String, Object> topic = new LinkedHashMap<>();
        topic.put("topicCode", topicCode);
        topic.put("topicAuditType", topicAuditType);
        topic.put("topicDescription", source.get("topicDescription"));
        topic.put("property", buildPropertyArray(source));

        Map<String, Object> auditType = new LinkedHashMap<>();
        auditType.put("auditDateTime", topicAuditType.get("topicAuditDateTime"));
        auditType.put("systemModifiedDateTime", topicAuditType.get("systemModifiedDateTime"));
        auditType.put("auditSourceId", source.get("auditSourceId"));
        auditType.put("applicationId", source.get("applicationId"));

        Map<String, Object> target = new LinkedHashMap<>();
        target.put("c360Id", c360Id);
        target.put("eid", eid);
        target.put("topic", List.of(topic));
        target.put("auditType", auditType);
        target.put("sourceSystemCode", source.getOrDefault("sourceSystemCode", "C360"));

        return record.newRecord(
            record.topic(),
            record.kafkaPartition(),
            record.keySchema(),
            record.key(),
            null,
            target,
            record.timestamp()
        );
    }

    private List<Map<String, Object>> buildPropertyArray(Map<String, Object> source) {
        Map<String, Object> property = new LinkedHashMap<>();
        property.put("propertyCode", source.get("propertyCode"));
        property.put("propertyDescription", source.get("propertyDescription"));

        Map<String, Object> option = new LinkedHashMap<>();
        option.put("optionCode", source.get("optionCode"));
        option.put("optionValue", source.get("optionValue"));

        property.put("propertyOption", List.of(option));
        return List.of(property);
    }

    private String toIso8601(Object value) {
        if (value == null) {
            return null;
        }

        String raw = String.valueOf(value).trim();
        if (raw.isEmpty()) {
            return null;
        }

        try {
            // Handles strings already in ISO-8601 format.
            return Instant.parse(raw).toString();
        } catch (Exception ignored) {
            // Continue to fallback parsing.
        }

        try {
            // Example fallback for values like 2026-05-11T14:15:19 without zone.
            return OffsetDateTime.parse(raw + "Z").withOffsetSameInstant(ZoneOffset.UTC)
                .format(DateTimeFormatter.ISO_INSTANT);
        } catch (Exception e) {
            throw new DataException("Unable to convert timestamp to ISO-8601: " + raw, e);
        }
    }

    private String asString(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    @Override
    public ConfigDef config() {
        return new ConfigDef()
            .define(
                "excluded.topic.codes",
                ConfigDef.Type.STRING,
                "",
                ConfigDef.Importance.HIGH,
                "Comma-separated topicCode values to exclude"
            )
            .define(
                "drop.canonical.when.no.valid.topics",
                ConfigDef.Type.BOOLEAN,
                true,
                ConfigDef.Importance.HIGH,
                "Whether to drop the canonical MongoDB document when no valid topics remain"
            );
    }

    @Override
    public void close() {
        // Nothing to close.
    }
}
```

---

## Important Note About Multi-Topic Documents

If each Kafka message contains only one topic row, the SMT cannot reliably recalculate the document-level audit across all remaining topics because SMTs process one record at a time.

For full document-level recalculation, CP3 should use one of these patterns:

### Pattern 1: Pre-assemble the full canonical document before the sink

Use Kafka Streams, Flink, Spark, or an ETL service to group all topics by `c360Id`, remove excluded topics, recalculate audit fields, and publish one complete document to the sink topic.

```text
preferences row events
  + sor_xwalk lookup events
  -> stream processor grouped by c360Id
  -> complete canonical MongoDB document topic
  -> MongoDB Sink Connector
```

This is the preferred pattern if CP3 needs document-level correctness across multiple child/topic records.

### Pattern 2: Use sink-side partial updates

Send topic-level updates to MongoDB and use update pipelines or custom write strategies to maintain the document. This is more complex and should be used only when CP3 has strong streaming update requirements.

### Pattern 3: Batch migration for initial load, streaming for CDC

Use a batch job to build the initial canonical documents correctly, then use Kafka Connect CDC for incremental changes after cutover.

This is often the safest approach for migrations with parent-child exclusions and audit recalculation.

---

## Recommended CP3 Implementation Pattern

For CP3, the safest streaming design is:

```text
Debezium MySQL Source
  -> Kafka raw CDC topics
  -> Kafka Streams enrichment and document assembly
  -> Kafka topic containing final MongoDB canonical documents
  -> MongoDB Kafka Sink Connector
  -> MongoDB Atlas
```

The custom SMT can still be used for final lightweight checks, field cleanup, timestamp normalization, or defensive filtering, but the heavy business logic should be handled before the MongoDB Sink Connector if it depends on multiple rows.

---

## Example Final Document Topic Event

The final topic consumed by the MongoDB Sink Connector should already look like the MongoDB document CP3 wants to store:

```json
{
  "c360Id": "C360123",
  "eid": "EID456",
  "topic": [
    {
      "topicCode": "A",
      "topicAuditType": {
        "topicAuditDateTime": "2026-05-11T14:15:19Z",
        "systemModifiedDateTime": "2026-05-11T14:15:19Z"
      },
      "property": [
        {
          "propertyCode": "EMAIL_OPT_IN",
          "propertyOption": [
            {
              "optionCode": "Y",
              "optionValue": "true"
            }
          ]
        }
      ]
    },
    {
      "topicCode": "B",
      "topicAuditType": {
        "topicAuditDateTime": "2026-05-10T18:06:09Z",
        "systemModifiedDateTime": "2026-05-10T18:06:09Z"
      },
      "property": []
    }
  ],
  "auditType": {
    "auditDateTime": "2026-05-11T14:15:19Z",
    "systemModifiedDateTime": "2026-05-11T14:15:19Z"
  },
  "sourceSystemCode": "C360"
}
```

---

## Testing Checklist

Test the following cases before production cutover:

- A record with a valid `topicCode` is written to MongoDB.
- A record with an excluded `topicCode` is skipped.
- A canonical record with all topics excluded is not migrated.
- A canonical record with mixed valid and skipped topics keeps only valid topics.
- Document-level audit uses the latest valid remaining topic.
- `topicAuditDateTime` and `systemModifiedDateTime` are ISO 8601 strings.
- `EID` is populated from `sor_xwalk` enrichment.
- Missing `EID` behavior is explicitly defined.
- Deletes from MySQL produce the desired MongoDB behavior.
- Replayed Kafka events produce the same MongoDB documents.
- Dead-letter queue captures malformed records.

---

## Operational Recommendations

- Keep the custom SMT stateless.
- Avoid external database calls inside the SMT.
- Use DLQ settings for invalid records.
- Version the custom SMT JAR.
- Add unit tests for every exclusion and audit scenario.
- Run a reconciliation job comparing source counts, skipped counts, and MongoDB counts.
- Log skipped record reasons to a separate audit topic if compliance or traceability is required.
- Use idempotent upserts keyed by `c360Id` or the agreed canonical business key.

---

## Deployment Steps

```text
1. Build the custom SMT JAR.
2. Copy the JAR to the Kafka Connect plugin path.
3. Restart Kafka Connect workers so the plugin is discovered.
4. Register the Debezium MySQL Source Connector.
5. Register the enrichment/document assembly stream if required.
6. Register the MongoDB Sink Connector.
7. Validate records in MongoDB Atlas.
8. Run reconciliation and exception reporting.
9. Enable production CDC after sign-off.
```

Example build command:

```bash
mvn clean package
```

Example plugin installation:

```bash
mkdir -p /opt/kafka-connect/plugins/cp3-custom-smts
cp target/cp3-custom-smts-1.0.0.jar /opt/kafka-connect/plugins/cp3-custom-smts/
```

---

## Summary Recommendation

Use the MongoDB Kafka Connector with SMTs for lightweight per-record transformations, filtering, and final cleanup. For CP3's parent-child exclusion rules, `EID` enrichment, and document-level audit recalculation across multiple topics, use a Kafka Streams or ETL enrichment stage before the MongoDB Sink Connector. The final sink topic should contain canonical MongoDB-ready documents so MongoDB Atlas receives clean, idempotent upserts.
