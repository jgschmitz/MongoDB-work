import os
import html
from datetime import datetime
from typing import Dict, Any, List

import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import voyageai


load_dotenv()

st.set_page_config(
    page_title="RFP Agent Demo",
    page_icon="🧠",
    layout="wide",
)

# =========================
# CONFIG (NO ENV BS 😄)
# =========================

MONGODB_URI = ""
DB_NAME = "RFP_Demo"

VOYAGE_API_KEY = ""

INDEX_NAME = "vector_index"
EMBED_MODEL = "voyage-4-large"

COLLECTIONS = [
    "knowledge_base",
    "historical_rfp_answers",
    "source_documents"
]

AGENT_RUNS_COLLECTION = "agent_runs"


# =========================
# STYLING
# =========================

def inject_ui() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg0: #0d1022;
            --bg1: #17122d;
            --card: rgba(255,255,255,.10);
            --card2: rgba(255,255,255,.07);
            --stroke: rgba(255,255,255,.14);
            --text: #f8f6ef;
            --muted: rgba(248,246,239,.72);
            --accent: #b892ff;
            --accent2: #4fd4ff;
            --good: #70f0b4;
            --warn: #ffd36e;
            --bad: #ff6b8a;
            --shadow: 0 24px 80px rgba(0,0,0,.30);
            --radius: 24px;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 16% 8%, rgba(184,146,255,.35), transparent 30%),
                radial-gradient(circle at 82% 14%, rgba(79,212,255,.22), transparent 28%),
                radial-gradient(circle at 48% 100%, rgba(255,107,138,.16), transparent 35%),
                linear-gradient(135deg, var(--bg0), var(--bg1));
            color: var(--text);
        }

        [data-testid="stAppViewContainer"] > .main {
            background: transparent;
        }

        [data-testid="stHeader"] {
            background: rgba(0,0,0,0);
        }

        [data-testid="stSidebar"] {
            background: rgba(15, 18, 38, 0.86);
            border-right: 1px solid rgba(255,255,255,.08);
        }

        [data-testid="stSidebar"] * {
            color: var(--text) !important;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        .hero-card {
            border: 1px solid var(--stroke);
            background: var(--card);
            border-radius: 30px;
            padding: 26px 28px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
            margin-bottom: 1.25rem;
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border: 1px solid var(--stroke);
            border-radius: 999px;
            background: rgba(255,255,255,.05);
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 14px;
        }

        .hero-title {
            font-size: clamp(2.4rem, 5vw, 4.5rem);
            line-height: .92;
            letter-spacing: -0.06em;
            font-weight: 900;
            margin: 0 0 .4rem 0;
        }

        .hero-subtitle {
            color: var(--muted);
            font-size: 1.06rem;
            line-height: 1.65;
            margin-bottom: 0;
            max-width: 900px;
        }

        .glass-card {
            border: 1px solid var(--stroke);
            background: var(--card);
            border-radius: 26px;
            padding: 18px 18px 16px 18px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(16px);
            margin-bottom: 1rem;
        }

        .glass-card.tight {
            padding: 14px 16px;
        }

        .section-title {
            font-size: 1.05rem;
            font-weight: 800;
            margin: 0 0 .5rem 0;
            color: var(--text);
        }

        .section-copy {
            color: var(--muted);
            line-height: 1.6;
            margin: 0;
        }

        .step-list {
            margin: .35rem 0 0 0;
            padding-left: 1.1rem;
            color: var(--muted);
        }

        .step-list li {
            margin-bottom: .45rem;
            line-height: 1.45;
        }

        .metric-tile {
            border: 1px solid rgba(255,255,255,.12);
            background: rgba(255,255,255,.06);
            border-radius: 20px;
            padding: 14px 16px;
            min-height: 96px;
        }

        .metric-label {
            color: var(--muted);
            font-size: .78rem;
            text-transform: uppercase;
            letter-spacing: .12em;
            margin-bottom: .35rem;
        }

        .metric-value {
            color: var(--text);
            font-size: 1.35rem;
            font-weight: 800;
            line-height: 1.2;
            word-break: break-word;
        }

        .metric-sub {
            color: var(--muted);
            font-size: .85rem;
            margin-top: .4rem;
        }

        .pill {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.12);
            color: var(--muted);
            font-size: .78rem;
            margin: 0 8px 8px 0;
        }

        .pill.good {
            background: rgba(112,240,180,.12);
            border-color: rgba(112,240,180,.22);
            color: #b9ffd8;
        }

        .pill.warn {
            background: rgba(255,211,110,.14);
            border-color: rgba(255,211,110,.24);
            color: #ffe8a8;
        }

        .pill.bad {
            background: rgba(255,107,138,.12);
            border-color: rgba(255,107,138,.24);
            color: #ffb5c7;
        }

        .result-header {
            font-size: 1.2rem;
            font-weight: 800;
            margin-bottom: .35rem;
        }

        .question-block {
            color: var(--text);
            font-size: 1rem;
            line-height: 1.6;
            margin: .25rem 0 .5rem 0;
        }

        .muted {
            color: var(--muted);
        }

        .subtle-divider {
            height: 1px;
            background: rgba(255,255,255,.09);
            margin: 1rem 0;
        }

        .codeish {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: .9rem;
            color: #efe7ff;
        }

        .source-content {
            border: 1px solid rgba(255,255,255,.10);
            background: rgba(0,0,0,.14);
            border-radius: 18px;
            padding: 14px 15px;
            color: var(--text);
            line-height: 1.6;
        }

        .small-kv {
            color: var(--muted);
            line-height: 1.8;
        }

        .small-kv strong {
            color: var(--text);
        }

        .summary-banner {
            border: 1px solid rgba(112,240,180,.20);
            background: rgba(112,240,180,.10);
            border-radius: 18px;
            padding: 14px 16px;
            color: #d7ffe9;
            margin-bottom: 1rem;
        }

        .past-run {
            border: 1px solid rgba(255,255,255,.10);
            background: rgba(255,255,255,.05);
            border-radius: 22px;
            padding: 16px;
        }

        .past-run-title {
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: .45rem;
        }

        .sidebar-card {
            border: 1px solid rgba(255,255,255,.10);
            background: rgba(255,255,255,.06);
            border-radius: 20px;
            padding: 14px 14px 10px 14px;
            margin-bottom: 1rem;
        }

        .sidebar-label {
            font-size: .78rem;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: .12em;
            margin-bottom: 4px;
        }

        /* Inputs */
        .stTextArea textarea {
            background: rgba(0,0,0,.16) !important;
            color: var(--text) !important;
            border-radius: 22px !important;
            border: 1px solid rgba(255,255,255,.14) !important;
            padding: 16px !important;
        }

        .stTextArea textarea::placeholder {
            color: rgba(248,246,239,.40) !important;
        }

        .stButton > button {
            border-radius: 999px !important;
            border: none !important;
            padding: .8rem 1.2rem !important;
            font-weight: 800 !important;
            color: #140f20 !important;
            background: linear-gradient(135deg, #fff2b8, #b892ff 48%, #4fd4ff) !important;
            box-shadow: 0 10px 24px rgba(0,0,0,.24) !important;
        }

        .stButton > button:hover {
            filter: brightness(1.04);
            transform: translateY(-1px);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background: rgba(255,255,255,.05);
            border-radius: 18px;
            padding: 6px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 14px;
            padding: .7rem 1rem;
            color: var(--muted);
        }

        .stTabs [aria-selected="true"] {
            background: rgba(255,255,255,.10) !important;
            color: var(--text) !important;
        }

        /* Expanders */
        .streamlit-expanderHeader {
            background: rgba(255,255,255,.04);
            border-radius: 16px;
        }

        /* Metric default cleanup */
        [data-testid="metric-container"] {
            background: rgba(255,255,255,.06);
            border: 1px solid rgba(255,255,255,.10);
            padding: 14px;
            border-radius: 18px;
        }

        [data-testid="stMarkdownContainer"] p {
            color: inherit;
        }

        .note {
            color: var(--muted);
            font-size: .92rem;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_tile(label: str, value: str, sub: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-tile">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            {f'<div class="metric-sub">{html.escape(sub)}</div>' if sub else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_signal_pills(signals: List[str]) -> None:
    if not signals:
        st.markdown('<span class="pill">No signals</span>', unsafe_allow_html=True)
        return

    pill_html = []
    for s in signals:
        klass = "pill"
        if s in {"APPROVED", "PRIOR_WIN", "PREVIOUSLY_USED", "POLICY_SOURCE"}:
            klass += " good"
        elif s in {"STALE"}:
            klass += " warn"
        elif s in {"PRIOR_LOSS"}:
            klass += " bad"
        pill_html.append(f'<span class="{klass}">{html.escape(s)}</span>')

    st.markdown("".join(pill_html), unsafe_allow_html=True)


def section_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="section-title">{html.escape(title)}</div>
            <p class="section-copy">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_db():
    if not MONGODB_URI:
        return None
    client = MongoClient(MONGODB_URI)
    return client[DB_NAME]


@st.cache_resource
def get_voyage():
    if not VOYAGE_API_KEY:
        return None
    return voyageai.Client(api_key=VOYAGE_API_KEY)


db = get_db()
vo = get_voyage()


def source_label(name: str) -> str:
    return {
        "knowledge_base": "Knowledge Base",
        "historical_rfp_answers": "Historical RFP Answers",
        "source_documents": "Source Documents",
    }.get(name, name)


def parse_questions(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def check_runtime_readiness() -> None:
    if not MONGODB_URI:
        st.error("MONGODB_URI is missing. Add it to your config.")
        st.stop()

    if not VOYAGE_API_KEY:
        st.error("VOYAGE_API_KEY is missing. Add it to your config.")
        st.stop()

    if db is None:
        st.error("MongoDB client could not be initialized.")
        st.stop()

    if vo is None:
        st.error("Voyage client could not be initialized.")
        st.stop()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def embed_query(text: str) -> List[float]:
    return vo.embed(
        texts=[text],
        model=EMBED_MODEL,
    ).embeddings[0]


def search_collection(name: str, query_vec: List[float], limit: int = 3) -> List[Dict[str, Any]]:
    pipeline = [
        {
            "$vectorSearch": {
                "index": INDEX_NAME,
                "path": "embedding",
                "queryVector": query_vec,
                "numCandidates": 20,
                "limit": limit,
            }
        },
        {
            "$project": {
                "_id": 1,
                "question_text": 1,
                "answer_text": 1,
                "title": 1,
                "chunk_text": 1,
                "review_status": 1,
                "outcome": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    results = list(db[name].aggregate(pipeline))
    for r in results:
        r["source_collection"] = name
        r["_id"] = str(r["_id"])
    return results


def rerank_score(doc: Dict[str, Any]) -> float:
    score = safe_float(doc.get("score", 0))

    if doc.get("review_status") == "approved":
        score += 0.08
    if doc.get("review_status") == "stale":
        score -= 0.08

    if doc.get("outcome") == "won":
        score += 0.08
    if doc.get("outcome") == "used":
        score += 0.03
    if doc.get("outcome") == "lost":
        score -= 0.08

    return score


def explain_signals(doc: Dict[str, Any]) -> List[str]:
    signals = []

    if doc.get("review_status") == "approved":
        signals.append("APPROVED")
    if doc.get("review_status") == "stale":
        signals.append("STALE")
    if doc.get("outcome") == "won":
        signals.append("PRIOR_WIN")
    if doc.get("outcome") == "used":
        signals.append("PREVIOUSLY_USED")
    if doc.get("outcome") == "lost":
        signals.append("PRIOR_LOSS")
    if doc.get("source_collection") == "source_documents":
        signals.append("POLICY_SOURCE")

    return signals


def run_search(query: str, per_collection_limit: int = 3) -> List[Dict[str, Any]]:
    query_vec = embed_query(query)

    all_results: List[Dict[str, Any]] = []
    for name in COLLECTIONS:
        all_results.extend(search_collection(name, query_vec, per_collection_limit))

    for r in all_results:
        r["final_score"] = rerank_score(r)
        r["signals"] = explain_signals(r)

    return sorted(all_results, key=lambda x: x["final_score"], reverse=True)


def classify_question(question: str) -> Dict[str, Any]:
    q = question.lower()

    if any(term in q for term in ["hipaa", "soc2", "iso", "compliance", "audit"]):
        category = "COMPLIANCE"
        route = "sme_team_compliance"
    elif any(term in q for term in ["security", "encryption", "access control", "incident"]):
        category = "SECURITY"
        route = "sme_team_security"
    elif any(term in q for term in ["sla", "uptime", "availability", "disaster recovery"]):
        category = "PLATFORM"
        route = "sme_team_platform"
    elif any(term in q for term in ["pricing", "cost", "commercial", "license"]):
        category = "COMMERCIAL"
        route = "sme_team_commercial"
    else:
        category = "GENERAL"
        route = "sme_team_general"

    return {
        "category": category,
        "suggested_route": route,
    }


def assess_result(top_result: Dict[str, Any]) -> Dict[str, Any]:
    score = safe_float(top_result.get("final_score", 0))
    signals = top_result.get("signals", [])

    risk_flags: List[str] = []

    if "STALE" in signals:
        risk_flags.append("Content may be stale")
    if "PRIOR_LOSS" in signals:
        risk_flags.append("Based on prior losing content")
    if top_result.get("source_collection") == "source_documents":
        risk_flags.append("Grounded in source policy document")

    if score >= 0.90:
        confidence = "HIGH"
    elif score >= 0.75:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "confidence_band": confidence,
        "risk_flags": risk_flags,
    }


def build_trace(
    question: str,
    classification: Dict[str, Any],
    ranked: List[Dict[str, Any]],
    assessment: Dict[str, Any],
) -> List[Dict[str, Any]]:
    top = ranked[0] if ranked else {}
    now = datetime.utcnow().isoformat()

    return [
        {
            "stage": "QUESTION_CLASSIFICATION",
            "timestamp": now,
            "result": {
                "question": question,
                **classification,
            },
        },
        {
            "stage": "ANSWER_SELECTION",
            "timestamp": now,
            "result": {
                "selected_source": top.get("source_collection"),
                "selected_score": top.get("final_score"),
                "vector_score": top.get("score"),
                "signals": top.get("signals", []),
            },
        },
        {
            "stage": "RISK_ASSESSMENT",
            "timestamp": now,
            "result": assessment,
        },
    ]


def save_agent_run(
    question: str,
    classification: Dict[str, Any],
    ranked: List[Dict[str, Any]],
    assessment: Dict[str, Any],
    trace: List[Dict[str, Any]],
) -> str:
    top = ranked[0] if ranked else {}

    record = {
        "question": question,
        "agent_type": "RFP_SELECTION_AGENT",
        "classification": classification,
        "selected_result": top,
        "top_results": ranked[:5],
        "assessment": assessment,
        "trace": trace,
        "created_at": datetime.utcnow(),
    }

    result = db[AGENT_RUNS_COLLECTION].insert_one(record)
    return str(result.inserted_id)


def run_agent_pipeline(question: str, per_collection_limit: int) -> Dict[str, Any]:
    classification = classify_question(question)
    ranked = run_search(question, per_collection_limit=per_collection_limit)

    if not ranked:
        return {
            "success": False,
            "question": question,
            "message": "No ranked results returned from search engine.",
        }

    assessment = assess_result(ranked[0])
    trace = build_trace(question, classification, ranked, assessment)
    run_id = save_agent_run(question, classification, ranked, assessment, trace)

    return {
        "success": True,
        "question": question,
        "run_id": run_id,
        "classification": classification,
        "ranked": ranked,
        "assessment": assessment,
        "trace": trace,
    }


def get_past_runs(limit: int = 10) -> List[Dict[str, Any]]:
    docs = list(
        db[AGENT_RUNS_COLLECTION]
        .find(
            {},
            {
                "question": 1,
                "classification": 1,
                "assessment": 1,
                "selected_result.source_collection": 1,
                "selected_result.final_score": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(limit)
    )

    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


def render_result_card(idx: int, result: Dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="result-header">Question #{idx}</div>
            <div class="question-block"><strong>Question:</strong> {html.escape(result.get('question', ''))}</div>
        """,
        unsafe_allow_html=True,
    )

    if not result["success"]:
        st.error(result["message"])
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.caption(f"Saved Run ID: {result['run_id']}")

    ranked = result["ranked"]
    top = ranked[0]
    classification = result["classification"]
    assessment = result["assessment"]
    trace = result["trace"]

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_tile("Category", classification["category"])
    with c2:
        metric_tile("Suggested Route", classification["suggested_route"])
    with c3:
        metric_tile("Confidence", assessment["confidence_band"])

    st.markdown('<div class="subtle-divider"></div>', unsafe_allow_html=True)

    top_col, risk_col = st.columns([2, 1], gap="large")

    with top_col:
        st.markdown('<div class="section-title">Top Selected Result</div>', unsafe_allow_html=True)

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            metric_tile("Source", source_label(top.get("source_collection")))
        with sc2:
            metric_tile("Final Score", f"{safe_float(top.get('final_score')):.4f}")
        with sc3:
            metric_tile("Vector Score", f"{safe_float(top.get('score')):.4f}")

        st.markdown('<div style="margin-top: .65rem;"></div>', unsafe_allow_html=True)
        render_signal_pills(top.get("signals", []))

        details = []
        if top.get("review_status"):
            details.append(f"<strong>Status:</strong> {html.escape(str(top['review_status']))}")
        if top.get("outcome"):
            details.append(f"<strong>Outcome:</strong> {html.escape(str(top['outcome']))}")

        if details:
            st.markdown(
                f'<div class="small-kv">{"<br>".join(details)}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div style="height: .5rem;"></div>', unsafe_allow_html=True)

        if top.get("source_collection") == "source_documents":
            title = top.get("title")
            if title:
                st.markdown(f"**Title:** {title}")
            content = top.get("chunk_text") or ""
        else:
            if top.get("question_text"):
                st.markdown(f"**Matched Question:** {top.get('question_text')}")
            content = top.get("answer_text") or ""

        st.markdown(
            f'<div class="source-content">{html.escape(str(content))}</div>',
            unsafe_allow_html=True,
        )

    with risk_col:
        st.markdown('<div class="section-title">Risk Assessment</div>', unsafe_allow_html=True)
        metric_tile("Confidence Band", assessment.get("confidence_band", "N/A"))

        risk_flags = assessment.get("risk_flags", [])
        st.markdown('<div style="height: .5rem;"></div>', unsafe_allow_html=True)
        if risk_flags:
            for flag in risk_flags:
                st.markdown(f'<span class="pill warn">{html.escape(flag)}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="pill good">No major risk flags detected</span>', unsafe_allow_html=True)

    with st.expander("View Agent Trace", expanded=False):
        for step in trace:
            st.markdown(
                f"""
                <div class="glass-card tight">
                    <div class="section-title">{html.escape(step['stage'])}</div>
                    <div class="note"><strong>Timestamp:</strong> {html.escape(step['timestamp'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.json(step["result"])

    with st.expander("View Ranked Results", expanded=False):
        for i, r in enumerate(ranked, start=1):
            st.markdown(
                f"""
                <div class="glass-card tight">
                    <div class="section-title">Result #{i}</div>
                    <div class="small-kv">
                        <strong>Source:</strong> {html.escape(source_label(r.get('source_collection')))}<br>
                        <strong>Final Score:</strong> {safe_float(r.get('final_score')):.4f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_signal_pills(r.get("signals", []))

            if r.get("source_collection") == "source_documents":
                if r.get("title"):
                    st.markdown(f"**Title:** {r.get('title')}")
                content = r.get("chunk_text") or ""
            else:
                if r.get("question_text"):
                    st.markdown(f"**Matched Question:** {r.get('question_text')}")
                content = r.get("answer_text") or ""

            st.markdown(
                f'<div class="source-content">{html.escape(str(content))}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# APP
# =========================

inject_ui()
check_runtime_readiness()

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-eyebrow">🧠 Agentic answer selection · Atlas trace persistence</div>
        <h1 class="hero-title">RFP QA<br/>Agent Demo</h1>
        <p class="hero-subtitle">
            Paste one or more RFP questions and watch the agent classify, search across collections,
            rerank candidates, assess confidence and risk, and save the full decision trace in Atlas.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-label">Control Panel</div>
            <div class="section-title" style="font-size:1rem;">Agent Settings</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    per_collection_limit = st.slider(
        "Results per collection",
        min_value=1,
        max_value=5,
        value=3,
    )

    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-label">Environment</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(f"**DB Name:** `{DB_NAME}`")
    st.write(f"**Saved Runs Collection:** `{AGENT_RUNS_COLLECTION}`")
    st.write(f"**Atlas Vector Index:** `{INDEX_NAME}`")
    st.write(f"**Embedding Model:** `{EMBED_MODEL}`")

    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-label">History</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    past_limit = st.slider(
        "Show recent runs",
        min_value=3,
        max_value=25,
        value=10,
    )

main_left, main_right = st.columns([2.1, 1], gap="large")

with main_left:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">RFP Questions</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-copy">One per line. The agent will process each question independently and persist the trace.</p>',
        unsafe_allow_html=True,
    )

    questions_raw = st.text_area(
        "RFP Questions (one per line)",
        value="",
        height=190,
        placeholder="Paste one or more RFP questions, one per line...",
        label_visibility="collapsed",
    )

    run_agent = st.button("Analyze Questions →", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with main_right:
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-title">How this agent works</div>
            <ol class="step-list">
                <li>Classifies the incoming question</li>
                <li>Runs vector search across all configured collections</li>
                <li>Reranks using approval and outcome signals</li>
                <li>Assesses confidence and risk</li>
                <li>Saves the full trace in Atlas</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

    r1, r2 = st.columns(2)
    with r1:
        metric_tile("Collections", len(COLLECTIONS), "Search surfaces")
    with r2:
        metric_tile("Model", EMBED_MODEL, "Embedding engine")

if run_agent:
    questions = parse_questions(questions_raw)

    if not questions:
        st.warning("Please enter at least one question.")
    else:
        with st.spinner("Running agent pipeline..."):
            st.session_state.analysis_results = [
                run_agent_pipeline(question, per_collection_limit)
                for question in questions
            ]

tab1, tab2 = st.tabs(["Analysis Results", "View Past Runs"])

with tab1:
    results = st.session_state.analysis_results

    if results:
        success_count = sum(1 for r in results if r.get("success"))
        st.markdown(
            f"""
            <div class="summary-banner">
                Processed <strong>{success_count}</strong> of <strong>{len(results)}</strong> questions successfully.
            </div>
            """,
            unsafe_allow_html=True,
        )

        for idx, result in enumerate(results, start=1):
            render_result_card(idx, result)
    else:
        section_card(
            "No analysis yet",
            "Paste one or more RFP questions above and click <strong>Analyze Questions</strong> to see the agent pipeline in action.",
        )

with tab2:
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-title">Recent Agent Runs</div>
            <p class="section-copy">These are the traces already saved in Atlas.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    runs = get_past_runs(limit=past_limit)

    if not runs:
        st.info("No past runs found yet.")
    else:
        for run in runs:
            classification = run.get("classification", {})
            assessment = run.get("assessment", {})
            selected = run.get("selected_result", {})

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="past-run-title">Run ID: <span class="codeish">{html.escape(run['_id'])}</span></div>
                <div class="note"><strong>Created At:</strong> {html.escape(str(run.get('created_at')))}</div>
                <div class="question-block"><strong>Question:</strong> {html.escape(run.get('question', ''))}</div>
                """,
                unsafe_allow_html=True,
            )

            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                metric_tile("Category", classification.get("category", "N/A"))
            with pc2:
                metric_tile("Route", classification.get("suggested_route", "N/A"))
            with pc3:
                metric_tile("Confidence", assessment.get("confidence_band", "N/A"))

            st.markdown('<div style="height: .7rem;"></div>', unsafe_allow_html=True)

            sc1, sc2 = st.columns(2)
            with sc1:
                metric_tile("Selected Source", source_label(selected.get("source_collection")))
            with sc2:
                metric_tile("Top Final Score", f"{safe_float(selected.get('final_score')):.4f}")

            st.markdown("</div>", unsafe_allow_html=True)
