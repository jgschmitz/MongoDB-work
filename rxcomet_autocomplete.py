# rxcomet_autocomplete.py
import textwrap, html
from typing import List, Dict, Any, Optional
import streamlit as st
from pymongo import MongoClient
from voyageai import Client as VoyageClient

# ========= EDIT THESE =========
MONGO_URI  = ""              # e.g. mongodb+srv://user:pass@cluster/...
VOYAGE_API_KEY = ""     # used only to embed the QUERY
DB_NAME    = "rxcomet_autofill_demo"
COLL_NAME  = "historical_answers_demo"
VS_INDEX   = "vs_rx_answers_demo"
EMBED_PATH = "embedding"
DIM        = 2048                          # must match your stored vectors & index
TOP_K      = 6
NUM_CANDIDATES = 80
# ==============================

# Clients
mongo = MongoClient(MONGO_URI)
coll  = mongo[DB_NAME][COLL_NAME]
vo    = VoyageClient(api_key=VOYAGE_API_KEY)

# UI
st.set_page_config(page_title="RxComet • Predictive Auto-Fill", page_icon="🧩", layout="centered")
st.title("🧩 RxComet — Predictive Auto-Fill (Vector Autocomplete)")
st.caption("Type an answer; suggestions come from similar historical answers via Atlas Vector Search.")

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    # simple distinct lists (fine for demo-size corpora)
    try:
        template_ids = sorted([d["_id"] for d in coll.aggregate([{"$group": {"_id": "$template_id"}}])])
    except Exception:
        template_ids = ["benefit_eligibility_v3"]
    try:
        question_ids = sorted([d["_id"] for d in coll.aggregate([{"$group": {"_id": "$question_id"}}])])
    except Exception:
        question_ids = ["prior_auth_policy"]
    try:
        custs = ["(any)"] + sorted([d["_id"] for d in coll.aggregate([{"$group": {"_id": "$customer"}}]) if d["_id"]])
    except Exception:
        custs = ["(any)"]

    selected_template = st.selectbox("Template", template_ids, index=0)
    selected_question = st.selectbox("Question", question_ids, index=0)
    selected_customer = st.selectbox("Customer", custs, index=0)

# Manual query embedding (because we're not using auto-embed)
def embed_query(q: str) -> List[float]:
    r = vo.contextualized_embed(
        inputs=[[q]],
        model="voyage-context-3",
        input_type="query",
        output_dimension=DIM,
        output_dtype="float"
    )
    return r.results[0].embeddings[0]

# Vector search
def vector_suggest(query_text: str) -> List[Dict[str, Any]]:
    qv = embed_query(query_text)
    match = {"template_id": selected_template, "question_id": selected_question}
    if selected_customer != "(any)":
        match["customer"] = selected_customer

    pipeline = [
        {"$vectorSearch": {
            "index": VS_INDEX,
            "path": EMBED_PATH,
            "queryVector": qv,
            "numCandidates": NUM_CANDIDATES,
            "limit": TOP_K
        }},
        {"$match": match},
        {"$project": {
            "_id": 0,
            "answer_text": 1,
            "customer": 1,
            "template_id": 1,
            "question_id": 1,
            "score": {"$meta": "vectorSearchScore"}
        }}
    ]
    return list(coll.aggregate(pipeline))

# Session state for accepted answers
if "accepted" not in st.session_state:
    st.session_state.accepted = {}

st.subheader("Field")
st.write(f"**Template:** `{selected_template}`  •  **Question:** `{selected_question}`  •  **Customer:** `{selected_customer}`")

answer_text = st.text_input(
    "Start typing the answer…",
    key="answer_input",
    placeholder="e.g., Prior authorization is required for specialty drugs…"
)

# Suggestions
suggestions = []
if answer_text.strip():
    try:
        suggestions = vector_suggest(answer_text.strip())
    except Exception as e:
        st.error(f"Vector search failed: {e}")

st.markdown("#### Suggestions")
if suggestions:
    for i, s in enumerate(suggestions, 1):
        txt   = s.get("answer_text", "")
        cust  = s.get("customer", "—")
        score = s.get("score", None)
        display = textwrap.shorten(txt, width=90, placeholder="…")
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            if st.button(f"💡 {display}", key=f"sugg_{i}", use_container_width=True):
                st.session_state.answer_input = txt  # autofill the input
                st.experimental_rerun()
        with c2:
            if isinstance(score, (int, float)):
                st.caption(f"vs: {score:.3f}")
            st.caption(f"Cust: {cust}")
else:
    st.info("Start typing to see suggestions from similar historical answers.")

# Accept / Clear
colA, colB = st.columns(2)
if colA.button("✅ Accept Answer"):
    key = (selected_template, selected_question, selected_customer)
    st.session_state.accepted[key] = st.session_state.get("answer_input", "")
    st.success("Answer accepted for this field.")
if colB.button("🧹 Clear"):
    st.session_state.answer_input = ""
    st.experimental_rerun()

# Show accepted values this session
if st.session_state.accepted:
    st.markdown("### 📄 Accepted Field Values (session)")
    for (tpl, qid, cust), ans in st.session_state.accepted.items():
        st.markdown(f"- **{tpl} / {qid} / {cust}** → {html.escape(ans)}")

st.caption("Stage 1: Atlas Vector Search over manual 2048-dim embeddings. (No reranker, no auto-embed.)")
