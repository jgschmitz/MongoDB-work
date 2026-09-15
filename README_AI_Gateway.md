<div align="center">

# ⚡ AI Gateway Control Plane on MongoDB 🍃

### A fully simulated Streamlit experience for AI operations, observability, governance, and cost

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Ready-00ED64?style=for-the-badge&logo=mongodb&logoColor=white)
![Mode](https://img.shields.io/badge/Mode-100%25_Simulated-B896FF?style=for-the-badge)


</div>

---

## What this demo shows

The AI Gateway Control Plane demonstrates what a centralized operational experience for enterprise AI traffic could look like.

A user sends a prompt through a simulated gateway. The application then captures the request, model-routing decision, response, agent execution trace, policy findings, latency, token usage, estimated cost, identity, session, audit event, and retention metadata.

The entire experience runs locally using generated data stored only in the current Streamlit session.

## The experience

| Area | What it demonstrates |
| --- | --- |
| Gateway Playground | Sends a prompt through a simulated policy, routing, model, filtering, and persistence pipeline |
| Operations Dashboard | Visualizes request volume, success rate, latency, tokens, and estimated cost |
| Interaction Explorer | Filters and investigates individual AI requests and their complete execution traces |
| Audit Trail | Correlates actors, actions, risk signals, models, and request identifiers |
| Retention | Shows hot-data retention and long-term archive metadata |
| Requirement Map | Connects the application directly to the stated AI Gateway requirements |

## Quick start

### 1. Install the two dependencies

    pip install streamlit pandas

### 2. Launch the application

    streamlit run ai_gateway_demo.py

### 3. Seed the demo

Click **Seed Demo Data** in the sidebar. The application generates realistic traffic across multiple applications, environments, identities, providers, and models.

<code>
# --- Mongo ---
client = pymongo.MongoClient("mongodb+srv://jschmitz:gcp2025@darkstar.tnhx6.mongodb.net/?retryWrites=true&w=majority")
db = client.mixtureexperts
collection = db.voyage4demo
</code>

blah...blah blah.....

## Recommended demo flow

### 1 — Establish the problem

Open **Requirement Map** and explain that AI traffic creates more than prompts and responses. Enterprises also need agent traces, identity, policy results, telemetry, auditability, analytics, and retention.

### 2 — Generate realistic traffic

Click **Seed Demo Data**. The demo creates requests from:

- Benefits Assistant
- Claims Copilot
- RFP Studio
- Provider Search

The generated traffic is routed across simulated OpenAI, Azure OpenAI, and Ollama models.

### 3 — Show operational visibility

Open **Operations Dashboard** and highlight:

- Total AI request volume
- Success rate
- Average model latency
- Estimated model cost
- Usage by model and application
- Daily traffic patterns

### 4 — Investigate one interaction

Open **Interaction Explorer**, filter the data, and select a request.

Each interaction includes the original prompt, simulated response, calling application, environment, user or service identity, session, model provider, model name, tokens, latency, cost, compliance findings, and execution trace.

### 5 — Demonstrate governance

Open **Audit Trail** to show how operational events can be correlated through a common request identifier.

For a stronger policy example, submit a prompt containing an email address, patient-related language, or a fictional SSN such as <code>123-45-6789</code>. The gateway will attach risk and compliance findings to the interaction.

### 6 — Close with retention

Open **Retention** and explain the hot operational window, TTL concept, archive metadata, and separation of rich interaction documents from high-volume telemetry.

## Simulated gateway pipeline

    Incoming request
          │
          ▼
    Authenticate identity
          │
          ▼
    Evaluate policy and risk
          │
          ▼
    Route to selected model
          │
          ▼
    Simulate model execution
          │
          ▼
    Filter the response
          │
          ▼
    Capture interaction + telemetry + audit

Every stage appears in the execution trace with an outcome, duration, timestamp, and supporting details.

## Example interaction document

    {
      "request_id": "req_a8f19d72c841",
      "application": "claims-copilot",
      "environment": "production",
      "identity": {
        "user_id": "jeff.demo",
        "roles": ["demo-user"]
      },
      "session": {
        "id": "session_1430"
      },
      "model": {
        "provider": "openai",
        "name": "gpt-5-mini",
        "execution_mode": "SIMULATED"
      },
      "request": {
        "prompt": "Explain how MongoDB supports an AI Gateway."
      },
      "response": {
        "text": "Simulated model response"
      },
      "metrics": {
        "latency_ms": 642,
        "input_tokens": 91,
        "output_tokens": 73,
        "total_tokens": 164,
        "estimated_cost_usd": 0.00016875
      },
      "compliance": {
        "risk_level": "LOW",
        "findings": [],
        "policy_action": "ALLOW"
      },
      "trace": [
        {
          "step": "AUTHENTICATE",
          "outcome": "SUCCESS",
          "duration_ms": 5
        },
        {
          "step": "POLICY_CHECK",
          "outcome": "ALLOW",
          "duration_ms": 8
        },
        {
          "step": "MODEL_ROUTE",
          "outcome": "SUCCESS",
          "duration_ms": 3
        },
        {
          "step": "MODEL_CALL",
          "outcome": "SUCCESS",
          "duration_ms": 642
        }
      ],
      "retention": {
        "archive_after_days": 90,
        "archive_target": "OBJECT_STORAGE"
      }
    }

## Requirement coverage

| Requirement | Demo implementation |
| --- | --- |
| High-throughput request and response logging | Generated interaction records contain prompts, responses, models, identity, sessions, latency, tokens, and cost |
| Agent execution and orchestration traces | Each interaction contains a nested, ordered execution trace |
| Telemetry and observability data | Separate telemetry records drive latency, volume, reliability, token, and cost analytics |
| Audit and compliance records | Correlated audit events capture actors, actions, requests, and policy results |
| Real-time and historical analytics | Streamlit dashboards and filters demonstrate operational and historical analysis |
| Long-term retention and reporting | Retention dates and archive targets are included in each interaction |

## Simulated collections

The UI presents the data as three logical collections:

| Collection | Purpose |
| --- | --- |
| <code>ai_interactions</code> | Complete prompts, responses, context, identity, compliance results, and agent traces |
| <code>ai_telemetry</code> | High-volume time-oriented latency, token, cost, and success measurements |
| <code>ai_audit_events</code> | Durable actor, action, request, and governance records |

These are Python lists in the current version. They intentionally mirror the separation that could be implemented in MongoDB Atlas.

## Moving from demo to production

This demo intentionally stops before production integration. A real implementation could replace the in-memory lists with:

- MongoDB Atlas collections for interactions and audit events
- An Atlas time-series collection for telemetry
- OpenTelemetry instrumentation for agent and application traces
- Live model providers behind a gateway API
- Atlas Search or Vector Search for similar-interaction investigation
- TTL indexes for hot-data lifecycle management
- Atlas Online Archive or object storage for older history
- Role-based access controls, encryption, and enterprise audit configuration

The UI and document shapes can remain largely the same while the simulated persistence and model execution are replaced behind the scenes.

## Project structure

    AI_Gateway/
    ├── app.py
    └── README.md

If the downloaded Python file is still named <code>ai_gateway_demo.py</code>, either run it directly or rename it to <code>app.py</code>.

## Important note

This application is a presentation and architecture demo. Model outputs, performance, token consumption, costs, policy decisions, audit events, and retention behavior are simulated. It should not be used to evaluate actual provider performance, pricing, security, or regulatory compliance.

---

<div align="center">

### One gateway view. Every AI interaction. Full operational context.

Built as a lightweight demonstration of an AI Gateway operational data layer.

</div>
