# First Pass MongoDB Data Model

This is a first pass MongoDB data model based on the provided MySQL dump. It is a first pass and should be treated as a starting point for review with the application team.

The main assumption is that the current MySQL schema was created around application specific tables and workflow processing tables. The MongoDB model below tries to reduce duplicate table families, keep high write event data separate, and use embedded documents where the relationship appears to be one to one or configuration oriented.

## Goals

Move away from a table for collection migration.

Group repeated application specific tables into shared collections with an app or lineOfBusiness discriminator.

Embed one to one details where they are read with the parent.

Keep append only history, audit, delivery, and task data in separate collections.

Convert varchar timestamps to proper BSON Date values during migration.

Preserve current uniqueness rules with MongoDB unique indexes where appropriate.

## Important assumptions to validate

The application frequently searches by dataSetId, historyId, status, currentAction, appName, feedFrom, processFile, policyNumber, customerName, templateId, resourceMetadataId, and lineOfBusiness.

History and audit records are append heavy and should not be embedded into parent documents as unbounded arrays.

The many app specific tables such as calm, coc_spd, dbd, ifp, oxford, prime, uhc, uhone, umr, ush, and usp represent variants of the same logical model.

The detail properties tables appear to be one to one with resource metadata because resourceMetadataId is unique.

The delivery detail tables appear to be one to one per historyId per delivery type because historyId is unique in those tables.

The ds_*_fields tables appear to be search metadata for data sets or documents and can be consolidated.

## Proposed collections

### applicationConfigs

Source tables

application_config
service_config
access
executions
workflow

Purpose

Store application level configuration, UI configuration, service configuration, access metadata, and execution wiring.

Suggested shape

```javascript
{
  _id: ObjectId,
  appName: "coc_spd",
  groupName: "group name",
  lob: "line of business",
  searchFields: {},
  headerFields: {},
  configParams: {},
  tableRes: {},
  holdConfigs: {},
  appDetails: {},
  uiConfigs: {},
  serviceConfig: {
    metadata: {}
  },
  executions: [
    {
      serviceName: "service",
      listenTopic: "topic",
      listenConsumerGroup: "group",
      targetTopic: "topic",
      deliverPolicy: "policy",
      priority: "priority",
      sourceType: "source",
      targetType: "target",
      description: "description"
    }
  ],
  createdAt: ISODate,
  updatedAt: ISODate
}
```

Indexes

```javascript
db.applicationConfigs.createIndex({ appName: 1 }, { unique: true })
db.applicationConfigs.createIndex({ lob: 1 })
db.applicationConfigs.createIndex({ "executions.serviceName": 1 })
```

Notes

The JSON columns in application_config should become native embedded documents instead of strings.

### DataSets

Source tables

data_set
archive_data_set
archive_history_new where it denormalizes data_set fields
batch_feeds as optional references or separate collection
ds_*_fields as search metadata

Purpose

Represent an inbound feed, document request, or processing unit. This appears to be one of the core operational entities.

Suggested shape

```javascript
{
  _id: "data_set_id",
  feed: {
    policy: "policy",
    set: "set",
    effectiveDate: ISODate,
    location: "path",
    from: "source"
  },
  templateConfigId: NumberLong,
  batchGroupId: NumberLong,
  jobStatus: "status",
  priority: "priority",
  startTime: ISODate,
  createTime: ISODate,
  artifactPrefix: "path",
  message: "message",
  metaDataId: "resource metadata id",
  reconcile: "Y",
  processFile: "file name",
  finalResultLocation: "path",
  dataInfo: "info",
  dataMark: "mark",
  tenancy: {
    subTenancy: "sub tenancy"
  },
  appName: "app",
  searchMetadata: {
    policyNumber: "policy",
    customerName: "customer",
    groupId: "group",
    groupName: "group",
    effectiveDate: ISODate,
    product: "product",
    state: "state",
    templateId: "template",
    documentType: "doc type",
    fields: {}
  },
  archived: false
}
```

Indexes

```javascript
db.dataSets.createIndex({ processFile: 1 }, { unique: true })
db.dataSets.createIndex({ "feed.from": 1, "tenancy.subTenancy": 1, createTime: -1 })
db.dataSets.createIndex({ jobStatus: 1, createTime: -1 })
db.dataSets.createIndex({ metaDataId: 1 })
db.dataSets.createIndex({ "searchMetadata.policyNumber": 1 })
db.dataSets.createIndex({ "searchMetadata.customerName": 1 })
db.dataSets.createIndex({ "searchMetadata.templateId": 1 })
db.dataSets.createIndex({ "searchMetadata.effectiveDate": 1 })
```

Notes

The ds_*_fields tables have many app specific indexed columns. Consolidating them into searchMetadata keeps the model flexible while still allowing targeted indexes for the fields actually used by the application.

Do not create every current MySQL single column index in MongoDB on day one. Start with the access patterns the app actually uses.

### histories

Source tables

history
archive_history
calm_history
coc_spd_history
dbd_history
ifp_history
levelfunded_history
lf_history
oxford_history
prime_history
umr_history
ush_history
usp_history
archive_history_new

Purpose

Store workflow execution state and history. This is likely a high value operational collection.

Suggested shape

```javascript
{
  _id: "history_id",
  appName: "coc_spd",
  workflowId: NumberLong,
  dataSetId: "data_set_id",
  executionId: "execution_id",
  status: "status",
  jobStatus: "job status",
  currentAction: "action",
  params: {},
  message: "message",
  retryCount: 0,
  workerChain: "worker chain",
  transmission: {
    init: {},
    worker: {}
  },
  version: "version",
  info: {},
  mark: {},
  result: "result",
  feedSnapshot: {
    feedFrom: "source",
    processFile: "file",
    feedLocation: "path",
    templateConfigId: NumberLong,
    batchGroupId: NumberLong,
    metaDataId: "id"
  },
  tenancy: {
    subTenancy: "sub tenancy"
  },
  timestamps: {
    startTime: ISODate,
    createTime: ISODate,
    lastUpdateTime: ISODate
  },
  archived: false
}
```

Indexes

```javascript
db.histories.createIndex({ dataSetId: 1, "timestamps.lastUpdateTime": -1 })
db.histories.createIndex({ workflowId: 1 })
db.histories.createIndex({ status: 1, "timestamps.lastUpdateTime": -1 })
db.histories.createIndex({ currentAction: 1, "timestamps.lastUpdateTime": -1 })
db.histories.createIndex({ appName: 1, "tenancy.subTenancy": 1, "timestamps.createTime": -1 })
db.histories.createIndex({ "feedSnapshot.feedFrom": 1, "tenancy.subTenancy": 1, "timestamps.createTime": -1 })
```

Notes

This should be a separate collection, not embedded inside dataSets, because history records are operational, indexed independently, and likely grow over time.

The archive tables can be represented with archived true or moved to a separate historiesArchive collection if retention and query isolation matter.

### resources

Source tables

resource_metadata
calm_resource_metadata
coc_spd_resource_metadata
dbd_resource_metadata
ifp_resource_metadata
levelfunded_resource_metadata
oxford_resource_metadata
prime_resource_metadata
uhc_resource_metadata
uhone_resource_metadata
umr_resource_metadata
ush_resource_metadata
usp_resource_metadata
*_detail_properties

Purpose

Represent document or resource metadata with optional detail properties embedded.

Suggested shape

```javascript
{
  _id: NumberLong,
  appName: "coc_spd",
  resourceName: "name",
  resourcePath: "path",
  parentId: NumberLong,
  lineOfBusiness: "lob",
  type: "type",
  userLastModified: "user",
  currentVersion: NumberLong,
  aliasName: "alias",
  md5Checksum: "checksum",
  status: "status",
  sizeInBytes: NumberLong,
  comments: "comments",
  migrationId: "migration id",
  reference: "reference",
  tenancy: {
    subTenancy: "sub tenancy"
  },
  detailProperties: {
    detailPropertiesId: "id",
    type: "type",
    status: "status",
    timestamp: ISODate,
    usage: "usage",
    properties: {},
    details: {},
    user: "user"
  },
  timestamps: {
    created: ISODate,
    lastModified: ISODate
  }
}
```

Indexes

```javascript
db.resources.createIndex({ resourceName: 1, parentId: 1, lineOfBusiness: 1, appName: 1 }, { unique: true })
db.resources.createIndex({ migrationId: 1 }, { unique: true, sparse: true })
db.resources.createIndex({ aliasName: 1 })
db.resources.createIndex({ parentId: 1 })
db.resources.createIndex({ lineOfBusiness: 1, status: 1 })
```

Notes

The detail properties tables look like good embedding candidates because resourceMetadataId is unique.

Keep parentId as a reference rather than embedding children unless the UI always reads an entire resource tree and the tree size is bounded.

### templates

Source tables

templates_config
calm_templates_config
coc_spd_templates_config
dbd_templates_config
ifp_templates_config
levelfunded_templates_config
oxford_templates_config
prime_templates_config
uhc_templates_config
uhone_templates_config
umr_templates_config
ush_templates_config
usp_templates_config
*_template_reference

Purpose

Represent template definitions and ordered resource references.

Suggested shape

```javascript
{
  _id: NumberLong,
  appName: "coc_spd",
  referenceId: "reference",
  templateName: "template",
  productName: "product",
  planProductYear: "year",
  businessSegment: "segment",
  fundingArrangement: "funding",
  planTypes: "types",
  templatePath: "path",
  lineOfBusiness: "lob",
  type: "type",
  resourceMetadataId: NumberLong,
  searchConfig: {},
  info: {},
  tenancy: {
    subTenancy: "sub tenancy"
  },
  resourceRefs: [
    {
      templateRefId: NumberLong,
      resourceMetadataId: NumberLong,
      sequence: NumberLong,
      tempSequence: NumberLong,
      lineOfBusiness: "lob",
      rules: {},
      comments: "comments",
      compendiumDocId: "id",
      ditamapParentId: "id"
    }
  ]
}
```

Indexes

```javascript
db.templates.createIndex({
  productName: 1,
  planProductYear: 1,
  businessSegment: 1,
  fundingArrangement: 1,
  planTypes: 1,
  lineOfBusiness: 1,
  appName: 1
}, { unique: true, sparse: true })

db.templates.createIndex({ appName: 1, lineOfBusiness: 1 })
db.templates.createIndex({ resourceMetadataId: 1 })
db.templates.createIndex({ "resourceRefs.resourceMetadataId": 1 })
```

Notes

Embedding template references is reasonable if the number of resources per template is bounded. If a template can have thousands of references or references are frequently updated independently, keep templateReferences as a separate collection.

### appAttributes

Source tables

calm_app_attributes
coc_spd_app_attributes
dbd_app_attributes
ifp_app_attributes
levelfunded_app_attributes
oxford_app_attributes
prime_app_attributes
uhc_app_attributes
uhone_app_attributes
umr_app_attributes
ush_app_attributes
usp_app_attributes

Purpose

Store application attribute definitions.

Suggested shape

```javascript
{
  _id: "attribute_id",
  appName: "coc_spd",
  key: "key",
  displayName: "display name",
  usageType: "usage",
  dataType: "type",
  extractProperties: {},
  attributeDetails: {},
  attributeInfo: {},
  messages: "message",
  order: "order",
  transferType: "transfer type"
}
```

Indexes

```javascript
db.appAttributes.createIndex({ appName: 1, key: 1 }, { unique: true })
db.appAttributes.createIndex({ appName: 1, usageType: 1 })
```

Notes

This is a straightforward consolidation. Add appName because the old schema split the same structure into multiple app specific tables.

### rules

Source tables

rules_*
rule_ref_*
rule_set_*
rule_set_archive
rule_ref_template_mapping_*

Purpose

Store rules, rule references, rule sets, and mappings to templates.

Suggested shape

```javascript
{
  _id: NumberLong,
  appName: "usp",
  condition: "condition",
  ruleName: "name",
  type: "type",
  field: "field",
  value: "value",
  lineOfBusiness: "lob",
  ruleRefId: NumberLong,
  sourceId: NumberLong,
  props: {},
  details: {},
  valid: true,
  disabled: false,
  tenancy: {
    subTenancy: "sub tenancy"
  },
  timestamps: {
    created: ISODate,
    lastUpdated: ISODate
  },
  modifiedBy: "user"
}
```

Possible supporting collection

```javascript
{
  _id: NumberLong,
  appName: "usp",
  refRules: {},
  refProps: {}
}
```

Indexes

```javascript
db.rules.createIndex({ appName: 1, lineOfBusiness: 1, type: 1 })
db.rules.createIndex({ appName: 1, field: 1, value: 1 })
db.rules.createIndex({ ruleRefId: 1 })
db.rules.createIndex({ disabled: 1, valid: 1 })
```

Notes

Rules tend to be configuration data but may be updated independently. Do not over embed until the application confirms how rules are read and changed.

### variables

Source tables

coc_spd_variables
uhone_variables
umr_variables
ush_variables
*_variables_ref

Purpose

Store reusable variables and their resource mappings.

Suggested shape

```javascript
{
  _id: NumberLong,
  appName: "coc_spd",
  fieldId: NumberLong,
  variableName: "name",
  description: "description",
  variableType: "type",
  dataType: "type",
  details: {},
  active: true,
  res1: {},
  res2: "value",
  lastModifiedDate: ISODate
}
```

Supporting collection if needed

```javascript
{
  _id: ObjectId,
  appName: "coc_spd",
  resourceMetadataId: NumberLong,
  variableId: NumberLong,
  sequence: NumberLong,
  res1: {},
  res2: "value"
}
```

Indexes

```javascript
db.variables.createIndex({ appName: 1, variableName: 1 }, { unique: true })
db.variableRefs.createIndex({ appName: 1, variableId: 1, resourceMetadataId: 1 }, { unique: true })
db.variableRefs.createIndex({ appName: 1, resourceMetadataId: 1, sequence: 1 })
```

Notes

The reference table is many to many, so it should usually remain separate unless the number of variables per resource is small and only read from the resource side.

### deliveries

Source tables

deliver_b360
deliver_ben_answers
deliver_doc360
deliver_ibaag
deliver_rrd
deliver_uspclient
deliver_status
deliver_package

Purpose

Track delivery status and downstream acknowledgements.

Suggested shape

```javascript
{
  _id: "deliver_detail_id",
  deliveryType: "doc360",
  historyId: "history_id",
  delivered: "Y",
  ack: "ack",
  status: "status",
  batchId: "batch",
  appName: "app",
  info: "info",
  detail: {},
  downstream: {
    name: "downstream",
    ackTime: ISODate,
    props: {},
    config: {}
  },
  package: {
    deliverPackageId: "id",
    properties: {},
    batchSize: 100,
    batchConfig: "config"
  },
  tenancy: {
    subTenancy: "sub tenancy"
  },
  createdAt: ISODate
}
```

Indexes

```javascript
db.deliveries.createIndex({ historyId: 1, deliveryType: 1 }, { unique: true })
db.deliveries.createIndex({ delivered: 1, ack: 1 })
db.deliveries.createIndex({ status: 1, createdAt: -1 })
db.deliveries.createIndex({ batchId: 1 })
db.deliveries.createIndex({ appName: 1 })
```

Notes

The repeated delivery tables have nearly identical schemas. A single deliveries collection with deliveryType is a better first pass than one collection per downstream.

### audits

Source tables

com360_audit_log
service_audit_log
book_of_business_audit_details

Purpose

Append only audit events.

Suggested shape

```javascript
{
  _id: ObjectId,
  auditType: "service",
  historyId: "history id",
  sourceId: "source id",
  serviceName: "service",
  action: "action",
  status: "status",
  message: "message",
  bob: "book of business",
  templateId: "template",
  benefitPlanId: "plan",
  source: "source",
  channel: "channel",
  sourceTransactionId: "id",
  documentType: "document type",
  upstreamSystem: "system",
  state: "state",
  tenancy: {
    tenancy: "tenancy",
    subTenancy: "sub tenancy"
  },
  user: "user",
  timestamp: ISODate,
  updatedAt: ISODate
}
```

Indexes

```javascript
db.audits.createIndex({ historyId: 1, timestamp: -1 })
db.audits.createIndex({ serviceName: 1, action: 1, timestamp: -1 })
db.audits.createIndex({ status: 1, timestamp: -1 })
db.audits.createIndex({ sourceTransactionId: 1 })
db.audits.createIndex({ bob: 1, status: 1 })
db.audits.createIndex({ templateId: 1, status: 1 })
```

Notes

Keep audits separate. They are append only and often have different retention needs from operational state.

### tasks

Source tables

task

Purpose

Track claimable or executable work items.

Suggested shape

```javascript
{
  _id: NumberLong,
  historyId: "history_id",
  dataSetId: "data_set_id",
  status: "status",
  claim: {
    user: "user",
    time: ISODate,
    file: "path"
  },
  parameters: {},
  contentFile: "path"
}
```

Indexes

```javascript
db.tasks.createIndex({ historyId: 1 })
db.tasks.createIndex({ dataSetId: 1 })
db.tasks.createIndex({ status: 1 })
db.tasks.createIndex({ "claim.user": 1 })
```

Notes

Convert parameters to an object if it is JSON like content. If it is plain text, keep it as a string.

### referenceData

Source tables

data_dictionary
error
book_of_business
book_of_business_plan_setup

Purpose

Store smaller lookup and reference data.

Suggested shapes

```javascript
{
  _id: NumberLong,
  type: "dataDictionary",
  fieldName: "field",
  screenName: "screen",
  field: "field path",
  effectiveStart: ISODate,
  effectiveEnd: ISODate,
  validValues: "values",
  sources: {
    cirrus: "value",
    planLibrary: "value",
    nimbus: "value"
  },
  fieldId: "field id",
  screenId: "screen id",
  lob: "lob"
}
```

```javascript
{
  _id: NumberLong,
  type: "error",
  name: "error name",
  code: "code",
  description: "description",
  lob: "lob",
  properties: {},
  result: {},
  resolution: "resolution",
  include: "include",
  exclude: "exclude"
}
```

Indexes

```javascript
db.referenceData.createIndex({ type: 1, lob: 1 })
db.referenceData.createIndex({ type: 1, fieldId: 1 })
db.referenceData.createIndex({ type: 1, code: 1 })
db.referenceData.createIndex({ type: 1, appName: 1 })
```

## Embed versus reference guidance

Embed when the child is one to one with the parent and is normally read with the parent.

Good first pass embedding candidates

detailProperties inside resources
feedSnapshot inside histories
searchMetadata inside dataSets
application UI and config JSON inside applicationConfigs
delivery package detail inside deliveries if small and read together

Reference when the child can grow without bound, is queried independently, or has a different lifecycle.

Good first pass reference candidates

histories from dataSets
audits from histories
tasks from histories
deliveries from histories
variableRefs between variables and resources
large template resource references if they can grow large

## Type conversion recommendations

Convert varchar timestamp fields to BSON Date.

Examples

start_time to startTime
create_time to createTime
last_update_time to lastUpdateTime
created_timestamp to createdAt
last_modified_timestamp to lastModifiedAt
current_time_stamp to timestamp

Convert Y and N or 1 and 0 flags to booleans where possible.

Examples

active to active boolean
valid to valid boolean
disabled to disabled boolean
delivered should be reviewed because it may be a status code rather than a boolean

Keep business identifiers as strings if upstream systems treat them as strings.

Examples

policyNumber
groupId
templateId
historyId
dataSetId
processFile

## Suggested migration sequence

Phase 1

Create applicationConfigs, dataSets, histories, resources, templates, deliveries, audits, tasks, referenceData.

Phase 2

Migrate configuration and reference data first because it is lower risk.

Phase 3

Migrate resources and templates.

Phase 4

Migrate operational data sets and histories.

Phase 5

Migrate append only deliveries, audits, and tasks.

Phase 6

Backfill searchMetadata on dataSets from ds_*_fields tables.

Phase 7

Compare application query results between MySQL and MongoDB.

## Questions still worth asking later

What are the top application screens and API queries by volume?

Which entities are always read together in one request?

Which history and audit records have retention requirements?

Which ds_*_fields columns are actually searched by users?

How often are templates, rules, variables, and resource metadata updated independently?

## Red flags to watch

Do not create one MongoDB collection per MySQL table by default.

Do not embed unbounded history or audit arrays inside dataSets.

Do not carry over all MySQL indexes without validating query patterns.

Do not keep dates as strings unless there is a strong application reason.

Do not split collections by app name unless isolation requirements demand it.

Do not assume every JSON column is clean JSON in production data. Validate before migration.

## First pass collection list

applicationConfigs
dataSets
histories
resources
templates
appAttributes
rules
variables
variableRefs
deliveries
audits
tasks
referenceData

## Example document flow

A feed file enters the system and creates a dataSets document.

Workflow processing creates one or more histories documents referencing dataSetId.

Tasks, deliveries, and audits reference historyId.

Resources and templates are referenced from dataSets or histories through metadata ids and template config ids.

Search screens query dataSets.searchMetadata, histories.status, histories.currentAction, resources.aliasName, templates.lineOfBusiness, and audits.timestamp.

## Bottom line

The best first pass is to collapse repeated app specific table families into shared collections with appName and lineOfBusiness fields.

The strongest consolidation opportunities are histories, resources, template configs, template references, app attributes, detail properties, rules, deliveries, and ds_*_fields.

The safest operational boundary is to keep dataSets, histories, audits, tasks, and deliveries separate because they likely have different growth, indexing, and retention patterns.
