# MongoDB Rules Engine — Corrected Schema and Recommendations

This replaces the supplied schema with a consistent versioned authoring model and immutable compiled runtime snapshots. It preserves nested AND/OR conditions, multiple outputs, rule-local constants, screen-based aggregation, and the FIRST / COLLECT_MIN / COLLECT_MAX policies.

## Review findings and corrections

| Issue in the supplied file | Correction |
| --- | --- |
| Group/strategy IDs were unique even though documents have versions | Use unique compound business-ID/version indexes. |
| Rule-name uniqueness conflicted with multiple versions | Reserve each stable rule name once in `rule_identities`; versions retain the same name. |
| References selected IDs without versions | Pin every rule, group, and screen dependency to an explicit version. |
| `derivedParameters.parameter` disagreed with `.name`; `#useOriginatorNdc` was undefined | Standardize on `name` and define all three constants. |
| Snapshot used a different condition shape and retained unresolved constants | Copy the full condition tree and compile constants into every expression. |
| APPROVED and ACTIVE were conflated | Approval belongs to authoring versions; a publication pointer selects the runtime snapshot. |
| Monetary NUMBER was a string; timestamps and IDs were placeholders | Use Decimal128 for decimal literals, BSON Date timestamps, and valid ObjectIds. |
| Screen and snapshot aggregation used different expression fields | Use `valueType` + `value` consistently. |
| First price selection silently assumed a match and uniqueness | Guard against missing or duplicate matches before selecting `[1]`. |
| Authoring references duplicated labels/descriptions | Keep references minimal; use versioned source records for labels. |
| Screen fields contained duplicate self-references | Remove the contradictory sample; document UI-only references separately. |

## Storage and modeling conventions

Each fenced JSON example is one document in the named collection. Arrays inside documents are intentional bounded child structures. The original file already used individual top-level documents; no top-level-array correction is needed here.

Examples use MongoDB Extended JSON: `$oid`, `$date`, and `$numberDecimal` represent BSON values. Parse through an Extended JSON-aware driver utility or import tool; do not insert these wrappers as ordinary nested objects using plain JSON parsing. Versions and order values are positive integers.

Store workflow timestamps as BSON Date. A business date such as `dateOfService` is deliberately an ISO `YYYY-MM-DD` string in the stored literal, converted to a FEEL date by the evaluator; it is not a UTC timestamp. Normalize incoming facts to the declared type before comparison.

Assumptions: one logical namespace, unsharded collections, globally unique and case-sensitive immutable rule names, and one published snapshot per strategy per environment. Multi-tenancy requires a tenant key on documents, references, queries, and uniqueness indexes. Sharding requires a separate shard-key/index review. Decimal computation and rounding policy must be agreed with the application team.

## Version and lifecycle contract

Keep multiple versions in the same authoring collection, one document per version. `rules`, `rule_groups`, `strategies`, and `customscreens` use `DRAFT`, `SUBMITTED`, `APPROVED`, `REJECTED`, `DISABLED`, or `ARCHIVED`. Multiple versions may be APPROVED simultaneously; approval does not select runtime execution. Draft edits may update that draft with optimistic concurrency; after submission, freeze its executable content and create a new version for content changes. Metadata-only workflow transitions are recorded separately in audit events.

An approved executable tree pins an approved screen version and approved rule/group versions. Editing a rule does not silently change an existing group or strategy: create new ancestor versions with updated references, approve, compile, and publish. Existing snapshots remain immutable. Disabling an authoring version prevents new compilation; stopping an already published strategy requires an explicit publication change.

## `rule_identities` — unique logical rule names

```json
{
  "_id": {
    "$oid": "000000000000000000000006"
  },
  "ruleId": "R001",
  "ruleName": "R_BUY_Walmart_1_Brand_202603_DySupp_1_83",
  "createdAt": {
    "$date": "2026-07-15T11:33:24.377Z"
  },
  "createdBy": "jane.doe"
}
```

This small registry reserves one `ruleName` for one `ruleId` across all versions. Both fields are unique here. Version documents repeat the name for display, but must match the registry. Names are immutable in this recommendation; renames require an explicit migration. Do not release a reserved name just because a rule is archived. Create the identity and initial version together in a transaction. MongoDB does not enforce cross-collection equality; the authoring service owns that check.

## `rules` — versioned rule content

```json
{
  "_id": {
    "$oid": "000000000000000000000001"
  },
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
      "value": {
        "$numberDecimal": "1.1"
      }
    },
    {
      "name": "referencePriceSource",
      "dataType": "STRING",
      "value": "Medispan-AWP"
    },
    {
      "name": "useOriginatorNdc",
      "dataType": "STRING",
      "value": "Y"
    }
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
      "value": {
        "$numberDecimal": "10.00"
      }
    }
  ],
  "createdAt": {
    "$date": "2026-07-15T11:33:24.377Z"
  },
  "updatedAt": {
    "$date": "2026-07-16T09:48:59.052Z"
  },
  "createdBy": "jane.doe",
  "updatedBy": "jane.doe",
  "screenVersion": 1,
  "expressionLanguage": "FEEL"
}
```

`conditions` is a nonempty array of trees, implicitly AND'ed. A GROUP has an AND/OR operator and a nonempty `conditions` array; group nesting is bounded by an application-defined limit. A literal CONDITION requires `parameter`, `dataType`, `valueType: "LITERAL"`, and `operator`. An expression CONDITION requires `valueType: "EXPRESSION"`, `dataType: "BOOLEAN"`, and a FEEL expression in `value`; `label` is display-only, and neither a comparison operator nor a fact path is used for this variant.

Literal operators are `EQUALS`, `NOT_EQUALS`, `GREATER_THAN`, `LESS_THAN`, `GREATER_THAN_OR_EQUAL`, `LESS_THAN_OR_EQUAL`, `IN`, `NOT_IN`, `BETWEEN`, `CONTAINS`, `STARTS_WITH`, `REGEX`, `IS_NULL`, and `IS_NOT_NULL`. Reject unknown operators. IN/NOT_IN require a list of values of the operand type; BETWEEN requires two ordered bounds and is inclusive. IS_NULL/IS_NOT_NULL omit `value`. Define missing paths explicitly: in this recommendation missing and null satisfy IS_NULL; other comparisons on missing/null are nonmatches. STRING/NUMBER/BOOLEAN/DATE/LIST are type declarations, not permission for arbitrary coercion. LIST requires a defined element type for typed list comparisons. Document the application operator-to-FEEL mapping and regex dialect.

Derived parameters are independent named literals, unique by `name` within a rule. Their `#name` syntax is an application compile-time extension, not assumed native FEEL syntax. Reject undefined constants, duplicate names, and references to other constants. Use a tokenizer/parser and type-aware literal serialization, including escaping strings and constructing date literals; never use unrestricted string replacement in the production compiler. Do not replace token-like text inside quoted strings.

The example explicitly defines `useOriginatorNdc = "Y"`, which was missing in the original. This is a proposed business setting requiring confirmation. It retains `adjustmentFactor = 1.1` and the original `1 - (factor * 0.01)` formula, meaning a 1.1% reduction, not a 10% increase.

The guard requires exactly one matching drug and one price from the requested source. Duplicate matches are rejected rather than resolved by arbitrary list order. Validate facts before evaluation: `drug_prices`/`prices` must be lists, NDCs must be strings preserving leading zeroes, and unit price/quantity must be numeric. Empty lists yield no match. The sample FEEL expressions must be compiled and exercised against the selected engine; engine/version and fact adapters were not supplied.

Output parameter names are unique within a rule. Evaluate outputs in array order, using an isolated candidate context. A later output may reference an earlier output; reject forward/cyclic references. Remove optional `order` from outputs to avoid two conflicting order definitions. Promote the selected candidate's outputs only after hit-policy selection, so evaluating a losing candidate never changes another candidate's facts. Use decimal arithmetic end to end, not a Decimal128-to-double conversion. Define currency scale and rounding in the deployed evaluator configuration.

## `rule_groups` — versioned ordered references

```json
{
  "_id": {
    "$oid": "000000000000000000000002"
  },
  "groupId": "G000001",
  "groupName": "Test12",
  "groupDescription": "test1112",
  "screenCode": "SCREEN_DEFAULT",
  "version": 1,
  "type": "RULE_GROUP",
  "status": "APPROVED",
  "hitPolicy": "FIRST",
  "items": [
    {
      "type": "RULE",
      "ref": "R001",
      "refVersion": 1,
      "order": 1
    }
  ],
  "createdAt": {
    "$date": "2026-07-15T18:08:58.571Z"
  },
  "updatedAt": {
    "$date": "2026-07-15T18:08:58.577Z"
  },
  "createdBy": "jane.doe",
  "updatedBy": "jane.doe",
  "screenVersion": 1
}
```

Each item has `type: "RULE"` or `"GROUP"`, `ref`, `refVersion`, and a positive sibling-unique `order`. A nested group uses the same shape, with `ref` pointing to a `groupId`. Sort by `order`, independent of physical array order. Reject missing targets, cross-screen/version references, cycles, and excessive depth/expanded size. Cycle detection must track versioned nodes on the current traversal path; reuse in separate branches is not itself a cycle.

FIRST returns the first matching child. COLLECT_MIN / COLLECT_MAX return one child's complete result with the minimum/maximum comparable value, not a mixture of outputs from different rules. Ties use the first child in order at each level. A nested group returns its selected candidate to its parent. No matching child returns a distinct NO_MATCH result, never a fabricated zero price.

## `strategies` — versioned strategy definition

```json
{
  "_id": {
    "$oid": "000000000000000000000003"
  },
  "strategyId": "S000001",
  "strategyName": "STR_BUY_NYSIF_Network_1",
  "strategyDescription": "STR_BUY_NYSIF_Network_1",
  "screenCode": "SCREEN_DEFAULT",
  "version": 1,
  "hitPolicy": "COLLECT_MIN",
  "status": "APPROVED",
  "ruleGroups": [
    {
      "groupId": "G000001",
      "groupVersion": 1,
      "order": 1
    }
  ],
  "createdAt": {
    "$date": "2026-07-15T18:28:04.834Z"
  },
  "updatedAt": {
    "$date": "2026-07-15T18:28:11.561Z"
  },
  "createdBy": "jane.doe",
  "updatedBy": "jane.doe",
  "screenVersion": 1
}
```

`ruleGroups` pins `groupId` + `groupVersion`. Orders are positive and unique among siblings. All transitive dependencies share both `screenCode` and `screenVersion`. The strategy uses the same hit-policy semantics as groups. Multiple approved strategy versions can coexist; runtime selection is handled by `strategy_publications`.

## `parameters` — authoring catalog

```json
{
  "_id": {
    "$oid": "000000000000000000000004"
  },
  "parameterCode": "P0001",
  "parameterName": "pricingMethodology",
  "displayName": "Pricing Methodology",
  "description": "Calculated price before dispense fee.",
  "parameterType": [
    "OUTPUT"
  ],
  "dataType": "NUMBER",
  "uiFieldType": "NUMBER",
  "status": "ACTIVE",
  "createdAt": {
    "$date": "2026-07-14T20:13:19.090Z"
  },
  "createdBy": "jane.doe",
  "updatedAt": {
    "$date": "2026-07-14T20:13:19.090Z"
  },
  "updatedBy": "jane.doe"
}
```

The example is one catalog document; the other rule identifiers need their own catalog documents before validation succeeds. Required catalog entries for this rule set are shown below. `parameterCode` and `parameterName` are unique. `parameterType` is a nonempty, duplicate-free array of INPUT/OUTPUT/DERIVED roles. Screen membership is a UI concern; not every fact dependency must appear as an editable screen field.

| Required parameter name | Role | Type / purpose |
| --- | --- | --- |
| pricingMethodology | OUTPUT | NUMBER; illustrated above as P0001 |
| dispenseFee | OUTPUT | NUMBER |
| dateOfService | INPUT | DATE |
| drug_prices | INPUT | LIST of structured price records; define its fact contract |
| repackagedFlag | INPUT | STRING |
| originatorNDC | INPUT | STRING |
| requestNDC | INPUT | STRING |
| quantity | INPUT | NUMBER |
| adjustmentFactor | DERIVED | NUMBER |
| referencePriceSource | DERIVED | STRING |
| useOriginatorNdc | DERIVED | STRING |

Declare structured fact paths (`ndc`, `prices`, `source`, `unitprice`) in the `drug_prices` input contract. They are not free-standing scalar inputs. A schema/API contract for incoming facts must be implemented alongside this model.

Use optional `defaultValue` only with an explicit matching `valueType`; omit both when there is no default. `defaultOperator` applies only to INPUT roles. Derived values remain rule-local literals; remove the original COMPUTED-derived option unless computed derived values are deliberately added to the evaluator. Optional UI dropdown choices should use an ordered array of `{ "value": "stored-code", "label": "Display label" }` objects instead of keys with implicit order.

Treat catalog names, roles, and types as immutable once referenced by approved content; introduce a new parameter code/name for incompatible changes. Display labels may change. Runtime snapshots must not query this mutable catalog; compile required type/dependency information into the runtime contract as needed.

## `customscreens` — versioned screen and aggregation

```json
{
  "_id": {
    "$oid": "000000000000000000000005"
  },
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
      "parameters": [
        {
          "parameterCode": "P0001",
          "mandatory": true
        }
      ]
    }
  ],
  "aggregationOutput": {
    "name": "price",
    "dataType": "NUMBER",
    "valueType": "EXPRESSION",
    "value": "pricingMethodology + dispenseFee"
  },
  "createdAt": {
    "$date": "2026-07-14T20:13:19.090Z"
  },
  "createdBy": "jane.doe",
  "updatedAt": {
    "$date": "2026-07-14T20:13:19.090Z"
  },
  "updatedBy": "jane.doe"
}
```

`screenCode` + `version` identifies an exact screen definition. Before compiling the example, transition this screen from ACTIVE in the source to APPROVED as shown by the corrected lifecycle. `sectionId` is a UI identifier; `layoutColumns` replaces the unexplained `layout` number. Screen section parameter references point to catalog codes.

`aggregationOutput` uses `name`, `dataType`, `valueType`, and `value`, consistently with snapshot expression storage. It evaluates in each matched candidate's local output context. Every matching rule must produce all required outputs (`pricingMethodology` and `dispenseFee` here). A missing/non-numeric aggregate is an evaluation error, not NO_MATCH or zero. Reject publication if the output contract cannot be satisfied.

Optional `referredParameters` is UI-only. If retained, require distinct existing targets and explicit visibility/validation semantics, reject self-references and cycles, and keep it out of snapshots. The ambiguous original duplicate P0059 example has been removed.

## `strategy_snapshots` — immutable compiled runtime tree

```json
{
  "_id": {
    "$oid": "000000000000000000000007"
  },
  "strategyId": "S000001",
  "strategyVersion": 1,
  "snapshotVersion": 1,
  "screenCode": "SCREEN_DEFAULT",
  "screenVersion": 1,
  "compiledAt": {
    "$date": "2026-07-20T10:00:00Z"
  },
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
              "value": {
                "$numberDecimal": "10.00"
              }
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

This is a fully resolved nested tree, not a flattened structure. It preserves the same `conditions` and `outputParameters` shapes as the rule and includes the referenced rule/group versions. No runtime rule/group lookup or constant substitution is needed. Both guard and pricing expression have all constants substituted; the authoring rule retains its tokens.

`strategyVersion` identifies source content; `snapshotVersion` identifies a compilation artifact for that source. A compiler upgrade can create a new snapshotVersion without overwriting an existing artifact. Persist the exact engine version, fact-adapter version, decimal/rounding policy, and compiler build in production compilation metadata; the sample compilerVersion is illustrative. Bind those details to the artifact before publication.

Compile only from approved, version-pinned content, using a consistent read view. Recheck eligibility on publication if statuses have changed. Refuse publication on compilation/type errors or unresolved tokens. A rule/group edit creates impact-analysis work for its parents; it does not rewrite published snapshots.

One document fetch can supply this runtime tree after resolving the publication pointer. Keep serialized snapshots below MongoDB's 16 MiB BSON document limit with operational headroom and a bounded nesting depth. MongoDB also limits BSON nesting to 100 levels. Reject oversized expansions or design version-pinned segmented snapshots, accepting additional fetches; do not assume arbitrarily large strategies fit one document.

A snapshot reproduces the rule configuration, not external input state. Replaying a decision also needs the original input facts or an immutable fact reference, reference-price dataset version, and matching evaluator/compiler configuration.

## `strategy_publications` — explicit runtime selection

```json
{
  "_id": {
    "$oid": "000000000000000000000008"
  },
  "strategyId": "S000001",
  "environment": "production",
  "snapshotId": {
    "$oid": "000000000000000000000007"
  },
  "revision": 1,
  "publishedAt": {
    "$date": "2026-07-20T10:05:00Z"
  },
  "publishedBy": "rahul"
}
```

The unique `(strategyId, environment)` record points to exactly one immutable snapshot. Resolve it first, then fetch/cache the snapshot by `_id`. `revision` is an optimistic-concurrency counter: update using the expected prior revision and increment it atomically; a no-match update means another publisher won. A missing publication means the strategy is not deployed. Do not select runtime content using "latest version" or APPROVED status.

For publication, verify the snapshot belongs to this strategy and all required approvals, then update the pointer and append the publication audit event in one transaction. Rollback explicitly points to a prior retained snapshot and increments revision. Cache publication pointers with an explicit invalidation/refresh policy; document propagation delay. Already-running evaluations remain pinned to the snapshot they started with.

## Indexes

These commands define the intended indexes on the corrected collections. They are not a blind migration script: inspect existing indexes and data first, resolve duplicate keys, and deliberately replace incompatible unique `groupId`, `strategyId`, and `screenCode` indexes. Existing unique indexes on those IDs would still block multiple versions even after adding compound indexes. The examples assume unsharded collections and simple/case-sensitive collation.

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

The reverse-reference indexes use multiple scalar fields from the same array of embedded documents. Use `$elemMatch` so reference type, ID, and version must belong to the same element:

```javascript
db.rule_groups.find({
  items: { $elemMatch: { type: "RULE", ref: "R001", refVersion: 1 } }
});

db.strategies.find({
  ruleGroups: { $elemMatch: { groupId: "G000001", groupVersion: 1 } }
});
```

Repeat ancestor discovery for nested group references, with visited-node protection. Omit the version predicate only when intentionally finding all references to all versions. These indexes do not enforce sibling order uniqueness or referential integrity; application checks do. Screen-first status indexes support screen-scoped authoring lists; add a status-first index only if actual cross-screen workload warrants it.

## Audit and decision history

Keep full executable versions in their authoring collections. Keep append-only workflow audit events in a separate `audit_events` collection, rather than an ever-growing embedded history array. Each event records entity type, business ID, entity version or publication revision, action, actor, timestamp, and relevant before/after status or snapshot IDs. Create an index on `{ entityType: 1, entityId: 1, occurredAt: -1 }` if that is the timeline query.

`createdAt` and `updatedAt` describe creation and latest update; they are not a complete workflow timeline. Require nonempty authenticated actor IDs rather than accepting arbitrary client usernames. Application audit events need write permissions that prevent ordinary edits/deletes; an append-only design alone is not tamper-proof infrastructure auditing.

If decision traceability is required, use a separate evaluation-log collection keyed by decision ID with snapshot ID, selected rule/group version path, input/reference-data version, outputs, and outcome/error. Choose retention explicitly. Do not embed transaction histories in rule documents or add TTL deletion to source versions/snapshots needed for replay.

## Application checks and rollout

MongoDB unique indexes enforce the keys above. The authoring/compiler service enforces tree structure, types, token resolution, role compatibility, screen/version equality, reference existence, cycle/depth limits, sibling order uniqueness, allowed status transitions, approval authorization, and expression validity. Basic collection validation can be added for structural/type requirements; this document focuses on schema recommendations and corrected examples, not a validator framework.

Use compare-and-set updates for drafts and publication changes; allocate versions atomically or retry duplicate-key conflicts. Do not allocate using an unprotected `max(version) + 1`. Avoid hard-deleting versions still referenced by approved content or retained snapshots.

Before rollout, migrate string timestamps and decimal values to BSON types, reserve rule identities, and resolve every unversioned reference deliberately. Do not guess historical versions from today's ACTIVE document. Recompile new snapshots from corrected approved sources and compare outcomes with known decisions before publishing. Preserve the original executable artifacts needed for historical replay.

Validation cases must include nested AND/OR, FIRST order, min/max ties, no match, zero-valued valid prices, empty/missing/duplicate price records, undefined/quoted constant tokens, output dependencies, duplicate names/versions, reference cycles, decimal precision, and concurrent publication. Treat FEEL compile/runtime errors as explicit evaluation errors; only a successfully evaluated boolean true is a match. Do not silently convert malformed input or evaluator exceptions into ordinary NO_MATCH.

## Review boundary and references

The examples and references were checked for internal consistency, valid JSON, pinned dependencies, constant resolution, and snapshot/source alignment. No live MongoDB deployment, application compiler, or FEEL engine was supplied, so database execution, FEEL compatibility, and production business outcomes are not claimed as tested. Confirm the originator-NDC setting, duplicate-price policy, namespace/case rules, and rounding policy before deployment.

MongoDB storage/index references: [BSON types](https://www.mongodb.com/docs/v8.0/reference/bson-types/), [Unique indexes](https://www.mongodb.com/docs/manual/core/index-unique/), [Multikey index bounds](https://www.mongodb.com/docs/manual/core/indexes/index-types/index-multikey/multikey-index-bounds/), [Limits and thresholds](https://www.mongodb.com/docs/manual/reference/limits/). FEEL expressions are application behavior, not MongoDB server expressions.
