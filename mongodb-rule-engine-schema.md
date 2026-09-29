# MongoDB Rules Engine Schema

Corrected document examples, concise design notes, and recommended indexes.

## Design at a glance

| Area | Recommendation |
| --- | --- |
| Rule names | Reserve each unique name in `rule_identities`. |
| Version history | One document per version, in the same collection. |
| Dependencies | Reference exact rule, group, and screen versions. |
| Execution | Embed the resolved tree in an immutable snapshot. |
| Deployment | Publish one snapshot per strategy and environment. |
| Audit | Store workflow events separately from rule content. |

Each JSON block represents one document. `$oid`, `$date`, and `$numberDecimal` are MongoDB Extended JSON representations of BSON types; use an Extended JSON-aware parser when importing. Business dates such as `2020-01-01` remain date-only strings, converted by the evaluator.

Examples assume unsharded collections, one namespace, and case-sensitive rule names. Multi-tenancy or sharding requires an index and key review.

## 1. Rule identities · `rule_identities`

Reserves a stable, unique rule name across all versions.

```json
{
  "_id": {"$oid": "000000000000000000000006"},
  "ruleId": "R001",
  "ruleName": "R_BUY_Walmart_1_Brand_202603_DySupp_1_83",
  "createdAt": {"$date": "2026-07-15T11:33:24.377Z"},
  "createdBy": "jane.doe"
}
```

Both `ruleId` and `ruleName` are unique. Each version must match this registry; the application enforces that relationship. Create the identity and first version together in a transaction. Keep names reserved after archival; handle renames explicitly.

## 2. Rules · `rules`

Stores conditions, rule-local constants, and output assignments for one version.

```json
{
  "_id": {"$oid": "000000000000000000000001"},
  "ruleId": "R001",
  "ruleName": "R_BUY_Walmart_1_Brand_202603_DySupp_1_83",
  "ruleDescription": "R_BUY_Walmart_1_Brand_202603_DySupp_1_83",
  "screenCode": "SCREEN_DEFAULT",
  "version": 1,
  "status": "APPROVED",
  "conditions": [
    {
      "type": "GROUP",
      "operator": "AND",
      "conditions": [
        {
          "type": "CONDITION",
          "parameter": "dateOfService",
          "dataType": "DATE",
          "operator": "GREATER_THAN_OR_EQUAL",
          "value": "2020-01-01",
          "valueType": "LITERAL"
        },
        {
          "type": "CONDITION",
          "label": "Exactly one usable reference price",
          "dataType": "BOOLEAN",
          "valueType": "EXPRESSION",
          "value": "if drug_prices = null then false else if count(drug_prices[ndc = (if repackagedFlag = \"Y\" and #useOriginatorNdc = \"Y\" then originatorNDC else requestNDC)]) != 1 then false else if drug_prices[ndc = (if repackagedFlag = \"Y\" and #useOriginatorNdc = \"Y\" then originatorNDC else requestNDC)][1].prices = null then false else if count(drug_prices[ndc = (if repackagedFlag = \"Y\" and #useOriginatorNdc = \"Y\" then originatorNDC else requestNDC)][1].prices[source = #referencePriceSource]) != 1 then false else drug_prices[ndc = (if repackagedFlag = \"Y\" and #useOriginatorNdc = \"Y\" then originatorNDC else requestNDC)][1].prices[source = #referencePriceSource][1].unitprice != null and quantity != null"
        }
      ]
    }
  ],
  "derivedParameters": [
    {
      "name": "adjustmentFactor",
      "dataType": "NUMBER",
      "value": {"$numberDecimal": "1.1"}
    },
    {"name": "referencePriceSource", "dataType": "STRING", "value": "Medispan-AWP"},
    {"name": "useOriginatorNdc", "dataType": "STRING", "value": "Y"}
  ],
  "outputParameters": [
    {
      "parameter": "pricingMethodology",
      "dataType": "NUMBER",
      "valueType": "EXPRESSION",
      "value": "(drug_prices[ndc = (if repackagedFlag = \"Y\" and #useOriginatorNdc = \"Y\" then originatorNDC else requestNDC)][1].prices[source = #referencePriceSource][1].unitprice * quantity) * (1 - (#adjustmentFactor * 0.01))"
    },
    {
      "parameter": "dispenseFee",
      "dataType": "NUMBER",
      "valueType": "LITERAL",
      "value": {"$numberDecimal": "10.00"}
    }
  ],
  "createdAt": {"$date": "2026-07-15T11:33:24.377Z"},
  "updatedAt": {"$date": "2026-07-16T09:48:59.052Z"},
  "createdBy": "jane.doe",
  "updatedBy": "jane.doe",
  "screenVersion": 1,
  "expressionLanguage": "FEEL"
}
```

### Field behavior

| Field | Behavior |
| --- | --- |
| `conditions` | Nonempty trees; top-level entries combine with AND. Nested groups support AND/OR. |
| Literal condition | Compare the `parameter` fact path using `operator` and `value`. |
| Expression condition | Evaluate `value` as a boolean; `label` is display-only. |
| `derivedParameters` | Unique `name` values; independent literal constants. |
| `outputParameters` | Unique parameter names; evaluate in array order. |
| `screenCode` + `screenVersion` | Identify the exact screen contract. |

Compile `#name` tokens with a parser and type-aware escaping. Reject undefined constants; leave quoted text untouched. Outputs use an isolated candidate context and may depend only on earlier outputs. Apply only the winning candidate's outputs.

The price guard requires exactly one matching drug and source price. Validate list shapes and numeric inputs first; preserve NDCs as strings. Confirm the proposed `useOriginatorNdc = "Y"` setting. The existing formula applies a 1.1% reduction. Keep decimal arithmetic throughout and define rounding explicitly.

### Literal operators

| Operators | Value requirement |
| --- | --- |
| `EQUALS`, `NOT_EQUALS` | Compatible scalar value |
| `GREATER_THAN`, `LESS_THAN`, `GREATER_THAN_OR_EQUAL`, `LESS_THAN_OR_EQUAL` | Comparable value |
| `IN`, `NOT_IN` | List of values matching the operand type |
| `BETWEEN` | Two ordered, inclusive bounds |
| `CONTAINS`, `STARTS_WITH`, `REGEX` | Type-compatible value; define regex dialect |
| `IS_NULL`, `IS_NOT_NULL` | Omit `value` |

Missing/null values satisfy IS_NULL; other comparisons on missing/null are nonmatches. Supported types are STRING, NUMBER, BOOLEAN, DATE, and LIST; define LIST element types. Reject unknown operators and invalid casts.

## 3. Rule groups · `rule_groups`

Combines version-pinned rules or nested groups in an explicit order.

```json
{
  "_id": {"$oid": "000000000000000000000002"},
  "groupId": "G000001",
  "groupName": "Test12",
  "groupDescription": "test1112",
  "screenCode": "SCREEN_DEFAULT",
  "version": 1,
  "type": "RULE_GROUP",
  "status": "APPROVED",
  "hitPolicy": "FIRST",
  "items": [{"type": "RULE", "ref": "R001", "refVersion": 1, "order": 1}],
  "createdAt": {"$date": "2026-07-15T18:08:58.571Z"},
  "updatedAt": {"$date": "2026-07-15T18:08:58.577Z"},
  "createdBy": "jane.doe",
  "updatedBy": "jane.doe",
  "screenVersion": 1
}
```

Items use `type: "RULE"` or `"GROUP"`, a matching `ref` and `refVersion`, and a positive sibling-unique `order`. Sort by order. Reject missing targets, screen/version mismatches, cycles, and excessive depth or size. Reuse in separate branches is allowed.

| Hit policy | Result |
| --- | --- |
| `FIRST` | First matching child in order |
| `COLLECT_MIN` | Complete child result with the lowest comparable value |
| `COLLECT_MAX` | Complete child result with the highest comparable value |

Ties select the first child in order. Nested groups return their selected result to the parent. No matching child returns NO_MATCH, never a fabricated zero price.

## 4. Strategies · `strategies`

Defines an ordered set of group versions and the strategy hit policy.

```json
{
  "_id": {"$oid": "000000000000000000000003"},
  "strategyId": "S000001",
  "strategyName": "STR_BUY_NYSIF_Network_1",
  "strategyDescription": "STR_BUY_NYSIF_Network_1",
  "screenCode": "SCREEN_DEFAULT",
  "version": 1,
  "hitPolicy": "COLLECT_MIN",
  "status": "APPROVED",
  "ruleGroups": [{"groupId": "G000001", "groupVersion": 1, "order": 1}],
  "createdAt": {"$date": "2026-07-15T18:28:04.834Z"},
  "updatedAt": {"$date": "2026-07-15T18:28:11.561Z"},
  "createdBy": "jane.doe",
  "updatedBy": "jane.doe",
  "screenVersion": 1
}
```

Pin each `groupId` to a `groupVersion`; require positive, unique sibling orders. Every transitive dependency must share `screenCode` and `screenVersion`. Approval and runtime publication are separate.

## 5. Parameters · `parameters`

Defines authoring metadata and allowed roles for a parameter.

```json
{
  "_id": {"$oid": "000000000000000000000004"},
  "parameterCode": "P0001",
  "parameterName": "pricingMethodology",
  "displayName": "Pricing Methodology",
  "description": "Calculated price before dispense fee.",
  "parameterType": ["OUTPUT"],
  "dataType": "NUMBER",
  "uiFieldType": "NUMBER",
  "status": "ACTIVE",
  "createdAt": {"$date": "2026-07-14T20:13:19.090Z"},
  "createdBy": "jane.doe",
  "updatedAt": {"$date": "2026-07-14T20:13:19.090Z"},
  "updatedBy": "jane.doe"
}
```

`parameterCode` and `parameterName` are unique. Roles are INPUT, OUTPUT, and DERIVED; duplicates are not allowed. Freeze names, types, and roles once referenced by approved content; use new identifiers for incompatible changes.

This is one catalog example. Create the remaining entries before validating the complete rule:

| Parameter | Role | Type |
| --- | --- | --- |
| `pricingMethodology` | OUTPUT | NUMBER; P0001 above |
| `dispenseFee` | OUTPUT | NUMBER |
| `dateOfService` | INPUT | DATE |
| `drug_prices` | INPUT | LIST of structured records |
| `repackagedFlag` | INPUT | STRING |
| `originatorNDC` | INPUT | STRING |
| `requestNDC` | INPUT | STRING |
| `quantity` | INPUT | NUMBER |
| `adjustmentFactor` | DERIVED | NUMBER |
| `referencePriceSource` | DERIVED | STRING |
| `useOriginatorNdc` | DERIVED | STRING |

Define `ndc`, `prices`, `source`, and `unitprice` in the structured input contract. Optional defaults require an explicit `valueType`; `defaultOperator` applies only to INPUT roles. Derived values remain rule-local literals. Use ordered `{ "value": "code", "label": "Label" }` objects for dropdown choices.

## 6. Screens · `customscreens`

Defines the versioned authoring layout and comparable output formula.

```json
{
  "_id": {"$oid": "000000000000000000000005"},
  "screenCode": "SCREEN_DEFAULT",
  "screenName": "Smart Pricing Screen",
  "description": "Default screen used by Rule creation.",
  "version": 1,
  "status": "APPROVED",
  "sections": [
    {
      "sectionId": "SEC_EXECUTION",
      "name": "Execution Parameters",
      "layoutColumns": 2,
      "displayOrder": 1,
      "parameters": [{"parameterCode": "P0001", "mandatory": true}]
    }
  ],
  "aggregationOutput": {
    "name": "price",
    "dataType": "NUMBER",
    "valueType": "EXPRESSION",
    "value": "pricingMethodology + dispenseFee"
  },
  "createdAt": {"$date": "2026-07-14T20:13:19.090Z"},
  "createdBy": "jane.doe",
  "updatedAt": {"$date": "2026-07-14T20:13:19.090Z"},
  "updatedBy": "jane.doe"
}
```

`screenCode` + `version` identifies the screen. Section fields reference catalog codes; not every input must be shown in the UI.

Evaluate `aggregationOutput` in each candidate's output context. Every matching rule must supply `pricingMethodology` and `dispenseFee`. Missing or nonnumeric aggregates are errors. Optional UI-only `referredParameters` must have valid targets, no self-references or cycles, and stay out of snapshots.

## 7. Runtime snapshots · `strategy_snapshots`

Embeds the complete approved tree, with constants compiled into expressions.

```json
{
  "_id": {"$oid": "000000000000000000000007"},
  "strategyId": "S000001",
  "strategyVersion": 1,
  "snapshotVersion": 1,
  "screenCode": "SCREEN_DEFAULT",
  "screenVersion": 1,
  "compiledAt": {"$date": "2026-07-20T10:00:00Z"},
  "compiledBy": "rahul",
  "compilerVersion": "rules-compiler-1.0.0",
  "expressionLanguage": "FEEL",
  "hitPolicy": "COLLECT_MIN",
  "aggregationOutput": {
    "name": "price",
    "dataType": "NUMBER",
    "valueType": "EXPRESSION",
    "value": "pricingMethodology + dispenseFee"
  },
  "groups": [
    {
      "type": "GROUP",
      "groupId": "G000001",
      "version": 1,
      "order": 1,
      "hitPolicy": "FIRST",
      "items": [
        {
          "ruleId": "R001",
          "ruleName": "R_BUY_Walmart_1_Brand_202603_DySupp_1_83",
          "ruleDescription": "R_BUY_Walmart_1_Brand_202603_DySupp_1_83",
          "version": 1,
          "conditions": [
            {
              "type": "GROUP",
              "operator": "AND",
              "conditions": [
                {
                  "type": "CONDITION",
                  "parameter": "dateOfService",
                  "dataType": "DATE",
                  "operator": "GREATER_THAN_OR_EQUAL",
                  "value": "2020-01-01",
                  "valueType": "LITERAL"
                },
                {
                  "type": "CONDITION",
                  "label": "Exactly one usable reference price",
                  "dataType": "BOOLEAN",
                  "valueType": "EXPRESSION",
                  "value": "if drug_prices = null then false else if count(drug_prices[ndc = (if repackagedFlag = \"Y\" and \"Y\" = \"Y\" then originatorNDC else requestNDC)]) != 1 then false else if drug_prices[ndc = (if repackagedFlag = \"Y\" and \"Y\" = \"Y\" then originatorNDC else requestNDC)][1].prices = null then false else if count(drug_prices[ndc = (if repackagedFlag = \"Y\" and \"Y\" = \"Y\" then originatorNDC else requestNDC)][1].prices[source = \"Medispan-AWP\"]) != 1 then false else drug_prices[ndc = (if repackagedFlag = \"Y\" and \"Y\" = \"Y\" then originatorNDC else requestNDC)][1].prices[source = \"Medispan-AWP\"][1].unitprice != null and quantity != null"
                }
              ]
            }
          ],
          "outputParameters": [
            {
              "parameter": "pricingMethodology",
              "dataType": "NUMBER",
              "valueType": "EXPRESSION",
              "value": "(drug_prices[ndc = (if repackagedFlag = \"Y\" and \"Y\" = \"Y\" then originatorNDC else requestNDC)][1].prices[source = \"Medispan-AWP\"][1].unitprice * quantity) * (1 - (1.1 * 0.01))"
            },
            {
              "parameter": "dispenseFee",
              "dataType": "NUMBER",
              "valueType": "LITERAL",
              "value": {"$numberDecimal": "10.00"}
            }
          ],
          "type": "RULE",
          "order": 1
        }
      ]
    }
  ]
}
```

`strategyVersion` identifies source content; `snapshotVersion` identifies the compilation artifact. Never overwrite a published snapshot. Keep condition/output shapes aligned with the source and reject unresolved tokens or compilation errors.

Compile from a consistent view of approved, pinned versions. Record the exact compiler, FEEL engine, fact adapter, and rounding configuration in production metadata. The sample compiler version is illustrative.

After publication lookup, this tree needs one document fetch. Keep BSON size below 16 MiB and nesting below the 100-level limit, with headroom. Reject oversized expansions or use explicitly versioned segments. Replay also requires original facts and reference-price data versions.

## 8. Publications · `strategy_publications`

Selects the runtime snapshot for one strategy and environment.

```json
{
  "_id": {"$oid": "000000000000000000000008"},
  "strategyId": "S000001",
  "environment": "production",
  "snapshotId": {"$oid": "000000000000000000000007"},
  "revision": 1,
  "publishedAt": {"$date": "2026-07-20T10:05:00Z"},
  "publishedBy": "rahul"
}
```

The unique `(strategyId, environment)` record points to an immutable snapshot. Update with the expected `revision`, then increment it atomically. A missing publication means the strategy is not deployed.

Verify strategy ownership and approvals; update the pointer and append its audit event in one transaction. Rollback points to a retained snapshot and increments revision. Cache snapshots by `_id`; define refresh/invalidation for publication pointers. In-flight evaluations keep their starting snapshot.

## Lifecycle

Authoring statuses are DRAFT, SUBMITTED, APPROVED, REJECTED, DISABLED, and ARCHIVED. Multiple versions can be APPROVED; the publication pointer determines execution.

Edit drafts with optimistic concurrency. Freeze executable content after submission; changes require a new version. Update ancestor references explicitly, then approve, compile, and publish. Disabling authoring content blocks new compilation; stopping a deployed strategy requires a publication change.

## Recommended indexes

Inspect existing data and indexes before applying. Resolve duplicate keys and replace incompatible unique indexes on `groupId`, `strategyId`, and `screenCode`; those older indexes would still block version history.

```javascript
db.rule_identities.createIndex({ ruleId: 1 }, { unique: true });
db.rule_identities.createIndex({ ruleName: 1 }, { unique: true });

db.rules.createIndex({ ruleId: 1, version: 1 }, { unique: true });
db.rules.createIndex({ screenCode: 1, status: 1 });

db.rule_groups.createIndex({ groupId: 1, version: 1 }, { unique: true });
db.rule_groups.createIndex({ screenCode: 1, status: 1 });
db.rule_groups.createIndex({ "items.ref": 1, "items.type": 1, "items.refVersion": 1 });

db.strategies.createIndex({ strategyId: 1, version: 1 }, { unique: true });
db.strategies.createIndex({ screenCode: 1, status: 1 });
db.strategies.createIndex({ "ruleGroups.groupId": 1, "ruleGroups.groupVersion": 1 });

db.strategy_snapshots.createIndex(
  { strategyId: 1, strategyVersion: 1, snapshotVersion: 1 },
  { unique: true }
);
db.strategy_publications.createIndex(
  { strategyId: 1, environment: 1 },
  { unique: true }
);

db.parameters.createIndex({ parameterCode: 1 }, { unique: true });
db.parameters.createIndex({ parameterName: 1 }, { unique: true });
db.parameters.createIndex({ parameterType: 1, status: 1 });

db.customscreens.createIndex({ screenCode: 1, version: 1 }, { unique: true });
db.customscreens.createIndex({ screenCode: 1, status: 1 });
```

### Find referencing documents

Use `$elemMatch` to match ID, type, and version within the same array element.

```javascript
db.rule_groups.find({
  items: { $elemMatch: { type: "RULE", ref: "R001", refVersion: 1 } }
});

db.strategies.find({
  ruleGroups: { $elemMatch: { groupId: "G000001", groupVersion: 1 } }
});
```

Repeat lookup through nested groups with visited-node protection. Indexes support discovery; application code enforces reference integrity and sibling order uniqueness.

## Audit and implementation notes

| Responsibility | Requirement |
| --- | --- |
| Workflow audit | Separate append-only `audit_events`: entity ID/version, action, actor, timestamp, and change details. |
| Audit lookup | Consider `{ entityType: 1, entityId: 1, occurredAt: -1 }`. |
| Decision replay | Store snapshot ID, selected rule path, input/data versions, outputs, and outcome separately. |
| Application checks | Validate types, references, roles, screen versions, constants, cycles, depth, approvals, and expressions. |
| Concurrent writes | Use compare-and-set updates and atomic version allocation; avoid unprotected `max(version) + 1`. |
| Retention | Preserve versions and snapshots needed for replay; avoid unbounded embedded history arrays. |

Require authenticated actor IDs. Creation/update timestamps are not a workflow timeline; restrict audit edits/deletes separately.

During migration, convert BSON types and resolve historical references explicitly. Test nested conditions, ordering, ties, missing/duplicate prices, zero prices, constants, decimal precision, output dependencies, and concurrent publication. Report evaluator errors distinctly from NO_MATCH; only boolean true matches.

## Validation scope

JSON structure, pinned references, resolved constants, and snapshot alignment were checked. Live MongoDB and FEEL execution were not tested. Confirm the originator-NDC setting, duplicate-price policy, name scope/case rules, and rounding before deployment.

[BSON types](https://www.mongodb.com/docs/v8.0/reference/bson-types/) · [Unique indexes](https://www.mongodb.com/docs/manual/core/index-unique/) · [Multikey indexes](https://www.mongodb.com/docs/manual/core/indexes/index-types/index-multikey/multikey-index-bounds/) · [Document limits](https://www.mongodb.com/docs/manual/reference/limits/)
