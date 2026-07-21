# UDP Domain -- MongoDB Atlas TFW walkthrough

## Executive Summary

MongoDB Atlas is a foundational component of the UDP platform. It serves
as the operational system of record, persistent memory layer, workflow
state store, and retrieval platform for agentic workloads.

While Redis handles short-lived session context and Azure ML provides
model inference, Atlas maintains the durable state required for agents
to operate consistently across requests and sessions.

## Current UDP Architecture Responsibilities

### Redis

-   Short-term memory
-   Active session context
-   Ephemeral cache
-   In-flight agent state

### MongoDB Atlas

-   Workflow state
-   Conversation history
-   Session history
-   Long-term memory
-   Agent metadata
-   Registry metadata
-   Domain context
-   Audit history
-   Operational data

### Atlas Search / Vector Search

-   Full-text search
-   Semantic search
-   Hybrid search
-   Conversation retrieval
-   Domain document retrieval

### Azure ML / AI Services

-   Model hosting
-   Inferencing
-   Safety controls
-   ML workflows

### Event Hubs

-   Asynchronous messaging
-   Workflow notifications
-   Event propagation

### Key Vault

-   Secret management
-   Credential storage

## Why MongoDB Atlas Matters

Atlas is not simply a database in the UDP architecture.

It provides: - Durable workflow state - Persistent agent memory -
Long-term conversation storage - Search and retrieval - Vector
capabilities - Operational metadata - Audit and recovery capabilities

> MongoDB Atlas serves as UDP's operational system of record, storing
> workflow state, conversation history, long-term memory, agent and
> registry metadata, and domain context. Atlas Search and Vector Search
> operate directly over that data to support lexical, semantic, and
> hybrid retrieval.

## Workflow State

UDP stores workflow state in Atlas, making it possible to: - Resume
interrupted workflows - Track current workflow step - Maintain approval
status - Support human-in-the-loop processes - Track retries and
failures - Maintain audit history

Typical attributes: - workflowId - currentStep - status -
assignedAgent - retryCount - timestamps - failureDetails -
approvalStatus - eventReferences

## Search Architecture

Recommended search pattern: 1. Apply metadata filters. 2. Execute Atlas
Search and/or Vector Search. 3. Retrieve 30--100 candidates. 4.
Optionally rerank. 5. Return the top 5--10 results to the LLM.

## Reranking

Use reranking selectively.

Good candidates: - Conversation history - Policies - Domain documents -
Taxonomies - Multi-document retrieval

Poor candidates: - workflowId lookups - Registry lookups - Exact
searches - Strongly filtered queries

Recommendation:

> Design for reranking, but do not apply it to every request.

## Voyage Context 4

Potential benefits: - Context-aware embeddings - Improved retrieval
quality - Reduced chunking sensitivity - Better handling of long
documents - Better conversation understanding

Useful for: - Long conversations - Policies - Workflow definitions -
Agent memory - Domain documentation

Recommended flow: 1. Chunk documents. 2. Generate contextual embeddings
using Voyage Context 4. 3. Store vectors in Atlas. 4. Execute Atlas
Vector Search. 5. Optionally rerank results.

## Chunking

The current architecture diagram does not indicate the chunking strategy
in use.

Common possibilities: - Semantic Kernel splitters - LangChain
RecursiveCharacterTextSplitter - Custom application logic

Questions for the UDP team: 1. How are documents chunked today? 2. Is
chunking token-based or semantic? 3. Have multiple chunking strategies
been evaluated? 4. Are conversations chunked by turn or by token count?

### Recommended Chunking Strategies

  Data Type              Strategy
  ---------------------- ----------------------------
  Conversations          5--10 conversational turns
  Policies               Section-based
  Workflow Definitions   Step-based
  MCP Documentation      Function-based
  Agent Logs             Session-based
  Registry Metadata      No chunking required

## Recommended Architecture

1.  Redis for short-term memory.
2.  Atlas for durable operational state.
3.  Atlas Search for lexical retrieval.
4.  Atlas Vector Search for semantic retrieval.
5.  Voyage Context 4 for contextual embeddings.
6.  Reranking where precision improvements are required.
7.  Azure ML for model inference.

## Final Takeaway

MongoDB Atlas is more than a persistence layer within UDP---it is the
durable memory, workflow state engine, and retrieval platform that
enables agents to maintain context and operate consistently across
sessions.

Combining Atlas Search, Vector Search, workflow state, and contextual
embeddings provides a strong foundation for building scalable enterprise
agentic systems.
