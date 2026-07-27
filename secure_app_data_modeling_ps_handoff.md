# Secure App Data Modeling Notes

## Purpose

This document captures the MongoDB data modeling work discussed for the
Secure application and is intended as a starting point for the
Professional Services engineer. These are working recommendations and
design questions, not a finalized physical schema.

## Domain Model Clarifications

### Identity

Identity represents a person.

Identity should remain the current representation of the person rather
than being used as a container for every access-related object
associated with that person.

### Account

Accounts are how access is granted.

Accounts should therefore be treated separately from Identity rather
than as another Identity subtype.

### System Access

Roles, Groups, and Hosts were discussed as different types of access
rather than automatically treating each as a separate top-level
collection.

A possible polymorphic model is:

``` javascript
{
  _id: ObjectId("..."),
  accessType: "role",
  systemId: ObjectId("..."),
  name: "Role1",
  state: "active"
}
```

Other documents could use:

``` javascript
accessType: "group"
```

or:

``` javascript
accessType: "host"
```

PS should validate whether these access types share enough schema,
lifecycle, ownership, and query behavior to justify a common System
Access collection.

## Roles and Granted Access

The diagrams showed Roles granting access through other access objects
such as Groups or Resources.

Two patterns were discussed.

### Reference only

``` javascript
{
  _id: 12,
  accessType: "role",
  name: "Role1",
  grants: [11, 14, 13]
}
```

This keeps the authoritative name and metadata on the referenced
objects.

### Reference plus selective denormalization

``` javascript
{
  _id: 12,
  accessType: "role",
  name: "Role1",
  grants: [
    {
      id: 11,
      name: "Group1",
      system: "MS"
    },
    {
      id: 14,
      name: "Group2",
      system: "MS"
    }
  ]
}
```

This can simplify reads and event generation, but creates duplicated
data that must be handled when names or other copied attributes change.

### Recommendation to validate

Determine whether Roles should maintain only IDs for granted Groups and
Resources or carry a small denormalized snapshot of frequently needed
values.

The decision should be based on:

-   Event payload requirements
-   Read patterns
-   Frequency of name changes
-   Whether consumers require self-contained data
-   Cost and complexity of propagating changes

## Templates and Roles

Templates were introduced as another document type used in the creation
or definition of Roles.

The major lifecycle question is whether a Template remains authoritative
after a Role is created.

### Authoritative inheritance

``` text
Template changes
      |
      v
Derived Roles change
```

This centralizes management but means a template modification can affect
existing access definitions.

### Blueprint or snapshot

``` text
Template
   |
   v
Create Role
   |
   v
Role evolves independently
```

In this model, the Role can retain lineage information:

``` javascript
{
  _id: 12,
  name: "Role1",
  templateSource: ObjectId("..."),
  templateVersion: 7,
  version: 22
}
```

### Recommendation to validate

Explicitly define whether Templates:

1.  Continuously govern derived Roles, or
2.  Serve as creation blueprints after which Roles have independent
    state.

If Roles can diverge, retaining the source template and version provides
useful lineage.

## Event-Oriented Modeling

Existing SQL queries were shown joining Application, environment,
Resource, Role, Platform, and classification data.

The important clarification was that these queries are used to assemble
the business context required to generate events.

The MongoDB design should therefore avoid simply reproducing the SQL
table structure.

Instead, PS should identify the natural aggregate needed to create each
event and determine which data should:

-   Live together
-   Be referenced
-   Be selectively duplicated

The goal is to make event construction align with the document model
rather than repeatedly reconstructing business objects through
relational-style joins.

## Name Changes and Denormalization

Name changes are particularly important when deciding whether to
duplicate names inside referencing documents.

For example, if a Role references a Group:

``` javascript
{
  roleId: 12,
  grants: [11]
}
```

a Group rename affects only the Group document.

If the Role stores:

``` javascript
{
  roleId: 12,
  grants: [
    {
      id: 11,
      name: "Old Group Name"
    }
  ]
}
```

the design needs a defined mechanism for deciding whether and when the
copied name is updated.

PS should establish whether copied values represent:

-   Current values that must remain synchronized, or
-   Historical snapshots that intentionally preserve the value at a
    point in time.

## Current State and Document Versioning

For operational entities, the recommended pattern discussed was to keep
one current document rather than inserting every version into the
primary collection.

Example:

``` javascript
{
  _id: ObjectId("..."),
  employeeId: 123,
  version: 17,
  name: "James Smith"
}
```

Updates modify the current document and increment the version.

If historical reconstruction or audit history is required, versions can
be persisted separately:

``` text
identity
  current document

identity_history
  version 15
  version 16
  version 17
```

This avoids requiring normal reads to find and sort through every
historical version just to retrieve current state.

The version field can also be used for optimistic concurrency to protect
against stale writes.

## Embedding Versus Referencing

The central modeling decision across Systems, System Access, Roles,
Groups, Resources, and Templates is not simply whether objects are
related, but whether they belong to the same aggregate.

Favor embedding when:

-   Data is normally read with the parent
-   Data shares the parent's lifecycle
-   Cardinality is bounded
-   Updates naturally occur at the aggregate level

Favor references when:

-   The object has an independent lifecycle
-   It is shared by many objects
-   It changes independently
-   The relationship can grow without a practical bound

Selective denormalization can be used where a small amount of
duplication materially improves common reads or event generation.

## Storage Considerations

Before finalizing embedding decisions, validate cardinality for:

-   Systems per application
-   Access objects per system
-   Groups or Resources granted by a Role
-   Roles derived from a Template
-   Accounts associated with an Identity
-   Historical versions per object

Avoid creating documents with arrays that can grow indefinitely.

Frequently changing objects should generally not be embedded inside
large, mostly static documents if a small change would create
unnecessary write amplification.

Audit/history data should not cause operational documents to grow
forever.

## Indexing and REST API Access Patterns

The Identity collection shown during the sessions had multiple
single-field indexes.

The REST API can query combinations of fields such as:

-   Status
-   Company
-   Department
-   Name

The recommendation is not to create an index for every possible
permutation.

Instead:

1.  Capture the highest-volume query shapes.
2.  Preserve dedicated indexes for important direct lookups.
3.  Design compound indexes around the dominant multi-field patterns.
4.  Validate proposed indexes with `explain("executionStats")` and
    production-like workloads.
5.  Add API guardrails where the query surface would otherwise be
    effectively unlimited.

A compound index should be designed for an actual access pattern rather
than created simply because fields can appear together.

## Atlas Search Boundary

Atlas Search was discussed as a potential capability for human-oriented
discovery across identities and access-related objects.

Examples include:

-   Name lookup
-   Partial matching
-   Autocomplete
-   Typo tolerance
-   Searching across several identity or access fields

It should not automatically replace exact operational lookups or
structured transactional API queries.

## Bulk Ingestion

The team discussed an initial ingest of approximately 2 million records.

This volume by itself is not a MongoDB scale concern.

For implementation, PS should validate:

-   Source and migration method
-   Bulk write batch sizes
-   Parallelism
-   Retry behavior
-   Idempotency
-   Index strategy during initial load
-   Cutover and reconciliation requirements

The exact ingestion approach should be tested against representative
document sizes and the target Atlas configuration.

## Recommended PS Validation Work

Rather than finalizing the physical schema from diagrams alone, use
representative workflows to test the model end to end.

Suggested workflows:

1.  Retrieve and update an Identity.
2.  Resolve the Accounts/access associated with an Identity.
3.  Create a Role from a Template.
4.  Resolve the Groups or Resources granted by a Role.
5.  Rename a referenced Group or Resource and determine the effect on
    denormalized data.
6.  Generate an event requiring Application, System, Role, Resource, or
    related context.

For each workflow, validate:

-   Aggregate boundary
-   Embed versus reference decision
-   Required denormalization
-   Cardinality
-   Update behavior
-   Version/history requirements
-   Query shape
-   Required indexes

## Key Open Decisions

The primary modeling decisions still to resolve are:

-   Whether the different System Access types belong in one polymorphic
    collection
-   Whether Roles reference granted access by ID only or include
    selected denormalized attributes
-   Whether Templates remain authoritative or act as one-time blueprints
-   What the natural aggregate boundary is for event generation
-   Which historical state must be retained separately from current
    state
-   Which REST API query patterns deserve purpose-built compound indexes
-   Where Atlas Search adds value versus standard MongoDB queries

These decisions should be driven by actual Secure workflows,
cardinality, ownership, and lifecycle rather than by the structure of
the legacy SQL or Cosmos models.
