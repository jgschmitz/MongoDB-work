# MongoDB Atlas Sizing — Showing the Work

## Purpose

This document turns the sizing questionnaire into a transparent sizing method that shows how the workload assumptions translate into storage, index footprint, working-set/RAM considerations, throughput, retention, backup, and the decision to begin with a replica set or evaluate sharding.

The intent is not to pretend there is one exact answer before load testing. The intent is to make the assumptions and math explicit enough that another architect can reproduce the estimate, challenge an assumption, and see how the final sizing changes.

---

## 1. Source workload assumptions

### Volume

- New transactions / primary records: **3,000,000 per day**
- Approximate monthly volume: **90,000,000 records**
- Approximate annual volume: **1.095 billion records**
- Two-year retained document count, if nothing is archived or purged: **2.19 billion records**

### Document-size bands

The workload contains multiple document types, so sizing should be expressed as a range rather than forcing every record into one average size.

| Dataset / planning case | Approx. document size | How it is used in sizing |
|---|---:|---|
| Primary transactional dataset | **2–5 KB** | High-volume stored records; primary storage-growth range |
| Aggregation / state dataset | **2–5 KB** | Upsert-based state data |
| Patient / business state | **5–10 KB** | Supporting state data |
| Active-processing state / larger test payload | **48–50 KB** | Larger document class and conservative upper-bound scenario |
| Combined workload planning case | **~240 GB/day logical** | Primary plus supporting collections using current planning assumptions |

The **2–5 KB** and **50 KB** figures are therefore not competing estimates. They describe different document classes and are intentionally retained as lower/base and upper-bound sizing cases.

### Throughput

- Average transaction rate: **3,000,000 / 86,400 = ~34.7 transactions/sec**
- Rounded questionnaire average: **~35 RPS**
- Peak target: **~1,000 RPS**
- Peak-to-average factor: **1,000 / 34.7 = ~28.8x**

### Access pattern

- High-volume inserts
- Indexed point reads / lookups
- Single-document updates and upserts
- Stateful aggregation updates
- More than **90% of reads and updates keyed by `patientId`**
- Occasional historical range and aggregation queries over as much as **12 months**
- Most real-time reads return **one document**
- Most writes modify or insert **one document**

### Latency targets

- End-to-end API read SLA: **≤ 400 ms**
- Preferred database p95 read latency: **< 20 ms**
- Preferred database p99 read latency: **< 50 ms**
- Preferred database p95 write latency: **< 20 ms**
- Preferred database p99 write latency: **< 50 ms**

---

## 2. Step 1 — Calculate logical data growth

The basic storage formula is:

```text
Logical data per day = documents per day × average document size
```

Using **3,000,000 documents/day**:

### Scenario A — 2 KB primary documents

```text
3,000,000 docs/day × 2 KB
= 6,000,000 KB/day
≈ 6 GB/day
```

```text
30-day month: 6 GB/day × 30 = 180 GB/month
12 months:    6 GB/day × 365 = 2.19 TB/year
24 months:    6 GB/day × 730 = 4.38 TB/two years
```

### Scenario B — 5 KB primary documents

```text
3,000,000 docs/day × 5 KB
= 15,000,000 KB/day
≈ 15 GB/day
```

```text
30-day month: 15 GB/day × 30 = 450 GB/month
12 months:    15 GB/day × 365 = 5.475 TB/year
24 months:    15 GB/day × 730 = 10.95 TB/two years
```

### Scenario C — 50 KB conservative upper bound

This is intentionally conservative and represents the larger payload class, not the assumption that every collection will necessarily average 50 KB.

```text
3,000,000 docs/day × 50 KB
= 150,000,000 KB/day
≈ 150 GB/day
```

```text
30-day month: 150 GB/day × 30 = 4.5 TB/month
12 months:    150 GB/day × 365 = 54.75 TB/year
24 months:    150 GB/day × 730 = 109.5 TB/two years
```

### Scenario D — combined-workload planning estimate

The questionnaire also uses approximately **240 GB/day** as a combined planning assumption for the primary transactional data plus supporting aggregation/state data.

```text
240 GB/day × 30 = 7.2 TB/month
240 GB/day × 365 = 87.6 TB/year
```

This scenario should be treated as a **capacity-planning envelope across collections**, not as the expected size of the primary transactional collection alone.

### Storage-growth summary

| Scenario | Logical/day | 30 days | 12 months | 24 months |
|---|---:|---:|---:|---:|
| 2 KB primary docs | 6 GB | 180 GB | 2.19 TB | 4.38 TB |
| 5 KB primary docs | 15 GB | 450 GB | 5.475 TB | 10.95 TB |
| 50 KB upper bound | 150 GB | 4.5 TB | 54.75 TB | 109.5 TB |
| Combined workload estimate | 240 GB | 7.2 TB | 87.6 TB | 175.2 TB |

> The final storage estimate should use the actual percentage of records in each document-size class. The range above deliberately shows what happens when those percentages are not yet known.

---

## 3. Step 2 — Add index footprint

A measured aggregation/state collection provides a useful empirical starting point:

```text
Documents:  90,000,374
Data size:  120.33 GB
Index size:  18.64 GB
```

Index-to-data ratio:

```text
18.64 GB / 120.33 GB = 0.1549
≈ 15.5%
```

For first-pass planning, we can apply **~15.5%** as an observed index ratio while recognizing that the final ratio depends on schema and index design.

Formula:

```text
Estimated indexes = logical data × 15.5%
Data + indexes    = logical data × 1.155
```

### 12-month examples

| Scenario | 12-mo logical data | Est. indexes @ 15.5% | Data + indexes |
|---|---:|---:|---:|
| 2 KB primary | 2.19 TB | ~0.34 TB | ~2.53 TB |
| 5 KB primary | 5.475 TB | ~0.85 TB | ~6.32 TB |
| 50 KB upper bound | 54.75 TB | ~8.48 TB | ~63.23 TB |
| 240 GB/day combined envelope | 87.6 TB | ~13.57 TB | ~101.17 TB |

### Important limitation

The **15.5% ratio is measured, not guaranteed**. It is valuable because it is better than inventing an index multiplier, but it should be replaced with collection-specific measurements as the final schema and query patterns become available.

Compound indexes, additional historical-query indexes, multikey indexes, index key size, field cardinality, and duplicated indexes across similar collections can all change the result.

---

## 4. Step 3 — Separate logical size from physical Atlas storage

Logical application data is not the same as the physical disk capacity that must be provisioned.

The bridge is:

```text
Physical data ≈ (logical data × compression factor)
              + physical index footprint
              + operational headroom
```

At this stage, the questionnaire does **not** provide a measured WiredTiger compression ratio for this workload. Therefore, compression should remain an explicit variable rather than being silently assumed.

Define:

```text
C = observed physical-data / logical-data compression factor
```

Then:

```text
Physical primary storage ≈ (logical data × C) + indexes + headroom
```

Example only:

```text
If C = 0.50, then 5.475 TB logical document data
would occupy roughly 2.74 TB before indexes/headroom.
```

Do not use the example 0.50 factor as the final answer. Capture the actual `dataSize`, `storageSize`, and `totalIndexSize` from representative loaded data and substitute the measured factor.

### Headroom

The cluster should not be sized so projected Month-12 data lands exactly at the storage ceiling. Preserve capacity for:

- growth forecast error
- index growth
- compaction / maintenance behavior
- temporary operational spikes
- schema changes
- delayed archival or purge jobs

For the sizing review, show both:

```text
Expected physical footprint
and
Expected physical footprint + agreed operational headroom
```

rather than hiding the headroom inside another multiplier.

---

## 5. Step 4 — Calculate retained document count

Document count matters independently of bytes because it affects index cardinality, B-tree depth, operational behavior, and the practicality of collection management.

### One year

```text
3,000,000 docs/day × 365 days
= 1,095,000,000 docs
≈ 1.095 billion documents
```

### Two years

```text
3,000,000 docs/day × 730 days
= 2,190,000,000 docs
≈ 2.19 billion documents
```

This is the primary transactional collection only. Upsert-based state collections may contain substantially fewer documents because repeated transactions can update an existing business-key record rather than always append a new one.

---

## 6. Step 5 — Estimate the working set rather than equating RAM to total data

RAM sizing should be based primarily on the **hot working set**, especially hot indexes and frequently accessed documents, rather than assuming all retained historical data must remain in memory.

The workload description indicates that most real-time traffic targets recent/active records with indexed access, while 12-month queries are occasional and non-real-time.

A useful first-pass model is:

```text
Working set ≈ hot document window
            + hot index pages
            + frequently accessed state collections
            + execution overhead
```

Using the observed **15.5% index ratio**, the primary transactional collection alone generates approximately:

| Hot window | 2 KB case, data+indexes | 5 KB case, data+indexes | 50 KB case, data+indexes |
|---|---:|---:|---:|
| 1 day | ~6.9 GB | ~17.3 GB | ~173 GB |
| 7 days | ~48.5 GB | ~121.3 GB | ~1.21 TB |
| 30 days | ~208 GB | ~520 GB | ~5.20 TB |

These numbers **do not equal the required RAM**. They are a way to expose the size of candidate hot windows. WiredTiger cache effectiveness, locality of reference, actual index-page residency, and state-collection access determine how much of that window needs to remain resident.

### Existing measured state collection

The questionnaire already includes a representative aggregation/state collection:

```text
Data:    120.33 GB
Indexes:  18.64 GB
Total:   138.97 GB
```

Because this collection participates in point lookups and stateful upserts, its active portion should be included in the RAM/working-set discussion rather than sizing RAM solely from the append-only transactional collection.

### What to measure in load testing

For the candidate Atlas tier, validate:

- WiredTiger cache utilization
- cache read-into / eviction behavior
- page faults / disk-read pressure
- index residency for high-frequency access paths
- CPU utilization at peak
- disk IOPS and latency
- query latency under mixed transactional + historical workload

The right tier is the smallest configuration that preserves the required latency and operational headroom at the **peak workload**, not the average workload.

---

## 7. Step 6 — Convert application throughput into database operations

The average input rate is straightforward:

```text
3,000,000 / 86,400
= 34.72 transactions/sec average
```

Peak target:

```text
1,000 transactions/sec
```

Burst factor:

```text
1,000 / 34.72
= 28.8x average
```

This means a cluster sized only around the daily average would materially understate the requirement.

### Transactions are not necessarily one database operation

The application flow includes inserts, reads, upserts, and state updates. Therefore:

```text
Peak DB operations/sec
= peak transactions/sec × DB operations per transaction
```

For example, if a representative transaction performs:

```text
1 insert
1 indexed lookup
1 state upsert
```

then the test workload is approximately:

```text
1,000 transactions/sec × 3 DB operations
= ~3,000 DB operations/sec
```

That **3,000 ops/sec is an example, not a stated requirement**. The final sizing model should replace `3` with the measured number of MongoDB operations generated by a representative transaction.

### Why this matters

Two systems can both claim “1,000 RPS” while placing very different load on MongoDB. The database-facing number must include:

- operations per request
- read/write mix
- document sizes
- index maintenance per write
- write concern
- query complexity
- concurrency

---

## 8. Step 7 — Account for write amplification from indexes

Every insert or update must maintain the indexes affected by that write.

A simplified sizing view is:

```text
Database write work
≈ document write
 + index entries changed by that write
```

Therefore, the 15.5% index **storage** ratio should not be interpreted as only a storage concern. Index count and design also affect CPU and disk I/O during sustained ingestion.

For this workload, indexing should be kept aligned to concrete access patterns:

- `patientId` point access
- business identifiers used by state upserts
- timestamps used for historical retrieval
- compound indexes that support the actual filter/sort pattern

Avoid sizing with a large hypothetical set of “future” indexes. Build the required index set, load representative data, and measure the resulting `totalIndexSize` and write cost.

---

## 9. Step 8 — Evaluate historical reporting separately from the real-time path

The real-time path consists primarily of indexed point operations with strict latency goals. Historical queries may scan or aggregate over up to 12 months of data and are described as occasional/user-initiated.

These are different workload classes and should be tested separately and then together.

### Test A — transactional only

Validate peak ingestion + point reads + state upserts at the required p95/p99 latency.

### Test B — historical only

Validate representative 12-month filters, ranges, sorts, and aggregations against realistic retained data volume.

### Test C — mixed workload

Run historical queries while the transactional workload is at or near peak.

If Test C causes unacceptable real-time latency, the sizing/architecture response can be one or more of:

- larger cluster tier
- better indexes/query shape
- workload isolation
- separate analytical path / nodes if later required
- data lifecycle/archival changes

This is preferable to increasing the production tier based on an unmeasured assumption that historical reporting will interfere with OLTP.

---

## 10. Step 9 — Determine whether a replica set is enough or sharding should be evaluated

Sharding should not be selected only because “the database is large.” It should be evaluated when a single replica set becomes constrained by one or more of:

- sustainable storage per node
- peak write throughput
- CPU
- RAM / working set
- disk IOPS
- operational headroom
- expected growth during the design horizon

### Lower/base range

At **2–5 KB** per primary transactional record, one year of primary data is approximately:

```text
2.19–5.475 TB logical before indexes
~2.53–6.32 TB logical including the observed 15.5% index ratio
```

This range is where a replica-set design can be evaluated first, subject to the measured compression ratio, working set, IOPS, and peak workload.

### Upper-bound range

At **50 KB** for every primary record:

```text
54.75 TB logical documents/year
~63.23 TB including indexes at the observed ratio
```

At the **240 GB/day combined-workload envelope**:

```text
87.6 TB logical/year
~101.17 TB including indexes at the observed ratio
```

Those upper envelopes strongly change the capacity discussion and justify evaluating a sharded design much earlier.

### Shard-key candidate

Because more than 90% of reads and updates are patient-centric, `patientId` is an important shard-key candidate, but the choice must also be tested for:

- cardinality
- write distribution
- concentration of activity for individual patients
- range-query behavior
- routing of timestamp-based historical queries
- whether compound or hashed strategies are more appropriate

The shard-key decision should follow the real query/write distribution, not just the most common filter field.

---

## 11. Step 10 — Multi-region HA and DR are topology requirements, not logical-data multipliers

Current requirements include:

- minimum three-node high availability
- private connectivity
- encryption in transit and at rest
- auditing
- backups / PITR
- near-zero RPO target
- recovery in minutes to less than one hour
- possible secondary Azure region for DR/business continuity

Do **not** inflate the logical application dataset by manually multiplying it by the number of replica-set members and then call that “the database size.”

Keep these concepts separate:

```text
Application logical data size
Physical storage per data-bearing node
Replica-set / multi-region topology
Backup storage
```

All four affect cost, but they are different parts of the sizing model.

The multi-region topology should be selected after the application regions, failover behavior, acceptable write latency, and exact RPO/RTO semantics are finalized.

---

## 12. Step 11 — Backup sizing

The questionnaire targets:

- backup protection from Day 1
- ~30-day snapshot/PITR planning window
- near-zero data-loss objective
- high data churn

The key sizing inputs are:

```text
Protected physical data size
Daily change rate / churn
PITR window
Snapshot retention policy
Compression / deduplication behavior of the backup service
```

The **240 GB/day** figure is useful for understanding incoming logical growth, but backup capacity should not be calculated as:

```text
primary data size × 30 full copies
```

Instead, use the Atlas backup estimator / measured backup growth once the physical dataset and actual churn rate are known.

For architecture review, keep the following two numbers separate:

```text
Month-12 logical dataset growth = ~87.6 TB under the 240 GB/day envelope
30-day PITR retention = recovery-policy requirement, not 30 complete copies of that dataset
```

---

## 13. Environment sizing

Planned environments:

| Environment | Initial relative size assumption |
|---|---:|
| Dev | ~5–10% of production |
| STG | ~25–50% of production |
| UAT | ~50–100% of production |
| Prod | 100% |

The percentage should be applied to the **workload characteristic being tested**, not blindly to every cluster dimension.

For example:

- Dev can use less retained data and lower concurrency.
- STG can use reduced retention but production-like schema/indexes.
- UAT/performance testing may need production-like peak throughput even if it does not retain a full year of data.
- Prod must satisfy both capacity and peak-latency requirements.

A 50% data-volume environment does not automatically need exactly 50% of production CPU/RAM if the test requires full peak throughput.

---

## 14. Current sizing envelope

Using only information currently available, the defensible sizing envelope is:

### Primary transactional collection, one-year retention

```text
Documents:            ~1.095 billion
Logical data:         ~2.19–5.475 TB using 2–5 KB documents
Observed-index model: ~0.34–0.85 TB
Data + indexes:       ~2.53–6.32 TB logical-equivalent planning footprint
```

### Conservative large-document envelope

```text
Documents:            ~1.095 billion
Logical data:         ~54.75 TB if all primary docs averaged 50 KB
Observed-index model: ~8.48 TB
Data + indexes:       ~63.23 TB
```

### Combined-workload capacity envelope

```text
Logical growth:       ~240 GB/day
Logical Month-12:     ~87.6 TB
Observed-index model: ~13.57 TB if the same 15.5% ratio applied
Data + indexes:       ~101.17 TB
```

The last two are intentionally conservative and should **not** replace the lower 2–5 KB primary-data model. They show the consequence if a much larger portion of the retained workload is actually in the 50 KB class or if the 240 GB/day aggregate assumption persists.

---

## 15. What determines the final Atlas tier

The final Atlas tier should be selected by satisfying all of the following at the same time:

```text
1. Physical storage at design-horizon retention
2. Hot working set / cache behavior
3. Peak CPU at ~1,000 application RPS
4. Actual DB operations generated per application request
5. Write IOPS including index maintenance
6. p95/p99 latency targets
7. Historical-query interference with the real-time path
8. Operational headroom
9. HA / DR topology
10. Growth path through the next sizing horizon
```

This is why a sizing answer should not be reduced to:

```text
X TB = Atlas tier Y
```

Storage may set a floor, but peak throughput, working set, IOPS, and latency can require a larger tier even when the data fits on disk.

---

## 16. Recommended validation sequence

### Phase 1 — resolve the data mix

Measure or estimate the percentage of daily documents in each size band:

```text
% at 2–5 KB
% at 5–10 KB
% at ~50 KB
```

Then calculate weighted daily growth:

```text
Daily logical growth
= Σ (documents/day in class × avg size of class)
```

This replaces the broad scenario range with a realistic expected case.

### Phase 2 — load representative retained data

Capture:

```text
db.collection.stats().dataSize
db.collection.stats().storageSize
db.collection.stats().totalIndexSize
```

Use those measurements to replace the assumed compression factor and the generalized 15.5% index ratio.

### Phase 3 — replay the database-facing transaction pattern

Measure the true number of database operations generated by each application transaction and the actual read/write mix.

### Phase 4 — test at peak, not average

Target at least the stated **~1,000 RPS peak**, with realistic document sizes and indexes.

### Phase 5 — introduce historical workload

Add representative 12-month queries while the transactional workload runs and observe impact on p95/p99 latency, CPU, cache, and disk.

### Phase 6 — choose topology

If the selected replica-set tier satisfies storage, cache, IOPS, throughput, latency, and headroom for the design horizon, sharding is not required merely for HA.

If a single replica set cannot satisfy those constraints economically or operationally, evaluate sharding and validate the shard key against real access distribution.

---

## 17. One-page sizing calculation

The sizing logic can be summarized as:

```text
INPUTS
------
3,000,000 transactions/day
2–5 KB primary docs
5–10 KB supporting state docs
~50 KB large active-processing docs
1–2 year retention
~15.5% observed index/data ratio
~1,000 RPS peak
~35 RPS average
12-month occasional historical queries
p95 DB latency target <20 ms
p99 DB latency target <50 ms

DATA
----
Primary data/day @ 2–5 KB
= 6–15 GB/day

Primary data/year
= 2.19–5.475 TB/year

Primary docs/year
= 1.095B

Observed index estimate
= data × 15.5%
= ~0.34–0.85 TB at year 1

Primary data + indexes
= ~2.53–6.32 TB at year 1

PEAK LOAD
---------
Average = 3,000,000 / 86,400
        = ~34.7 tx/sec

Peak    = ~1,000 tx/sec
Burst   = ~28.8x average

Peak DB ops/sec
= 1,000 × actual MongoDB operations per transaction

RAM / WORKING SET
-----------------
Size from hot documents + hot index pages + active state collections,
not from the full retained historical dataset.

PHYSICAL STORAGE
----------------
= logical documents × measured compression factor
+ physical indexes
+ operational headroom

FINAL TIER
----------
Choose the smallest tested Atlas configuration that satisfies:
storage + RAM/cache + CPU + IOPS + peak throughput + p95/p99 SLA + headroom.

SHARDING
--------
Evaluate when a single replica set cannot satisfy those constraints
for the required growth horizon; do not shard solely for HA.
```

---

## 18. Inputs still needed to collapse the range into a final production size

The current questionnaire is sufficient to build a sizing envelope. The following measurements will turn it into a much tighter production recommendation:

1. Percentage of retained records in each document-size class.
2. Actual physical compression ratio from representative MongoDB data.
3. Final retention period by collection, not only at application level.
4. Actual DB operations per application transaction.
5. Read/write ratio at peak.
6. Final index definitions and measured index footprint by collection.
7. Definition of the real-time hot-data window: hours, days, or active business state.
8. Peak concurrency in addition to RPS.
9. Representative 12-month historical query shapes and frequency.
10. Azure application regions and final RPO/RTO/failover requirements.

Once those are measured, the scenario table can be reduced from a broad envelope to an **expected case + peak case + growth headroom**, which is the appropriate basis for the final Atlas cluster recommendation.

---

## Bottom line

Based on the data currently supplied, the sizing should be communicated as a **range driven by different document classes**, not as a single contradictory document-size assumption.

The primary high-volume transactional data produces a one-year logical range of approximately **2.19–5.475 TB**, or approximately **2.53–6.32 TB including indexes using the observed 15.5% ratio**. The **50 KB** and **240 GB/day** calculations are useful conservative envelopes that show how the architecture changes if larger document classes dominate the retained dataset.

The final Atlas tier is then chosen by testing that storage envelope against the second half of the sizing problem: **working set, peak ~1,000 RPS, database operations per request, write/index IOPS, p95/p99 latency, historical-query interference, and operational headroom**.
