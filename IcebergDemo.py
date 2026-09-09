import time

import pandas as pd
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="UHG Iceberg CDC Demo",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# MONGODB ATLAS
#
# Paste Atlas URI directly here.
# Demo app. No getenv.
# ============================================================

MONGODB_URI = ""

client = (
    MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=4000,
        connectTimeoutMS=4000
    )
    if MONGODB_URI
    else None
)

db = client["uhg_iceberg_demo"] if client else None
collection = db["member_events"] if db is not None else None


# ============================================================
# DEMO RECORD
# ============================================================

LIVE_EVENT = {
    "_id": "EVT-LIVE-001",
    "memberId": "MBR-9001",
    "claimId": "CLM-99001",
    "eventType": "CLAIM_SUBMITTED",
    "serviceType": "Emergency",
    "providerId": "PRV-9100",
    "region": "MN",
    "amount": 2875.00,
    "status": "SUBMITTED",
    "serviceDate": "2026-08-20T14:20:00Z"
}


# ============================================================
# ATLAS HELPERS
# ============================================================

def atlas_status():
    if client is None:
        return False, "MONGODB_URI NOT CONFIGURED"

    try:
        client.admin.command("ping")
        return True, "ATLAS CONNECTED"

    except Exception as exc:
        return False, str(exc)


def get_mongo_rows():

    if collection is None:
        return []

    try:
        return list(
            collection
            .find({})
            .sort("_id", 1)
        )

    except PyMongoError:
        return []


def get_live_event():

    if collection is None:
        return None

    try:
        return collection.find_one({
            "_id": LIVE_EVENT["_id"]
        })

    except PyMongoError:
        return None


def serialize_doc(doc):

    if not doc:
        return None

    clean = {}

    for key, value in doc.items():

        if hasattr(value, "isoformat"):
            clean[key] = value.isoformat()

        else:
            clean[key] = value

    return clean


# ============================================================
# SESSION STATE
#
# MongoDB side = REAL
# Iceberg side = CANNED until Athena gets wired in
# ============================================================

if "iceberg_rows" not in st.session_state:

    st.session_state.iceberg_rows = []


if "schema_fields" not in st.session_state:

    st.session_state.schema_fields = [
        "_id",
        "memberId",
        "claimId",
        "eventType",
        "serviceType",
        "providerId",
        "region",
        "amount",
        "status",
        "serviceDate"
    ]


if "logs" not in st.session_state:

    st.session_state.logs = [
        "[BOOT] INFO  processor=uhg_iceberg_cdc",
        "[BOOT] INFO  source=uhg_iceberg_demo.member_events",
        "[BOOT] INFO  sink=S3 / Apache Iceberg v2",
        "[BOOT] INFO  catalog=AWS Glue",
        "[BOOT] READY waiting for change events..."
    ]


if "last_latency" not in st.session_state:

    st.session_state.last_latency = None


if "last_action" not in st.session_state:

    st.session_state.last_action = "READY"


# ============================================================
# LOGGING / CANNED ICEBERG
# ============================================================

def add_log(message):

    stamp = time.strftime("%H:%M:%S")

    st.session_state.logs.append(
        f"[{stamp}] {message}"
    )

    st.session_state.logs = (
        st.session_state.logs[-16:]
    )


def mark_sync(action, latency):

    st.session_state.last_action = action
    st.session_state.last_latency = latency

    add_log(
        f"CDC   {action}"
    )

    add_log(
        f"ICE   commit complete latency={latency:.1f}s"
    )

    add_log(
        "READY waiting for change events..."
    )


def mirror_to_iceberg(doc):

    doc = serialize_doc(doc)

    if not doc:
        return

    st.session_state.iceberg_rows = [
        row
        for row in st.session_state.iceberg_rows
        if row.get("_id") != doc["_id"]
    ]

    st.session_state.iceberg_rows.append(
        doc
    )


# ============================================================
# REAL MONGODB DEMO ACTIONS
# ============================================================

def insert_event():

    if collection is None:

        add_log(
            "ERROR Atlas connection not configured"
        )

        return

    try:

        collection.replace_one(
            {
                "_id": LIVE_EVENT["_id"]
            },
            LIVE_EVENT,
            upsert=True
        )

        doc = collection.find_one({
            "_id": LIVE_EVENT["_id"]
        })

        mirror_to_iceberg(
            doc
        )

        mark_sync(
            "INSERT EVT-LIVE-001",
            1.3
        )

    except PyMongoError as exc:

        add_log(
            f"ERROR insert failed: {exc}"
        )


def update_event():

    if collection is None:

        add_log(
            "ERROR Atlas connection not configured"
        )

        return

    try:

        if collection.find_one(
            {
                "_id": LIVE_EVENT["_id"]
            }
        ) is None:

            collection.insert_one(
                dict(LIVE_EVENT)
            )

        collection.update_one(
            {
                "_id": LIVE_EVENT["_id"]
            },
            {
                "$set": {
                    "status": "APPROVED",
                    "amount": 2540.25,
                    "eventType": "CLAIM_ADJUDICATED"
                }
            }
        )

        doc = collection.find_one({
            "_id": LIVE_EVENT["_id"]
        })

        mirror_to_iceberg(
            doc
        )

        mark_sync(
            "UPDATE EVT-LIVE-001",
            1.8
        )

    except PyMongoError as exc:

        add_log(
            f"ERROR update failed: {exc}"
        )


def delete_event():

    if collection is None:

        add_log(
            "ERROR Atlas connection not configured"
        )

        return

    try:

        collection.delete_one({
            "_id": LIVE_EVENT["_id"]
        })

        st.session_state.iceberg_rows = [
            row
            for row in st.session_state.iceberg_rows
            if row.get("_id") != LIVE_EVENT["_id"]
        ]

        mark_sync(
            "DELETE EVT-LIVE-001",
            1.1
        )

    except PyMongoError as exc:

        add_log(
            f"ERROR delete failed: {exc}"
        )


def evolve_schema():

    if collection is None:

        add_log(
            "ERROR Atlas connection not configured"
        )

        return

    try:

        collection.update_one(
            {
                "_id": "EVT-10003"
            },
            {
                "$set": {
                    "riskScore": 0.91,
                    "reviewReason": "HIGH_COST_AND_PENDING"
                }
            }
        )

        for field in [
            "riskScore",
            "reviewReason"
        ]:

            if field not in st.session_state.schema_fields:

                st.session_state.schema_fields.append(
                    field
                )

        source_doc = collection.find_one({
            "_id": "EVT-10003"
        })

        if source_doc:

            mirror_to_iceberg(
                source_doc
            )

        mark_sync(
            "SCHEMA EVOLUTION + riskScore + reviewReason",
            2.2
        )

    except PyMongoError as exc:

        add_log(
            f"ERROR schema evolution failed: {exc}"
        )


def reset_demo():

    if collection is not None:

        try:

            collection.delete_one({
                "_id": LIVE_EVENT["_id"]
            })

            collection.update_one(
                {
                    "_id": "EVT-10003"
                },
                {
                    "$unset": {
                        "riskScore": "",
                        "reviewReason": ""
                    }
                }
            )

        except PyMongoError:
            pass

    st.session_state.iceberg_rows = []

    st.session_state.schema_fields = [
        "_id",
        "memberId",
        "claimId",
        "eventType",
        "serviceType",
        "providerId",
        "region",
        "amount",
        "status",
        "serviceDate"
    ]

    st.session_state.logs = [
        "[RESET] INFO  demo state restored",
        "[RESET] READY waiting for change events..."
    ]

    st.session_state.last_latency = None
    st.session_state.last_action = "READY"


# ============================================================
# RETRO UI CSS
# ============================================================

st.markdown(
    """
<style>

/* ----------------------------------------------------------
   REMOVE STREAMLIT CHROME
   ---------------------------------------------------------- */

header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}


/* ----------------------------------------------------------
   GLOBAL
   ---------------------------------------------------------- */

html,
body,
[class*="css"] {
    font-family:
        "Courier New",
        Courier,
        monospace !important;
}

.stApp {
    background: #061216;
    color: #d7f7e4;
    margin-top: 0 !important;
    padding-top: 0 !important;
}

.block-container {
    padding-top: 0.35rem !important;
    padding-bottom: 1rem !important;
    max-width: 1500px;
}

div[data-testid="stVerticalBlock"] {
    gap: 0.45rem !important;
}

h1,
h2,
h3 {
    color: #71f0a7 !important;
    margin-top: 0.25rem !important;
    margin-bottom: 0.25rem !important;
}

p {
    margin-top: 0 !important;
    margin-bottom: 0.2rem !important;
}


/* ----------------------------------------------------------
   SIDEBAR
   ---------------------------------------------------------- */

section[data-testid="stSidebar"] {
    background: #0a1c21;
    border-right: 1px solid #355d64;
}


/* ----------------------------------------------------------
   HEADER
   ---------------------------------------------------------- */

.retro-title {
    border: 2px solid #f4d76e;
    background: #0b2228;
    padding: 11px 15px;
    color: #91ffd1;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-bottom: 6px;
}


/* ----------------------------------------------------------
   STATUS BAR
   ---------------------------------------------------------- */

.status-panel {
    border: 1px solid #3c7d84;
    background: #081a1f;

    padding: 9px 13px;
    margin: 0 0 7px 0;

    display: flex;
    align-items: center;
    flex-wrap: wrap;

    gap: 7px 11px;

    line-height: 1.15;
    min-height: 0;
}

.status-panel span {
    margin: 0 !important;
    padding: 0 !important;
    display: inline-block;
}

.status-panel p {
    margin: 0 !important;
    padding: 0 !important;
}

.connected {
    color: #71f0a7;
    font-weight: 700;
}

.disconnected {
    color: #ff7d7d;
    font-weight: 700;
}

.ok {
    color: #71f0a7;
}

.warn {
    color: #f4d76e;
}

.dim {
    color: #789da5;
}

.divider {
    color: #3c7d84;
}


/* ----------------------------------------------------------
   METRICS
   ---------------------------------------------------------- */

div[data-testid="stMetric"] {
    border: 1px solid #3c7d84;
    background: #091d22;
    padding: 8px 10px;
}

div[data-testid="stMetricLabel"] {
    color: #789da5;
}

div[data-testid="stMetricValue"] {
    color: #71f0a7;
}


/* ----------------------------------------------------------
   FLOW
   ---------------------------------------------------------- */

.flow {
    border: 1px solid #3c7d84;
    background: #07191e;
    padding: 9px;
    text-align: center;
    color: #9bdcb7;
    min-height: 58px;

    display: flex;
    align-items: center;
    justify-content: center;
}

.flow-arrow {
    color: #f4d76e;
    text-align: center;
    font-size: 24px;
    padding-top: 11px;
}


/* ----------------------------------------------------------
   SECTION TITLES
   ---------------------------------------------------------- */

.section-title {
    color: #71f0a7;
    font-weight: bold;
    margin-top: 3px;
    margin-bottom: 3px;
}


/* ----------------------------------------------------------
   TERMINAL
   ---------------------------------------------------------- */

.terminal {
    border: 1px solid #3c7d84;
    background: #02090b;
    color: #7df9a5;
    padding: 10px;
    height: 270px;
    overflow-y: auto;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}


/* ----------------------------------------------------------
   SCHEMA
   ---------------------------------------------------------- */

.schema {
    border: 1px solid #3c7d84;
    background: #081a1f;
    padding: 9px 11px;
    color: #a7f2c5;
    margin-top: 3px;
}


/* ----------------------------------------------------------
   BUTTONS
   ---------------------------------------------------------- */

.stButton > button {
    font-family:
        "Courier New",
        Courier,
        monospace !important;

    border-radius: 0 !important;

    border:
        1px solid
        #77d79b !important;

    background:
        #0a2528 !important;

    color:
        #b9ffd2 !important;

    min-height:
        39px;
}

.stButton > button:hover {
    border-color:
        #f4d76e !important;

    color:
        #fff0a8 !important;

    background:
        #12363a !important;
}


/* ----------------------------------------------------------
   DATAFRAME
   ---------------------------------------------------------- */

div[data-testid="stDataFrame"] {
    border:
        1px solid
        #3c7d84;
}


/* ----------------------------------------------------------
   ALERTS
   ---------------------------------------------------------- */

div[data-testid="stAlert"] {
    border-radius: 0 !important;
}


/* ----------------------------------------------------------
   CODE
   ---------------------------------------------------------- */

code {
    font-family:
        "Courier New",
        Courier,
        monospace !important;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# CONNECTION CHECK
# ============================================================

atlas_connected, atlas_message = atlas_status()

mongo_rows = get_mongo_rows()

mongo_count = len(mongo_rows)

latency = (
    f"{st.session_state.last_latency:.1f}s"
    if st.session_state.last_latency is not None
    else "--"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## ICEBERG SETUP UTILITY"
    )

    st.markdown(
        "`v0.4-demo`"
    )

    st.markdown("---")

    if atlas_connected:

        st.markdown(
            '<span class="connected">'
            '● ATLAS CONNECTED'
            '</span>',
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            '<span class="disconnected">'
            '● ATLAS DISCONNECTED'
            '</span>',
            unsafe_allow_html=True
        )

    st.code(
        "CLUSTER : darkstar\n"
        "DB      : uhg_iceberg_demo\n"
        "COLL    : member_events\n"
        "PROC    : uhg_iceberg_cdc\n"
        "MODE    : CDC\n"
        "CATALOG : AWS GLUE",
        language=None
    )

    st.markdown(
        "**DEMO CONTROL**"
    )

    if st.button(
        "[1] INSERT EVENT",
        use_container_width=True,
        disabled=not atlas_connected
    ):

        insert_event()
        st.rerun()

    if st.button(
        "[2] UPDATE EVENT",
        use_container_width=True,
        disabled=not atlas_connected
    ):

        update_event()
        st.rerun()

    if st.button(
        "[3] DELETE EVENT",
        use_container_width=True,
        disabled=not atlas_connected
    ):

        delete_event()
        st.rerun()

    if st.button(
        "[4] EVOLVE SCHEMA",
        use_container_width=True,
        disabled=not atlas_connected
    ):

        evolve_schema()
        st.rerun()

    st.markdown("---")

    if st.button(
        "[R] RESET DEMO",
        use_container_width=True,
        disabled=not atlas_connected
    ):

        reset_demo()
        st.rerun()

    st.markdown("---")

    st.caption(
        "F1 Help    F10 Quit"
    )

    st.caption(
        "ICEBERG SETUP UTILITY v0.4"
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="retro-title">'
    '| UHG ICEBERG / ATLAS STREAM PROCESSING |'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# COMPACT STATUS BAR
# ============================================================

if atlas_connected:

    atlas_state = (
        '<span class="connected">'
        '● MONGODB ATLAS CONNECTED'
        '</span>'
    )

else:

    atlas_state = (
        '<span class="disconnected">'
        '● MONGODB ATLAS DISCONNECTED'
        '</span>'
    )


status_html = (
    '<div class="status-panel">'
    f'{atlas_state}'
    '<span class="dim">namespace:</span>'
    '<span>uhg_iceberg_demo.member_events</span>'
    '<span class="dim">driver:</span>'
    '<span>PyMongo</span>'
    '<span class="divider">|</span>'
    '<span class="ok">● PROCESSOR RUNNING</span>'
    '<span class="divider">|</span>'
    '<span>LAST ACTION:</span>'
    f'<span class="warn">{st.session_state.last_action}</span>'
    '<span class="divider">|</span>'
    '<span>SYNC:</span>'
    f'<span class="ok">{latency}</span>'
    '</div>'
)

st.markdown(
    status_html,
    unsafe_allow_html=True
)


# ============================================================
# METRIC ROW
# ============================================================

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "MongoDB Documents",
    mongo_count
)

m2.metric(
    "Iceberg Rows",
    len(
        st.session_state.iceberg_rows
    )
)

m3.metric(
    "Iceberg Columns",
    len(
        st.session_state.schema_fields
    )
)

m4.metric(
    "Last Sync",
    latency
)


# ============================================================
# DATA PATH
# ============================================================

st.markdown(
    '<div class="section-title">'
    'DATA PATH'
    '</div>',
    unsafe_allow_html=True
)

a, b, c, d, e = st.columns(
    [
        1.2,
        0.25,
        1.4,
        0.25,
        1.2
    ]
)

with a:

    st.markdown(
        '<div class="flow">'
        '<div>'
        'MongoDB Atlas'
        '<br>'
        '<b>member_events</b>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


with b:

    st.markdown(
        '<div class="flow-arrow">'
        '→'
        '</div>',
        unsafe_allow_html=True
    )


with c:

    st.markdown(
        '<div class="flow">'
        '<div>'
        'Atlas Stream Processing'
        '<br>'
        '<b>$iceberg</b>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


with d:

    st.markdown(
        '<div class="flow-arrow">'
        '→'
        '</div>',
        unsafe_allow_html=True
    )


with e:

    st.markdown(
        '<div class="flow">'
        '<div>'
        'S3 / Iceberg v2'
        '<br>'
        '<b>AWS Glue</b>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# LIVE EVENT ROW
# ============================================================

left, right = st.columns(2)


with left:

    st.markdown(
        '<div class="section-title">'
        'SOURCE :: MONGODB ATLAS'
        '</div>',
        unsafe_allow_html=True
    )

    live_doc = get_live_event()

    if live_doc:

        st.json(
            serialize_doc(
                live_doc
            ),
            expanded=True
        )

    else:

        st.info(
            "EVT-LIVE-001 NOT FOUND\n\n"
            "PRESS [1] INSERT EVENT"
        )


with right:

    st.markdown(
        '<div class="section-title">'
        'SINK :: ICEBERG TABLE'
        '</div>',
        unsafe_allow_html=True
    )

    iceberg_live = next(
        (
            row
            for row
            in st.session_state.iceberg_rows
            if row.get("_id")
            == LIVE_EVENT["_id"]
        ),
        None
    )

    if iceberg_live:

        st.dataframe(
            pd.DataFrame(
                [iceberg_live]
            ),
            use_container_width=True,
            hide_index=True,
            height=220
        )

    else:

        st.code(
            "SELECT *\n"
            "FROM member_events\n"
            "WHERE _id = 'EVT-LIVE-001';\n\n"
            "-- 0 rows",
            language="sql"
        )


# ============================================================
# LOWER DASHBOARD
# ============================================================

left2, right2 = st.columns(
    [
        1.35,
        1
    ]
)


with left2:

    st.markdown(
        '<div class="section-title">'
        'ATLAS COLLECTION :: member_events'
        '</div>',
        unsafe_allow_html=True
    )

    if mongo_rows:

        mongo_df = pd.DataFrame(
            [
                serialize_doc(row)
                for row
                in mongo_rows
            ]
        )

        preferred_columns = [
            "_id",
            "memberId",
            "claimId",
            "eventType",
            "serviceType",
            "region",
            "amount",
            "status"
        ]

        existing_columns = [
            col
            for col
            in preferred_columns
            if col in mongo_df.columns
        ]

        extra_columns = [
            col
            for col
            in mongo_df.columns
            if col not in existing_columns
        ]

        mongo_df = mongo_df[
            existing_columns
            + extra_columns
        ]

        st.dataframe(
            mongo_df,
            use_container_width=True,
            hide_index=True,
            height=270
        )

    else:

        st.warning(
            "No documents returned "
            "from Atlas."
        )


with right2:

    st.markdown(
        '<div class="section-title">'
        'STREAM PROCESSOR CONSOLE'
        '</div>',
        unsafe_allow_html=True
    )

    console = "\n".join(
        st.session_state.logs
    )

    st.markdown(
        f'<div class="terminal">'
        f'{console}'
        f'</div>',
        unsafe_allow_html=True
    )


# ============================================================
# ICEBERG TABLE
# ============================================================

st.markdown(
    '<div class="section-title">'
    'ICEBERG TABLE :: member_events'
    '</div>',
    unsafe_allow_html=True
)


if st.session_state.iceberg_rows:

    iceberg_df = pd.DataFrame(
        st.session_state.iceberg_rows
    )

    for field in (
        st.session_state.schema_fields
    ):

        if field not in iceberg_df.columns:

            iceberg_df[field] = None

    iceberg_df = iceberg_df[
        st.session_state.schema_fields
    ]

    st.dataframe(
        iceberg_df,
        use_container_width=True,
        hide_index=True,
        height=230
    )

else:

    st.info(
        "No canned Iceberg rows yet. "
        "Run a demo operation."
    )


# ============================================================
# ICEBERG SCHEMA
# ============================================================

schema_line = (
    "  |  ".join(
        st.session_state.schema_fields
    )
)

st.markdown(
    '<div class="schema">'
    '<span class="warn">'
    'ICEBERG SCHEMA ::'
    '</span>'
    '&nbsp;&nbsp;'
    f'{schema_line}'
    '</div>',
    unsafe_allow_html=True
)
