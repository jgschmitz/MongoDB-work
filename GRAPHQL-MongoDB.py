import html
import json
import time

import pandas as pd
import streamlit as st
from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError
from pymongo.operations import SearchIndexModel


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Healthcare Semantic Ontology",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# MONGODB ATLAS
#
# The Atlas URI is the only value you provide.
# ============================================================

MONGODB_URI = ""

DATABASE_NAME = "healthcare_ontology_demo"
HEALTHCARE_COLLECTION = "healthcare"
ONTOLOGY_COLLECTION = "concepts"

VECTOR_INDEX_NAME = "healthcare_autoembed_v1"
EMBEDDING_MODEL = "voyage-4"

client = (
    MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    if MONGODB_URI
    else None
)

db = client[DATABASE_NAME] if client else None

healthcare_collection = (
    db[HEALTHCARE_COLLECTION]
    if db is not None
    else None
)

ontology_collection = (
    db[ONTOLOGY_COLLECTION]
    if db is not None
    else None
)


# ============================================================
# ONTOLOGY SEED DATA
# ============================================================

ONTOLOGY_ROWS = [
    (
        "healthcare_provider",
        "PROVIDER",
        "Healthcare Provider",
        "root",
        None,
        "A person or organization that delivers healthcare services.",
        ["medical provider", "care provider"],
    ),
    (
        "individual_provider",
        "INDIVIDUAL",
        "Individual Provider",
        "provider_category",
        "healthcare_provider",
        "An individual qualified to provide healthcare services.",
        ["individual practitioner", "clinician"],
    ),
    (
        "organization_provider",
        "ORGANIZATION",
        "Organization Provider",
        "provider_category",
        "healthcare_provider",
        "An organization that provides healthcare services.",
        ["healthcare organization", "facility provider"],
    ),
    (
        "physician",
        "PHYSICIAN",
        "Physician",
        "profession",
        "individual_provider",
        "A medical professional licensed to practice medicine.",
        ["doctor", "medical doctor"],
    ),
    (
        "advanced_practice",
        "ADVANCED_PRACTICE",
        "Advanced Practice Provider",
        "profession",
        "individual_provider",
        "A clinician with advanced education and clinical responsibilities.",
        ["APP", "advanced practice clinician"],
    ),
    (
        "nurse_practitioner",
        "NP",
        "Nurse Practitioner",
        "specialty",
        "advanced_practice",
        "An advanced practice registered nurse providing clinical care.",
        ["NP", "advanced practice nurse"],
    ),
    (
        "physician_assistant",
        "PA",
        "Physician Assistant",
        "specialty",
        "advanced_practice",
        "A licensed clinician who practices medicine collaboratively.",
        ["PA", "physician associate"],
    ),
    (
        "primary_care",
        "PRIMARY_CARE",
        "Primary Care",
        "specialty_group",
        "physician",
        "First-contact and continuing care for general health needs.",
        ["general medicine", "primary medicine"],
    ),
    (
        "family_medicine",
        "207Q00000X",
        "Family Medicine",
        "specialty",
        "primary_care",
        "Comprehensive care for individuals and families across all ages.",
        ["family practice", "family doctor"],
    ),
    (
        "internal_medicine",
        "207R00000X",
        "Internal Medicine",
        "specialty",
        "primary_care",
        "Prevention, diagnosis, and treatment of adult diseases.",
        ["internist", "adult medicine"],
    ),
    (
        "pediatrics",
        "208000000X",
        "Pediatrics",
        "specialty",
        "primary_care",
        "Medical care for infants, children, and adolescents.",
        ["pediatric medicine", "children's doctor"],
    ),
    (
        "cardiology",
        "CARDIOLOGY",
        "Cardiology",
        "specialty_group",
        "internal_medicine",
        "Diagnosis and treatment of diseases of the heart and circulation.",
        ["heart medicine", "cardiovascular medicine"],
    ),
    (
        "cardiovascular_disease",
        "207RC0000X",
        "Cardiovascular Disease",
        "specialty",
        "cardiology",
        "Management of diseases affecting the heart and blood vessels.",
        ["cardiologist", "heart specialist"],
    ),
    (
        "interventional_cardiology",
        "207RI0011X",
        "Interventional Cardiology",
        "subspecialty",
        "cardiovascular_disease",
        "Catheter-based diagnosis and treatment of cardiovascular disease.",
        [
            "interventional cardiologist",
            "heart catheterization specialist",
        ],
    ),
    (
        "cardiac_electrophysiology",
        "207RC0001X",
        "Clinical Cardiac Electrophysiology",
        "subspecialty",
        "cardiovascular_disease",
        "Diagnosis and treatment of abnormal heart rhythms.",
        ["electrophysiologist", "heart rhythm specialist"],
    ),
    (
        "endocrinology",
        "207RE0101X",
        "Endocrinology, Diabetes and Metabolism",
        "subspecialty",
        "internal_medicine",
        "Treatment of hormonal, metabolic, and endocrine disorders.",
        ["endocrinologist", "diabetes specialist"],
    ),
    (
        "gastroenterology",
        "207RG0100X",
        "Gastroenterology",
        "subspecialty",
        "internal_medicine",
        "Diagnosis and treatment of digestive system disorders.",
        ["gastroenterologist", "digestive specialist"],
    ),
    (
        "pulmonology",
        "207RP1001X",
        "Pulmonary Disease",
        "subspecialty",
        "internal_medicine",
        "Diagnosis and treatment of respiratory system diseases.",
        ["pulmonologist", "lung specialist"],
    ),
    (
        "surgery",
        "SURGERY",
        "Surgery",
        "specialty_group",
        "physician",
        "Medical treatment involving operative procedures.",
        ["surgical medicine", "surgeon"],
    ),
    (
        "general_surgery",
        "208600000X",
        "General Surgery",
        "specialty",
        "surgery",
        "Surgical treatment involving abdominal and other organ systems.",
        ["general surgeon"],
    ),
    (
        "vascular_surgery",
        "2086S0129X",
        "Vascular Surgery",
        "subspecialty",
        "general_surgery",
        "Surgical treatment of diseases of the vascular system.",
        ["vascular surgeon", "blood vessel surgeon"],
    ),
    (
        "neurological_surgery",
        "207T00000X",
        "Neurological Surgery",
        "specialty",
        "surgery",
        "Surgical treatment of disorders affecting the nervous system.",
        ["neurosurgery", "neurosurgeon", "brain surgeon"],
    ),
    (
        "orthopedic_surgery",
        "207X00000X",
        "Orthopaedic Surgery",
        "specialty",
        "surgery",
        "Surgical treatment of musculoskeletal conditions.",
        ["orthopedic surgeon", "bone surgeon"],
    ),
    (
        "hospital",
        "282N00000X",
        "General Acute Care Hospital",
        "facility",
        "organization_provider",
        "A facility providing inpatient acute medical care.",
        ["acute care hospital", "general hospital"],
    ),
    (
        "clinic",
        "261Q00000X",
        "Clinic or Center",
        "facility_group",
        "organization_provider",
        "An organization delivering outpatient healthcare services.",
        ["medical clinic", "outpatient center"],
    ),
    (
        "ambulatory_surgical_center",
        "261QA1903X",
        "Ambulatory Surgical Center",
        "facility",
        "clinic",
        "A facility providing same-day surgical care.",
        ["ASC", "outpatient surgery center"],
    ),
    (
        "urgent_care",
        "261QU0200X",
        "Urgent Care",
        "facility",
        "clinic",
        "A facility providing immediate non-emergency treatment.",
        ["walk-in clinic", "immediate care"],
    ),
]


def build_ontology_documents():
    fields = [
        "_id",
        "code",
        "name",
        "conceptType",
        "parentId",
        "description",
        "synonyms",
    ]

    return [
        dict(zip(fields, row))
        for row in ONTOLOGY_ROWS
    ]


# ============================================================
# SEMANTIC SEARCH DOCUMENTS
#
# These are deliberately phrased like user requests.
# Atlas automatically embeds searchText.
# ============================================================

HEALTHCARE_DOCUMENTS = [
    {
        "_id": "search-001",
        "conceptId": "interventional_cardiology",
        "title": "Heart catheterization and stent procedures",
        "searchText": (
            "Find a doctor who performs heart catheterization, "
            "angioplasty, coronary intervention, or places cardiac stents."
        ),
    },
    {
        "_id": "search-002",
        "conceptId": "cardiac_electrophysiology",
        "title": "Abnormal heart rhythm treatment",
        "searchText": (
            "Find a heart rhythm specialist who treats arrhythmia, "
            "atrial fibrillation, or performs cardiac ablation."
        ),
    },
    {
        "_id": "search-003",
        "conceptId": "cardiovascular_disease",
        "title": "General heart disease care",
        "searchText": (
            "Find a cardiologist for chest pain, coronary artery disease, "
            "high blood pressure, or general heart problems."
        ),
    },
    {
        "_id": "search-004",
        "conceptId": "endocrinology",
        "title": "Diabetes and hormone care",
        "searchText": (
            "Find a diabetes doctor or hormone specialist for thyroid, "
            "metabolism, insulin, or endocrine problems."
        ),
    },
    {
        "_id": "search-005",
        "conceptId": "gastroenterology",
        "title": "Digestive system care",
        "searchText": (
            "Find a digestive specialist for stomach pain, reflux, "
            "intestinal problems, liver disease, or colonoscopy."
        ),
    },
    {
        "_id": "search-006",
        "conceptId": "pulmonology",
        "title": "Lung and breathing care",
        "searchText": (
            "Find a lung doctor for asthma, COPD, breathing difficulty, "
            "sleep-related breathing problems, or pulmonary disease."
        ),
    },
    {
        "_id": "search-007",
        "conceptId": "family_medicine",
        "title": "Family primary care",
        "searchText": (
            "Find a regular family doctor for checkups, preventive care, "
            "common illnesses, and ongoing primary care."
        ),
    },
    {
        "_id": "search-008",
        "conceptId": "internal_medicine",
        "title": "Adult primary care",
        "searchText": (
            "Find an adult medicine doctor or internist for general "
            "medical care and chronic health conditions."
        ),
    },
    {
        "_id": "search-009",
        "conceptId": "pediatrics",
        "title": "Medical care for children",
        "searchText": (
            "Find a doctor for my child, infant, teenager, vaccinations, "
            "well-child visits, or childhood illness."
        ),
    },
    {
        "_id": "search-010",
        "conceptId": "vascular_surgery",
        "title": "Blood vessel surgery",
        "searchText": (
            "Find a surgeon for blocked arteries, vascular disease, "
            "aneurysm, circulation problems, or blood vessel surgery."
        ),
    },
    {
        "_id": "search-011",
        "conceptId": "neurological_surgery",
        "title": "Brain and spine surgery",
        "searchText": (
            "Find a brain or spine surgeon for a neurological condition, "
            "brain tumor, spinal compression, or neurosurgery."
        ),
    },
    {
        "_id": "search-012",
        "conceptId": "orthopedic_surgery",
        "title": "Bone and joint surgery",
        "searchText": (
            "Find a bone or joint surgeon for knee, hip, shoulder, "
            "fracture, arthritis, or musculoskeletal surgery."
        ),
    },
    {
        "_id": "search-013",
        "conceptId": "nurse_practitioner",
        "title": "Nurse practitioner care",
        "searchText": (
            "Find an advanced practice nurse or nurse practitioner "
            "for routine clinical care."
        ),
    },
    {
        "_id": "search-014",
        "conceptId": "physician_assistant",
        "title": "Physician assistant care",
        "searchText": (
            "Find a physician assistant or physician associate "
            "for evaluation and treatment."
        ),
    },
    {
        "_id": "search-015",
        "conceptId": "hospital",
        "title": "Acute inpatient hospital",
        "searchText": (
            "Find a general hospital providing acute inpatient "
            "medical and surgical care."
        ),
    },
    {
        "_id": "search-016",
        "conceptId": "ambulatory_surgical_center",
        "title": "Same-day surgery center",
        "searchText": (
            "Find an outpatient surgery center or ambulatory surgical "
            "facility for a same-day procedure."
        ),
    },
    {
        "_id": "search-017",
        "conceptId": "urgent_care",
        "title": "Immediate walk-in treatment",
        "searchText": (
            "Find a walk-in clinic for an illness or injury that needs "
            "immediate treatment but is not an emergency."
        ),
    },
]


# ============================================================
# SESSION STATE
# ============================================================

if "logs" not in st.session_state:
    st.session_state.logs = [
        "[BOOT] INFO  app=healthcare_semantic_ontology",
        f"[BOOT] INFO  database={DATABASE_NAME}",
        f"[BOOT] INFO  vector_source={HEALTHCARE_COLLECTION}",
        f"[BOOT] INFO  ontology={ONTOLOGY_COLLECTION}",
        "[BOOT] READY waiting for demo action...",
    ]

if "last_action" not in st.session_state:
    st.session_state.last_action = "READY"

if "last_latency" not in st.session_state:
    st.session_state.last_latency = None

if "query_text" not in st.session_state:
    st.session_state.query_text = (
        "I need a doctor who performs heart catheterization"
    )

if "semantic_results" not in st.session_state:
    st.session_state.semantic_results = []

if "matched_concept_id" not in st.session_state:
    st.session_state.matched_concept_id = None


def add_log(message):
    stamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{stamp}] {message}")
    st.session_state.logs = st.session_state.logs[-20:]


# ============================================================
# ATLAS OPERATIONS
# ============================================================

def atlas_status():
    if client is None:
        return False, "MONGODB_URI NOT CONFIGURED"

    try:
        client.admin.command("ping")
        return True, "ATLAS CONNECTED"
    except Exception as exc:
        return False, str(exc)


def collection_count(collection):
    if collection is None:
        return 0

    try:
        return collection.count_documents({})
    except PyMongoError:
        return 0


def get_vector_index_status():
    if healthcare_collection is None:
        return {
            "exists": False,
            "ready": False,
            "status": "NOT CONFIGURED",
        }

    try:
        indexes = list(
            healthcare_collection.list_search_indexes()
        )

        for index in indexes:
            if index.get("name") == VECTOR_INDEX_NAME:
                status = index.get("status", "UNKNOWN")
                queryable = index.get("queryable", False)

                return {
                    "exists": True,
                    "ready": bool(queryable),
                    "status": status,
                }

        return {
            "exists": False,
            "ready": False,
            "status": "NOT CREATED",
        }

    except PyMongoError as exc:
        return {
            "exists": False,
            "ready": False,
            "status": f"UNAVAILABLE: {exc}",
        }


def create_auto_embedding_index():
    current_status = get_vector_index_status()

    if current_status["exists"]:
        add_log(
            f"INDEX {VECTOR_INDEX_NAME} already exists "
            f"status={current_status['status']}"
        )
        return

    model = SearchIndexModel(
        definition={
            "fields": [
                {
                    "type": "autoEmbed",
                    "modality": "text",
                    "path": "searchText",
                    "model": EMBEDDING_MODEL,
                }
            ]
        },
        name=VECTOR_INDEX_NAME,
        type="vectorSearch",
    )

    healthcare_collection.create_search_index(
        model=model
    )

    add_log(
        f"INDEX created={VECTOR_INDEX_NAME} "
        f"model={EMBEDDING_MODEL}"
    )
    add_log(
        "INDEX asynchronous build started"
    )


def seed_demo():
    if (
        healthcare_collection is None
        or ontology_collection is None
    ):
        add_log("ERROR Atlas connection not configured")
        return False

    started = time.perf_counter()

    try:
        ontology_documents = (
            build_ontology_documents()
        )

        ontology_collection.delete_many({})
        healthcare_collection.delete_many({})

        ontology_collection.insert_many(
            ontology_documents,
            ordered=False,
        )

        healthcare_collection.insert_many(
            HEALTHCARE_DOCUMENTS,
            ordered=False,
        )

        ontology_collection.create_index(
            [("parentId", ASCENDING)]
        )
        ontology_collection.create_index(
            [("name", ASCENDING)]
        )
        ontology_collection.create_index(
            [("code", ASCENDING)]
        )

        healthcare_collection.create_index(
            [("conceptId", ASCENDING)]
        )

        add_log(
            f"LOAD ontology documents="
            f"{len(ontology_documents)}"
        )
        add_log(
            f"LOAD healthcare documents="
            f"{len(HEALTHCARE_DOCUMENTS)}"
        )

        create_auto_embedding_index()

        elapsed = time.perf_counter() - started

        st.session_state.last_action = (
            "SEED DATA + CREATE VECTOR INDEX"
        )
        st.session_state.last_latency = elapsed
        st.session_state.semantic_results = []
        st.session_state.matched_concept_id = None

        add_log(
            f"OK seed completed latency={elapsed:.3f}s"
        )

        return True

    except PyMongoError as exc:
        add_log(f"ERROR seed failed: {exc}")
        st.error(f"Seed failed: {exc}")
        return False


def reset_demo():
    if (
        healthcare_collection is None
        or ontology_collection is None
    ):
        return False

    started = time.perf_counter()

    try:
        ontology_collection.delete_many({})
        healthcare_collection.delete_many({})

        elapsed = time.perf_counter() - started

        st.session_state.semantic_results = []
        st.session_state.matched_concept_id = None
        st.session_state.last_action = "RESET DATA"
        st.session_state.last_latency = elapsed

        add_log(
            f"OK reset completed latency={elapsed:.3f}s"
        )

        return True

    except PyMongoError as exc:
        add_log(f"ERROR reset failed: {exc}")
        return False


# ============================================================
# TWO-STEP QUERY PIPELINES
# ============================================================

def vector_search_pipeline(query_text):
    return [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "searchText",
                "query": {
                    "text": query_text,
                },
                "numCandidates": 50,
                "limit": 5,
            }
        },
        {
            "$project": {
                "_id": 1,
                "conceptId": 1,
                "title": 1,
                "searchText": 1,
                "score": {
                    "$meta": "vectorSearchScore"
                },
            }
        },
    ]


def run_vector_search(query_text):
    pipeline = vector_search_pipeline(
        query_text
    )

    started = time.perf_counter()

    results = list(
        healthcare_collection.aggregate(pipeline)
    )

    elapsed = time.perf_counter() - started

    st.session_state.last_action = (
        "VECTOR SEARCH"
    )
    st.session_state.last_latency = elapsed

    add_log(
        f"VECTOR query={query_text!r}"
    )
    add_log(
        f"VECTOR matches={len(results)} "
        f"latency={elapsed:.3f}s"
    )

    return results


def ancestor_pipeline(concept_id):
    return [
        {
            "$match": {
                "_id": concept_id,
            }
        },
        {
            "$graphLookup": {
                "from": ONTOLOGY_COLLECTION,
                "startWith": "$parentId",
                "connectFromField": "parentId",
                "connectToField": "_id",
                "as": "ancestors",
                "depthField": "traversalDepth",
            }
        },
        {
            "$project": {
                "_id": 1,
                "code": 1,
                "name": 1,
                "conceptType": 1,
                "parentId": 1,
                "description": 1,
                "synonyms": 1,
                "ancestors": 1,
            }
        },
    ]


def descendant_pipeline(concept_id):
    return [
        {
            "$match": {
                "_id": concept_id,
            }
        },
        {
            "$graphLookup": {
                "from": ONTOLOGY_COLLECTION,
                "startWith": "$_id",
                "connectFromField": "_id",
                "connectToField": "parentId",
                "as": "descendants",
                "depthField": "traversalDepth",
            }
        },
    ]


def get_ontology_context(concept_id):
    started = time.perf_counter()

    ancestor_results = list(
        ontology_collection.aggregate(
            ancestor_pipeline(concept_id)
        )
    )

    descendant_results = list(
        ontology_collection.aggregate(
            descendant_pipeline(concept_id)
        )
    )

    elapsed = time.perf_counter() - started

    concept = (
        ancestor_results[0]
        if ancestor_results
        else None
    )

    descendants = (
        descendant_results[0].get(
            "descendants",
            [],
        )
        if descendant_results
        else []
    )

    add_log(
        f"GRAPH concept={concept_id} "
        f"latency={elapsed:.3f}s"
    )

    return concept, descendants, elapsed


# ============================================================
# DEEP PURPLE CSS
# ============================================================

st.markdown(
    """
<style>
:root {
    --bg: #100719;
    --panel: #1b0d2a;
    --panel2: #27123c;
    --border: #57327c;
    --accent: #a970ff;
    --bright: #c7a4ff;
    --text: #f5efff;
    --muted: #b8a5cf;
    --green: #56f2b3;
    --red: #ff6b9e;
}

header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu,
footer {
    display: none !important;
}

html,
body,
[data-testid="stAppViewContainer"],
.stApp {
    background:
        radial-gradient(
            circle at top right,
            rgba(115, 61, 170, 0.25),
            transparent 32%
        ),
        linear-gradient(
            145deg,
            #0d0614,
            #170923,
            #210e32
        ) !important;
    color: var(--text) !important;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #170a24,
            #210f34
        ) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--text);
}

.block-container {
    max-width: 1500px;
    padding-top: 1.3rem;
}

.retro-title {
    padding: 18px 22px;
    margin-bottom: 13px;
    border: 1px solid var(--accent);
    border-left: 7px solid var(--accent);
    background: rgba(72, 31, 108, 0.42);
    color: var(--text);
    font: 700 24px "Courier New", monospace;
    letter-spacing: 1.2px;
}

.section-title {
    margin: 16px 0 10px;
    padding: 8px 12px;
    border-left: 4px solid var(--accent);
    background: rgba(169, 112, 255, 0.09);
    color: var(--bright);
    font: 700 14px "Courier New", monospace;
    letter-spacing: 1px;
}

.status-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    padding: 11px 14px;
    border: 1px solid var(--border);
    background: rgba(27, 13, 42, 0.88);
    font: 13px "Courier New", monospace;
}

.metric-card {
    min-height: 105px;
    padding: 15px;
    border: 1px solid var(--border);
    border-top: 4px solid var(--accent);
    border-radius: 5px;
    background:
        linear-gradient(
            145deg,
            rgba(39, 18, 60, 0.98),
            rgba(24, 11, 37, 0.98)
        );
}

.metric-label {
    color: var(--muted);
    font: 12px "Courier New", monospace;
}

.metric-value {
    margin-top: 8px;
    color: var(--text);
    font: 700 25px "Courier New", monospace;
}

.path-node {
    padding: 11px 14px;
    border: 1px solid var(--border);
    border-left: 5px solid var(--accent);
    border-radius: 4px;
    background: rgba(38, 17, 58, 0.9);
    color: var(--text);
    font-family: "Courier New", monospace;
}

.path-arrow {
    padding-left: 19px;
    color: var(--accent);
    font-size: 18px;
}

.log-window {
    height: 230px;
    overflow-y: auto;
    padding: 13px;
    border: 1px solid var(--border);
    background: #09040e;
    color: #d9c5f5;
    font: 12px/1.55 "Courier New", monospace;
    white-space: pre-wrap;
}

.connected {
    color: var(--green) !important;
    font-family: "Courier New", monospace;
}

.disconnected {
    color: var(--red) !important;
    font-family: "Courier New", monospace;
}

div.stButton > button {
    min-height: 42px;
    border: 1px solid var(--accent) !important;
    background:
        linear-gradient(
            145deg,
            #3a1b57,
            #251036
        ) !important;
    color: var(--text) !important;
    font-family: "Courier New", monospace;
    font-weight: 700;
}

div.stButton > button:hover {
    border-color: var(--bright) !important;
    background: #51277a !important;
}

div[data-baseweb="input"] > div,
.stTextInput input {
    border-color: var(--border) !important;
    background-color: #180b25 !important;
    color: var(--text) !important;
}

[data-testid="stDataFrame"],
[data-testid="stExpander"] {
    border: 1px solid var(--border);
}

.stTabs [data-baseweb="tab"] {
    color: var(--muted);
}

.stTabs [aria-selected="true"] {
    color: var(--text) !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# STATUS
# ============================================================

atlas_connected, atlas_message = atlas_status()

healthcare_count = collection_count(
    healthcare_collection
)

ontology_count = collection_count(
    ontology_collection
)

index_status = (
    get_vector_index_status()
    if atlas_connected
    else {
        "exists": False,
        "ready": False,
        "status": "DISCONNECTED",
    }
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## SEMANTIC ONTOLOGY LAB")
    st.markdown("`v0.2-demo`")
    st.markdown("---")

    if atlas_connected:
        st.markdown(
            '<span class="connected">'
            "● ATLAS CONNECTED"
            "</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="disconnected">'
            "● ATLAS DISCONNECTED"
            "</span>",
            unsafe_allow_html=True,
        )

    if not MONGODB_URI:
        st.caption(
            "Paste the Atlas URI into MONGODB_URI."
        )
    elif not atlas_connected:
        st.error(atlas_message)

    st.markdown("---")
    st.markdown("**DEMO CONTROL**")

    if st.button(
        "[S] SEED DATA + VECTOR INDEX",
        use_container_width=True,
        disabled=not atlas_connected,
    ):
        if seed_demo():
            st.rerun()

    if st.button(
        "[I] REFRESH INDEX STATUS",
        use_container_width=True,
        disabled=not atlas_connected,
    ):
        st.rerun()

    if st.button(
        "[R] RESET DEMO DATA",
        use_container_width=True,
        disabled=not atlas_connected,
    ):
        if reset_demo():
            st.rerun()

    st.markdown("---")
    st.caption(f"Model: {EMBEDDING_MODEL}")
    st.caption(
        f"Vector index: {VECTOR_INDEX_NAME}"
    )
    st.caption(
        f"Index status: {index_status['status']}"
    )
    st.caption(
        "Index creation and embedding are asynchronous."
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="retro-title">
| VECTOR SEARCH → ONTOLOGY → $GRAPHLOOKUP |
</div>
""",
    unsafe_allow_html=True,
)

latency_text = (
    f"{st.session_state.last_latency:.3f}s"
    if st.session_state.last_latency is not None
    else "N/A"
)

st.markdown(
    f"""
<div class="status-bar">
    <span>ATLAS: {"CONNECTED" if atlas_connected else "DISCONNECTED"}</span>
    <span>HEALTHCARE: {healthcare_count}</span>
    <span>CONCEPTS: {ontology_count}</span>
    <span>VECTOR INDEX: {html.escape(index_status["status"])}</span>
    <span>LAST LATENCY: {latency_text}</span>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# EMPTY STATE
# ============================================================

if healthcare_count == 0 or ontology_count == 0:
    st.info(
        "Click [S] SEED DATA + VECTOR INDEX to create both "
        "collections and the automated embedding index."
    )

    a, b, c = st.columns(3)

    with a:
        st.markdown(
            """
<div class="metric-card">
    <div class="metric-label">STEP 1</div>
    <div class="metric-value">Vector Search</div>
    <div class="metric-label">Understand natural-language intent</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with b:
        st.markdown(
            """
<div class="metric-card">
    <div class="metric-label">STEP 2</div>
    <div class="metric-value">Concept ID</div>
    <div class="metric-label">Connect semantic results to ontology</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with c:
        st.markdown(
            """
<div class="metric-card">
    <div class="metric-label">STEP 3</div>
    <div class="metric-value">$graphLookup</div>
    <div class="metric-label">Traverse deterministic relationships</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="section-title">ACTIVITY LOG</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="log-window">'
        + html.escape(
            "\n".join(st.session_state.logs)
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# DEMO QUERY
# ============================================================

demo_tab, pipeline_tab, data_tab = st.tabs(
    [
        "LIVE DEMO",
        "PIPELINES",
        "SEEDED DATA",
    ]
)

with demo_tab:
    st.markdown(
        '<div class="section-title">'
        "NATURAL-LANGUAGE HEALTHCARE SEARCH"
        "</div>",
        unsafe_allow_html=True,
    )

    query_text = st.text_input(
        "Describe the healthcare provider you need",
        value=st.session_state.query_text,
        placeholder=(
            "Example: I need a doctor who performs "
            "heart catheterization"
        ),
    )

    st.session_state.query_text = query_text

    run_search = st.button(
        "RUN VECTOR SEARCH + GRAPH LOOKUP",
        use_container_width=True,
        disabled=not index_status["ready"],
    )

    if not index_status["ready"]:
        st.warning(
            "The Automated Embedding index is not queryable yet. "
            "Wait for its status to become READY, then click "
            "[I] REFRESH INDEX STATUS."
        )

    if run_search:
        try:
            with st.spinner(
                "Running semantic search and ontology traversal..."
            ):
                results = run_vector_search(
                    query_text
                )

                st.session_state.semantic_results = (
                    results
                )

                st.session_state.matched_concept_id = (
                    results[0]["conceptId"]
                    if results
                    else None
                )

        except PyMongoError as exc:
            add_log(
                f"ERROR vector search failed: {exc}"
            )
            st.error(
                f"Vector Search failed: {exc}"
            )

    vector_results = (
        st.session_state.semantic_results
    )

    matched_concept_id = (
        st.session_state.matched_concept_id
    )

    if vector_results:
        st.markdown(
            '<div class="section-title">'
            "STEP 1 / VECTOR SEARCH RESULTS"
            "</div>",
            unsafe_allow_html=True,
        )

        result_rows = [
            {
                "Rank": index + 1,
                "Matched intent": item["title"],
                "Concept ID": item["conceptId"],
                "Score": round(
                    item.get("score", 0),
                    4,
                ),
            }
            for index, item in enumerate(
                vector_results
            )
        ]

        st.dataframe(
            pd.DataFrame(result_rows),
            use_container_width=True,
            hide_index=True,
        )

        top_match = vector_results[0]

        st.success(
            f"Top semantic match: {top_match['title']} "
            f"→ {top_match['conceptId']}"
        )

        concept, descendants, graph_latency = (
            get_ontology_context(
                matched_concept_id
            )
        )

        if concept:
            ancestors = sorted(
                concept.get("ancestors", []),
                key=lambda item: item.get(
                    "traversalDepth",
                    0,
                ),
                reverse=True,
            )

            selected_concept = {
                key: value
                for key, value in concept.items()
                if key != "ancestors"
            }

            hierarchy = (
                ancestors
                + [selected_concept]
            )

            st.markdown(
                '<div class="section-title">'
                "STEP 2 / $GRAPHLOOKUP ONTOLOGY PATH"
                "</div>",
                unsafe_allow_html=True,
            )

            left, right = st.columns(
                [1.05, 1],
                gap="large",
            )

            with left:
                for index, node in enumerate(
                    hierarchy
                ):
                    selected = (
                        node.get("_id")
                        == matched_concept_id
                    )

                    marker = (
                        "VECTOR MATCH"
                        if selected
                        else f"LEVEL {index}"
                    )

                    st.markdown(
                        f"""
<div class="path-node">
{html.escape(marker)} ::
{html.escape(node.get("name", ""))}
[{html.escape(node.get("code", ""))}]
</div>
""",
                        unsafe_allow_html=True,
                    )

                    if index < len(hierarchy) - 1:
                        st.markdown(
                            '<div class="path-arrow">↓</div>',
                            unsafe_allow_html=True,
                        )

            with right:
                st.markdown(
                    f"### {concept.get('name')}"
                )
                st.write(
                    concept.get("description")
                )

                st.write(
                    "Synonyms:",
                    ", ".join(
                        concept.get(
                            "synonyms",
                            [],
                        )
                    ),
                )

                st.metric(
                    "Vector similarity",
                    f"{top_match.get('score', 0):.4f}",
                )

                st.metric(
                    "$graphLookup latency",
                    f"{graph_latency * 1000:.2f} ms",
                )

                if descendants:
                    descendant_rows = [
                        {
                            "Name": item.get("name"),
                            "Code": item.get("code"),
                            "Depth": (
                                item.get(
                                    "traversalDepth",
                                    0,
                                )
                                + 1
                            ),
                        }
                        for item in sorted(
                            descendants,
                            key=lambda item: (
                                item.get(
                                    "traversalDepth",
                                    0,
                                ),
                                item.get("name", ""),
                            ),
                        )
                    ]

                    st.markdown(
                        "#### Descendant concepts"
                    )

                    st.dataframe(
                        pd.DataFrame(
                            descendant_rows
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )


# ============================================================
# PIPELINE INSPECTION
# ============================================================

with pipeline_tab:
    st.markdown(
        '<div class="section-title">'
        "STEP 1 / AUTOMATED EMBEDDING VECTOR SEARCH"
        "</div>",
        unsafe_allow_html=True,
    )

    st.code(
        json.dumps(
            vector_search_pipeline(
                st.session_state.query_text
            ),
            indent=2,
        ),
        language="json",
    )

    st.markdown(
        '<div class="section-title">'
        "STEP 2 / ONTOLOGY ANCESTOR TRAVERSAL"
        "</div>",
        unsafe_allow_html=True,
    )

    example_concept = (
        matched_concept_id
        or "interventional_cardiology"
    )

    st.code(
        json.dumps(
            ancestor_pipeline(
                example_concept
            ),
            indent=2,
        ),
        language="json",
    )

    st.markdown(
        '<div class="section-title">'
        "AUTOMATED EMBEDDING INDEX"
        "</div>",
        unsafe_allow_html=True,
    )

    st.code(
        json.dumps(
            {
                "name": VECTOR_INDEX_NAME,
                "type": "vectorSearch",
                "definition": {
                    "fields": [
                        {
                            "type": "autoEmbed",
                            "modality": "text",
                            "path": "searchText",
                            "model": EMBEDDING_MODEL,
                        }
                    ]
                },
            },
            indent=2,
        ),
        language="json",
    )


# ============================================================
# DATA INSPECTION
# ============================================================

with data_tab:
    st.markdown(
        '<div class="section-title">'
        "HEALTHCARE SEMANTIC DOCUMENTS"
        "</div>",
        unsafe_allow_html=True,
    )

    healthcare_rows = list(
        healthcare_collection.find(
            {},
            {
                "_id": 1,
                "conceptId": 1,
                "title": 1,
                "searchText": 1,
            },
        ).sort("_id", ASCENDING)
    )

    st.dataframe(
        pd.DataFrame(healthcare_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Atlas stores automatically generated embeddings "
        "separately, so no embedding array appears here."
    )

    st.markdown(
        '<div class="section-title">'
        "ONTOLOGY CONCEPT DOCUMENTS"
        "</div>",
        unsafe_allow_html=True,
    )

    ontology_rows = list(
        ontology_collection.find(
            {},
            {
                "_id": 1,
                "name": 1,
                "code": 1,
                "conceptType": 1,
                "parentId": 1,
            },
        ).sort("name", ASCENDING)
    )

    st.dataframe(
        pd.DataFrame(ontology_rows),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ACTIVITY LOG
# ============================================================

st.markdown(
    '<div class="section-title">'
    "ACTIVITY LOG"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="log-window">'
    + html.escape(
        "\n".join(st.session_state.logs)
    )
    + "</div>",
    unsafe_allow_html=True,
)
