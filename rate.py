import time

import pandas as pd

import streamlit as st

from pymongo import MongoClient

from pymongo.errors import PyMongoError


# ============================================================

# PAGE CONFIG

# ============================================================

st.set_page_config(

    page_title="UHG RATE Automation Demo",

    page_icon="💲",

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

db = client["uhg_rate_demo"] if client else None

source_collection = db["fee_sources"] if db is not None else None

analytics_collection = db["pricing_analytics"] if db is not None else None


# ============================================================

# DEMO CONSTANTS

# ============================================================

PROCEDURES = {

    "99213": "Office outpatient visit",

    "99214": "Office outpatient visit - moderate complexity",

    "93000": "Electrocardiogram complete",

    "71046": "Chest x-ray - two views",

    "70551": "MRI brain without contrast",

    "93306": "Echocardiography complete"

}

STATES = ["TX", "MN", "CA", "FL"]

NETWORKS = ["Commercial", "Medicare", "Medicaid"]

PROVIDER_TYPES = ["Physician", "Facility"]

BASE_RATES = {

    "99213": 108.00,

    "99214": 154.00,

    "93000": 21.00,

    "71046": 35.00,

    "70551": 410.00,

    "93306": 225.00

}


# ============================================================

# DEMO DATA
#
# These documents intentionally use different shapes.
# That is the point of the demo.

# ============================================================

def build_seed_documents():

    docs = []

    seq = 1

    for procedure_index, (code, description) in enumerate(PROCEDURES.items()):

        for state_index, state in enumerate(STATES):

            for network_index, network in enumerate(NETWORKS):

                provider = PROVIDER_TYPES[

                    (procedure_index + state_index + network_index) % 2

                ]

                base = BASE_RATES[code]


                # ------------------------------------------------------------
                # CMS
                # ------------------------------------------------------------

                cms_rate = round(

                    base

                    * (1.00 + (state_index * 0.025)),

                    2

                )

                docs.append({

                    "_id": f"CMS-{seq:05d}",

                    "sourceType": "CMS",

                    "scheduleId": f"CMS-{state}-2026",

                    "hcpcs": code,

                    "description": description,

                    "locality": f"{state}-{state_index + 1:02d}",

                    "state": state,

                    "network": network,

                    "providerType": provider,

                    "facilityRate": round(cms_rate * 0.94, 2),

                    "nonFacilityRate": cms_rate,

                    "effectiveDate": "2026-01-01"

                })

                seq += 1


                # ------------------------------------------------------------
                # MEDICAID
                # ------------------------------------------------------------

                medicaid_rate = round(

                    base

                    * 0.84

                    * (1.00 + (network_index * 0.018)),

                    2

                )

                docs.append({

                    "_id": f"MED-{seq:05d}",

                    "sourceType": "MEDICAID",

                    "feeSource": f"{state}-MEDICAID",

                    "procedure": {

                        "code": code,

                        "description": description

                    },

                    "coverage": {

                        "state": state,

                        "network": network,

                        "providerType": provider

                    },

                    "reimbursement": {

                        "amount": medicaid_rate,

                        "method": "STATE_FEE_SCHEDULE",

                        "effectiveDate": "2026-01-01"

                    }

                })

                seq += 1


                # ------------------------------------------------------------
                # COMMERCIAL CONTRACT
                # ------------------------------------------------------------

                commercial_factor = 1.19 + (state_index * 0.02)

                commercial_rate = round(

                    base * commercial_factor,

                    2

                )

                docs.append({

                    "_id": f"COM-{seq:05d}",

                    "sourceType": "COMMERCIAL",

                    "contractId": f"UHC-COMM-{state}-{100 + seq}",

                    "serviceCode": code,

                    "serviceDescription": description,

                    "market": {

                        "state": state,

                        "network": network

                    },

                    "provider": {

                        "type": provider

                    },

                    "pricing": {

                        "method": "PERCENT_OF_BENCHMARK",

                        "factor": round(commercial_factor, 4),

                        "calculatedRate": commercial_rate

                    },

                    "term": {

                        "effectiveFrom": "2026-01-01"

                    }

                })

                seq += 1


                # ------------------------------------------------------------
                # FACILITY
                # ------------------------------------------------------------

                facility_rate = round(

                    base

                    * 1.30

                    * (1.00 + (procedure_index * 0.012)),

                    2

                )

                docs.append({

                    "_id": f"FAC-{seq:05d}",

                    "sourceType": "FACILITY",

                    "facilitySchedule": {

                        "name": f"{state} Hospital Facility Schedule",

                        "region": state

                    },

                    "service": {

                        "code": code,

                        "label": description

                    },

                    "dimensions": {

                        "state": state,

                        "network": network,

                        "providerType": "Facility"

                    },

                    "rate": {

                        "amount": facility_rate,

                        "methodology": "FACILITY_CONTRACT"

                    },

                    "validFrom": "2026-01-01"

                })

                seq += 1


                # ------------------------------------------------------------
                # PHYSICIAN
                # ------------------------------------------------------------

                physician_rate = round(

                    base

                    * 1.08

                    * (1.00 + (network_index * 0.01)),

                    2

                )

                docs.append({

                    "_id": f"PHY-{seq:05d}",

                    "sourceType": "PHYSICIAN",

                    "physicianFeeSchedule": f"{state}-PHYS-2026",

                    "cpt": {

                        "code": code,

                        "text": description

                    },

                    "geo": state,

                    "plan": network,

                    "providerClass": "Physician",

                    "allowedAmount": physician_rate,

                    "pricingMethod": "PHYSICIAN_FEE_SCHEDULE",

                    "startDate": "2026-01-01"

                })

                seq += 1


                # ------------------------------------------------------------
                # NEGOTIATED / CUSTOM
                #
                # Periodically inject a high-side outlier.
                # ------------------------------------------------------------

                outlier_factor = (

                    1.35

                    if (

                        procedure_index

                        + state_index

                        + network_index

                    ) % 7 == 0

                    else 1.00

                )

                custom_rate = round(

                    base

                    * 1.42

                    * outlier_factor,

                    2

                )

                docs.append({

                    "_id": f"CUS-{seq:05d}",

                    "sourceType": "CUSTOM",

                    "source": {

                        "name": f"CUSTOM-{state}-{seq}",

                        "kind": "Negotiated Contract"

                    },

                    "item": {

                        "procedureCode": code,

                        "display": description

                    },

                    "attributes": {

                        "state": state,

                        "network": network,

                        "providerType": provider

                    },

                    "price": {

                        "value": custom_rate,

                        "currency": "USD",

                        "formula": "NEGOTIATED"

                    },

                    "effective": {

                        "from": "2026-01-01"

                    }

                })

                seq += 1

    return docs


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


def safe_count(collection):

    if collection is None:

        return 0

    try:

        return collection.count_documents({})

    except PyMongoError:

        return 0


def source_family_count():

    if source_collection is None:

        return 0

    try:

        return len(

            source_collection.distinct("sourceType")

        )

    except PyMongoError:

        return 0


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


def get_source_example(source_type):

    if source_collection is None:

        return None

    try:

        return source_collection.find_one({

            "sourceType": source_type

        })

    except PyMongoError:

        return None


# ============================================================

# SESSION STATE

# ============================================================

if "logs" not in st.session_state:

    st.session_state.logs = [

        "[BOOT] INFO  app=uhg_rate_analytics",

        "[BOOT] INFO  source=uhg_rate_demo.fee_sources",

        "[BOOT] INFO  view=uhg_rate_demo.pricing_analytics",

        "[BOOT] READY waiting for demo action..."

    ]


if "last_action" not in st.session_state:

    st.session_state.last_action = "READY"


if "last_latency" not in st.session_state:

    st.session_state.last_latency = None


if "panel" not in st.session_state:

    st.session_state.panel = "overview"


# ============================================================

# LOGGING

# ============================================================

def add_log(message):

    stamp = time.strftime("%H:%M:%S")

    st.session_state.logs.append(

        f"[{stamp}] {message}"

    )

    st.session_state.logs = (

        st.session_state.logs[-18:]

    )


def complete_action(action, start_time):

    elapsed = (

        time.perf_counter()

        - start_time

    )

    st.session_state.last_action = action

    st.session_state.last_latency = elapsed

    add_log(

        f"OK    {action} latency={elapsed:.3f}s"

    )

    add_log(

        "READY waiting for demo action..."

    )


# ============================================================

# REAL MONGODB DEMO ACTIONS

# ============================================================

def seed_demo():

    if source_collection is None:

        add_log(

            "ERROR Atlas connection not configured"

        )

        return

    start_time = time.perf_counter()

    try:

        docs = build_seed_documents()

        source_collection.delete_many({})

        analytics_collection.delete_many({})

        source_collection.insert_many(

            docs,

            ordered=False

        )

        source_collection.create_index([

            ("sourceType", 1)

        ])

        source_collection.create_index([

            ("hcpcs", 1)

        ])

        source_collection.create_index([

            ("procedure.code", 1)

        ])

        source_collection.create_index([

            ("serviceCode", 1)

        ])

        add_log(

            f"LOAD  fee source documents={len(docs)}"

        )

        add_log(

            "INFO  six intentionally different source schemas"

        )

        complete_action(

            "SEED DEMO DATA",

            start_time

        )

        st.session_state.panel = "variability"

    except PyMongoError as exc:

        add_log(

            f"ERROR seed failed: {exc}"

        )


def canonical_pipeline():

    return [

        {

            "$project": {

                "_id": 1,

                "sourceType": 1,

                "feeSchedule": {

                    "$switch": {

                        "branches": [

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CMS"

                                    ]

                                },

                                "then": "$scheduleId"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "MEDICAID"

                                    ]

                                },

                                "then": "$feeSource"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "COMMERCIAL"

                                    ]

                                },

                                "then": "$contractId"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "FACILITY"

                                    ]

                                },

                                "then": "$facilitySchedule.name"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "PHYSICIAN"

                                    ]

                                },

                                "then": "$physicianFeeSchedule"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CUSTOM"

                                    ]

                                },

                                "then": "$source.name"

                            }

                        ],

                        "default": "UNKNOWN"

                    }

                },

                "procedureCode": {

                    "$switch": {

                        "branches": [

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CMS"

                                    ]

                                },

                                "then": "$hcpcs"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "MEDICAID"

                                    ]

                                },

                                "then": "$procedure.code"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "COMMERCIAL"

                                    ]

                                },

                                "then": "$serviceCode"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "FACILITY"

                                    ]

                                },

                                "then": "$service.code"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "PHYSICIAN"

                                    ]

                                },

                                "then": "$cpt.code"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CUSTOM"

                                    ]

                                },

                                "then": "$item.procedureCode"

                            }

                        ],

                        "default": None

                    }

                },

                "description": {

                    "$switch": {

                        "branches": [

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CMS"

                                    ]

                                },

                                "then": "$description"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "MEDICAID"

                                    ]

                                },

                                "then": "$procedure.description"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "COMMERCIAL"

                                    ]

                                },

                                "then": "$serviceDescription"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "FACILITY"

                                    ]

                                },

                                "then": "$service.label"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "PHYSICIAN"

                                    ]

                                },

                                "then": "$cpt.text"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CUSTOM"

                                    ]

                                },

                                "then": "$item.display"

                            }

                        ],

                        "default": None

                    }

                },

                "state": {

                    "$switch": {

                        "branches": [

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CMS"

                                    ]

                                },

                                "then": "$state"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "MEDICAID"

                                    ]

                                },

                                "then": "$coverage.state"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "COMMERCIAL"

                                    ]

                                },

                                "then": "$market.state"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "FACILITY"

                                    ]

                                },

                                "then": "$dimensions.state"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "PHYSICIAN"

                                    ]

                                },

                                "then": "$geo"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CUSTOM"

                                    ]

                                },

                                "then": "$attributes.state"

                            }

                        ],

                        "default": None

                    }

                },

                "network": {

                    "$switch": {

                        "branches": [

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CMS"

                                    ]

                                },

                                "then": "$network"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "MEDICAID"

                                    ]

                                },

                                "then": "$coverage.network"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "COMMERCIAL"

                                    ]

                                },

                                "then": "$market.network"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "FACILITY"

                                    ]

                                },

                                "then": "$dimensions.network"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "PHYSICIAN"

                                    ]

                                },

                                "then": "$plan"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CUSTOM"

                                    ]

                                },

                                "then": "$attributes.network"

                            }

                        ],

                        "default": None

                    }

                },

                "providerType": {

                    "$switch": {

                        "branches": [

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CMS"

                                    ]

                                },

                                "then": "$providerType"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "MEDICAID"

                                    ]

                                },

                                "then": "$coverage.providerType"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "COMMERCIAL"

                                    ]

                                },

                                "then": "$provider.type"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "FACILITY"

                                    ]

                                },

                                "then": "$dimensions.providerType"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "PHYSICIAN"

                                    ]

                                },

                                "then": "$providerClass"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CUSTOM"

                                    ]

                                },

                                "then": "$attributes.providerType"

                            }

                        ],

                        "default": None

                    }

                },

                "calculatedRate": {

                    "$switch": {

                        "branches": [

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CMS"

                                    ]

                                },

                                "then": "$nonFacilityRate"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "MEDICAID"

                                    ]

                                },

                                "then": "$reimbursement.amount"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "COMMERCIAL"

                                    ]

                                },

                                "then": "$pricing.calculatedRate"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "FACILITY"

                                    ]

                                },

                                "then": "$rate.amount"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "PHYSICIAN"

                                    ]

                                },

                                "then": "$allowedAmount"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CUSTOM"

                                    ]

                                },

                                "then": "$price.value"

                            }

                        ],

                        "default": None

                    }

                },

                "pricingMethod": {

                    "$switch": {

                        "branches": [

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CMS"

                                    ]

                                },

                                "then": {

                                    "$literal":

                                        "CMS_FEE_SCHEDULE"

                                }

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "MEDICAID"

                                    ]

                                },

                                "then": "$reimbursement.method"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "COMMERCIAL"

                                    ]

                                },

                                "then": "$pricing.method"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "FACILITY"

                                    ]

                                },

                                "then": "$rate.methodology"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "PHYSICIAN"

                                    ]

                                },

                                "then": "$pricingMethod"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CUSTOM"

                                    ]

                                },

                                "then": "$price.formula"

                            }

                        ],

                        "default": {

                            "$literal":

                                "UNKNOWN"

                        }

                    }

                },

                "effectiveFrom": {

                    "$switch": {

                        "branches": [

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CMS"

                                    ]

                                },

                                "then": "$effectiveDate"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "MEDICAID"

                                    ]

                                },

                                "then": "$reimbursement.effectiveDate"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "COMMERCIAL"

                                    ]

                                },

                                "then": "$term.effectiveFrom"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "FACILITY"

                                    ]

                                },

                                "then": "$validFrom"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "PHYSICIAN"

                                    ]

                                },

                                "then": "$startDate"

                            },

                            {

                                "case": {

                                    "$eq": [

                                        "$sourceType",

                                        "CUSTOM"

                                    ]

                                },

                                "then": "$effective.from"

                            }

                        ],

                        "default": None

                    }

                }

            }

        },

        {

            "$set": {

                "effectiveYear": {

                    "$substrBytes": [

                        "$effectiveFrom",

                        0,

                        4

                    ]

                }

            }

        },

        {

            "$merge": {

                "into": "pricing_analytics",

                "on": "_id",

                "whenMatched": "replace",

                "whenNotMatched": "insert"

            }

        }

    ]


def build_analytical_view():

    if source_collection is None:

        add_log(

            "ERROR Atlas connection not configured"

        )

        return

    start_time = time.perf_counter()

    try:

        add_log(

            "READ  source=fee_sources"

        )

        add_log(

            "MAP   source-specific fields -> common dimensions"

        )

        list(

            source_collection.aggregate(

                canonical_pipeline()

            )

        )

        analytics_collection.create_index([

            ("procedureCode", 1),

            ("state", 1),

            ("providerType", 1),

            ("network", 1),

            ("effectiveYear", 1)

        ])

        analytics_collection.create_index([

            ("sourceType", 1),

            ("calculatedRate", 1)

        ])

        add_log(

            "MERGE target=pricing_analytics"

        )

        add_log(

            f"VIEW  rows={safe_count(analytics_collection)}"

        )

        complete_action(

            "BUILD ANALYTICAL VIEW",

            start_time

        )

        st.session_state.panel = "analytics"

    except PyMongoError as exc:

        add_log(

            f"ERROR analytical view failed: {exc}"

        )


def reset_demo():

    if source_collection is None:

        return

    try:

        source_collection.delete_many({})

        analytics_collection.delete_many({})

    except PyMongoError:

        pass

    st.session_state.logs = [

        "[RESET] INFO  demo collections cleared",

        "[RESET] READY waiting for demo action..."

    ]

    st.session_state.last_latency = None

    st.session_state.last_action = "READY"

    st.session_state.panel = "overview"


# ============================================================

# ANALYTICAL HELPERS

# ============================================================

def build_match(

    procedure,

    state,

    provider,

    network,

    year

):

    match = {

        "procedureCode": procedure,

        "state": state,

        "effectiveYear": year

    }

    if provider != "All":

        match["providerType"] = provider

    if network != "All":

        match["network"] = network

    return match


def run_multidimensional_summary(match):

    if analytics_collection is None:

        return None

    pipeline = [

        {

            "$match": match

        },

        {

            "$facet": {

                "summary": [

                    {

                        "$group": {

                            "_id": None,

                            "count": {

                                "$sum": 1

                            },

                            "average": {

                                "$avg":

                                    "$calculatedRate"

                            },

                            "minimum": {

                                "$min":

                                    "$calculatedRate"

                            },

                            "maximum": {

                                "$max":

                                    "$calculatedRate"

                            },

                            "percentiles": {

                                "$percentile": {

                                    "input":

                                        "$calculatedRate",

                                    "p": [

                                        0.5,

                                        0.9

                                    ],

                                    "method":

                                        "approximate"

                                }

                            }

                        }

                    }

                ],

                "bySource": [

                    {

                        "$group": {

                            "_id":

                                "$sourceType",

                            "averageRate": {

                                "$avg":

                                    "$calculatedRate"

                            },

                            "minimumRate": {

                                "$min":

                                    "$calculatedRate"

                            },

                            "maximumRate": {

                                "$max":

                                    "$calculatedRate"

                            },

                            "records": {

                                "$sum": 1

                            }

                        }

                    },

                    {

                        "$sort": {

                            "averageRate": 1

                        }

                    }

                ],

                "byNetwork": [

                    {

                        "$group": {

                            "_id":

                                "$network",

                            "averageRate": {

                                "$avg":

                                    "$calculatedRate"

                            },

                            "records": {

                                "$sum": 1

                            }

                        }

                    },

                    {

                        "$sort": {

                            "averageRate": 1

                        }

                    }

                ]

            }

        }

    ]

    try:

        rows = list(

            analytics_collection.aggregate(

                pipeline

            )

        )

        return rows[0] if rows else None

    except PyMongoError:

        return None


def run_outlier_analysis(match):

    if analytics_collection is None:

        return []

    pipeline = [

        {

            "$match": match

        },

        {

            "$setWindowFields": {

                "partitionBy":

                    "$procedureCode",

                "sortBy": {

                    "calculatedRate": 1

                },

                "output": {

                    "populationAverage": {

                        "$avg":

                            "$calculatedRate",

                        "window": {

                            "documents": [

                                "unbounded",

                                "unbounded"

                            ]

                        }

                    },

                    "populationStdDev": {

                        "$stdDevPop":

                            "$calculatedRate",

                        "window": {

                            "documents": [

                                "unbounded",

                                "unbounded"

                            ]

                        }

                    }

                }

            }

        },

        {

            "$set": {

                "zScore": {

                    "$cond": [

                        {

                            "$gt": [

                                "$populationStdDev",

                                0

                            ]

                        },

                        {

                            "$divide": [

                                {

                                    "$subtract": [

                                        "$calculatedRate",

                                        "$populationAverage"

                                    ]

                                },

                                "$populationStdDev"

                            ]

                        },

                        0

                    ]

                }

            }

        },

        {

            "$match": {

                "zScore": {

                    "$gte": 1.20

                }

            }

        },

        {

            "$sort": {

                "zScore": -1,

                "calculatedRate": -1

            }

        },

        {

            "$limit": 12

        },

        {

            "$project": {

                "_id": 0,

                "feeSchedule": 1,

                "sourceType": 1,

                "network": 1,

                "providerType": 1,

                "calculatedRate": 1,

                "populationAverage": 1,

                "zScore": 1

            }

        }

    ]

    try:

        return list(

            analytics_collection.aggregate(

                pipeline

            )

        )

    except PyMongoError:

        return []


def fee_source_comparison(

    procedure,

    state,

    year

):

    if analytics_collection is None:

        return pd.DataFrame()

    pipeline = [

        {

            "$match": {

                "procedureCode":

                    procedure,

                "state":

                    state,

                "effectiveYear":

                    year

            }

        },

        {

            "$group": {

                "_id": {

                    "network":

                        "$network",

                    "sourceType":

                        "$sourceType"

                },

                "averageRate": {

                    "$avg":

                        "$calculatedRate"

                }

            }

        },

        {

            "$sort": {

                "_id.network": 1,

                "_id.sourceType": 1

            }

        }

    ]

    try:

        rows = list(

            analytics_collection.aggregate(

                pipeline

            )

        )

    except PyMongoError:

        return pd.DataFrame()

    if not rows:

        return pd.DataFrame()

    flat = [

        {

            "Network":

                row["_id"]["network"],

            "Fee Source":

                row["_id"]["sourceType"],

            "Average Rate":

                round(

                    row["averageRate"],

                    2

                )

        }

        for row in rows

    ]

    frame = pd.DataFrame(flat)

    return (

        frame

        .pivot(

            index="Network",

            columns="Fee Source",

            values="Average Rate"

        )

        .round(2)

    )


def canonical_rows(limit=14):

    if analytics_collection is None:

        return []

    try:

        return list(

            analytics_collection

            .find(

                {},

                {

                    "_id": 0,

                    "procedureCode": 1,

                    "state": 1,

                    "network": 1,

                    "providerType": 1,

                    "sourceType": 1,

                    "feeSchedule": 1,

                    "calculatedRate": 1

                }

            )

            .sort([

                ("procedureCode", 1),

                ("sourceType", 1)

            ])

            .limit(limit)

        )

    except PyMongoError:

        return []


# ============================================================

# OLD SCHOOL IBM / TERMINAL UI CSS

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

    max-width: 1550px;

}

div[data-testid="stVerticalBlock"] {

    gap: 0.42rem !important;

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

    letter-spacing: 0.025em;

    margin-bottom: 6px;

}


/* ----------------------------------------------------------
   STATUS
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

    min-height: 61px;

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
   SECTIONS
   ---------------------------------------------------------- */

.section-title {

    color: #71f0a7;

    font-weight: bold;

    margin-top: 3px;

    margin-bottom: 3px;

}

.feature-box {

    border: 1px solid #3c7d84;

    background: #07191e;

    padding: 10px 12px;

    min-height: 110px;

}

.feature-box b {

    color: #f4d76e;

}

.schema {

    border: 1px solid #3c7d84;

    background: #081a1f;

    padding: 9px 11px;

    color: #a7f2c5;

    margin-top: 3px;

}


/* ----------------------------------------------------------
   TERMINAL
   ---------------------------------------------------------- */

.terminal {

    border: 1px solid #3c7d84;

    background: #02090b;

    color: #7df9a5;

    padding: 10px;

    height: 245px;

    overflow-y: auto;

    white-space: pre-wrap;

    overflow-wrap: anywhere;

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

    min-height: 39px;

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
   DATAFRAMES / INPUTS
   ---------------------------------------------------------- */

div[data-testid="stDataFrame"] {

    border:

        1px solid

        #3c7d84;

}

div[data-baseweb="select"] > div {

    border-radius: 0 !important;

}

div[data-testid="stAlert"] {

    border-radius: 0 !important;

}

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

source_count = safe_count(source_collection)

analytics_count = safe_count(analytics_collection)

family_count = source_family_count()

latency = (

    f"{st.session_state.last_latency:.3f}s"

    if st.session_state.last_latency is not None

    else "--"

)


# ============================================================

# SIDEBAR

# ============================================================

with st.sidebar:

    st.markdown(

        "## RATE ANALYTICS LAB"

    )

    st.markdown(

        "`v0.1-demo`"

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

        "DB      : uhg_rate_demo\n"

        "SOURCE  : fee_sources\n"

        "VIEW    : pricing_analytics\n"

        "MODE    : MULTIDIMENSIONAL\n"

        "NLP/AI  : OUT OF SCOPE",

        language=None

    )

    st.markdown(

        "**DEMO CONTROL**"

    )

    if st.button(

        "[S] SEED DEMO DATA",

        use_container_width=True,

        disabled=not atlas_connected

    ):

        seed_demo()

        st.rerun()

    if st.button(

        "[1] SHOW SOURCE VARIABILITY",

        use_container_width=True,

        disabled=(

            not atlas_connected

            or source_count == 0

        )

    ):

        st.session_state.panel = "variability"

        st.session_state.last_action = (

            "SHOW SOURCE VARIABILITY"

        )

        add_log(

            "VIEW  heterogeneous fee source documents"

        )

        st.rerun()

    if st.button(

        "[2] BUILD ANALYTICAL VIEW",

        use_container_width=True,

        disabled=(

            not atlas_connected

            or source_count == 0

        )

    ):

        build_analytical_view()

        st.rerun()

    if st.button(

        "[3] MULTIDIMENSIONAL ANALYSIS",

        use_container_width=True,

        disabled=(

            not atlas_connected

            or analytics_count == 0

        )

    ):

        st.session_state.panel = "analytics"

        st.session_state.last_action = (

            "MULTIDIMENSIONAL ANALYSIS"

        )

        add_log(

            "AGG   $match -> $facet -> $group -> $percentile"

        )

        st.rerun()

    if st.button(

        "[4] FIND PRICING OUTLIERS",

        use_container_width=True,

        disabled=(

            not atlas_connected

            or analytics_count == 0

        )

    ):

        st.session_state.panel = "outliers"

        st.session_state.last_action = (

            "FIND PRICING OUTLIERS"

        )

        add_log(

            "AGG   $setWindowFields -> pricing outliers"

        )

        st.rerun()

    if st.button(

        "[5] COMPARE FEE SOURCES",

        use_container_width=True,

        disabled=(

            not atlas_connected

            or analytics_count == 0

        )

    ):

        st.session_state.panel = "compare"

        st.session_state.last_action = (

            "COMPARE FEE SOURCES"

        )

        add_log(

            "AGG   fee-source comparison matrix"

        )

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

        "RATE ANALYTICS LAB v0.1"

    )


# ============================================================

# HEADER

# ============================================================

st.markdown(

    '<div class="retro-title">'

    '| UHG RATE AUTOMATION / MULTIDIMENSIONAL PRICING |'

    '</div>',

    unsafe_allow_html=True

)


# ============================================================

# STATUS BAR

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

    '<span>uhg_rate_demo.pricing_analytics</span>'

    '<span class="divider">|</span>'

    '<span class="ok">● ANALYTICS ENGINE READY</span>'

    '<span class="divider">|</span>'

    '<span>LAST ACTION:</span>'

    f'<span class="warn">{st.session_state.last_action}</span>'

    '<span class="divider">|</span>'

    '<span>LATENCY:</span>'

    f'<span class="ok">{latency}</span>'

    '</div>'

)

st.markdown(

    status_html,

    unsafe_allow_html=True

)


# ============================================================

# METRICS

# ============================================================

m1, m2, m3, m4 = st.columns(4)

m1.metric(

    "Raw Fee Documents",

    f"{source_count:,}"

)

m2.metric(

    "Source Families",

    family_count

)

m3.metric(

    "Canonical Pricing Rows",

    f"{analytics_count:,}"

)

m4.metric(

    "Last Operation",

    latency

)


# ============================================================

# DATA PATH

# ============================================================

st.markdown(

    '<div class="section-title">'

    'DATA PATH / FEASIBILITY STORY'

    '</div>',

    unsafe_allow_html=True

)

a, b, c, d, e, f, g = st.columns(

    [

        1.15,

        0.18,

        1.15,

        0.18,

        1.35,

        0.18,

        1.25

    ]

)

with a:

    st.markdown(

        '<div class="flow">'

        '<div>'

        'Heterogeneous Sources'

        '<br>'

        '<b>CMS / Medicaid / Contracts</b>'

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

        'MongoDB Atlas'

        '<br>'

        '<b>Flexible Documents</b>'

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

        'Aggregation + $merge'

        '<br>'

        '<b>Canonical Pricing View</b>'

        '</div>'

        '</div>',

        unsafe_allow_html=True

    )

with f:

    st.markdown(

        '<div class="flow-arrow">'

        '→'

        '</div>',

        unsafe_allow_html=True

    )

with g:

    st.markdown(

        '<div class="flow">'

        '<div>'

        'RATE Analytics'

        '<br>'

        '<b>Slice / Compare / Outliers</b>'

        '</div>'

        '</div>',

        unsafe_allow_html=True

    )


# ============================================================

# ANALYTICAL DIMENSIONS

# ============================================================

st.markdown(

    '<div class="section-title">'

    'ANALYTICAL DIMENSIONS'

    '</div>',

    unsafe_allow_html=True

)

f1, f2, f3, f4, f5 = st.columns(5)

with f1:

    selected_procedure = st.selectbox(

        "Procedure",

        list(PROCEDURES.keys()),

        index=0

    )

with f2:

    selected_state = st.selectbox(

        "State",

        STATES,

        index=0

    )

with f3:

    selected_provider = st.selectbox(

        "Provider",

        [

            "All",

            "Physician",

            "Facility"

        ],

        index=0

    )

with f4:

    selected_network = st.selectbox(

        "Network",

        [

            "All",

            "Commercial",

            "Medicare",

            "Medicaid"

        ],

        index=0

    )

with f5:

    selected_year = st.selectbox(

        "Year",

        ["2026"],

        index=0

    )


current_match = build_match(

    selected_procedure,

    selected_state,

    selected_provider,

    selected_network,

    selected_year

)


# ============================================================

# OVERVIEW PANEL

# ============================================================

if st.session_state.panel == "overview":

    st.markdown(

        '<div class="section-title">'

        'TFW CAPABILITY CHECKPOINTS'

        '</div>',

        unsafe_allow_html=True

    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(

            '<div class="feature-box">'

            '<b>01 / FLEXIBLE MODEL</b>'

            '<br><br>'

            'Different fee-source shapes coexist without '

            'forcing every source into one rigid schema.'

            '</div>',

            unsafe_allow_html=True

        )

    with c2:

        st.markdown(

            '<div class="feature-box">'

            '<b>02 / CANONICAL VIEW</b>'

            '<br><br>'

            'Aggregation maps common pricing dimensions '

            'and materializes an analytical collection.'

            '</div>',

            unsafe_allow_html=True

        )

    with c3:

        st.markdown(

            '<div class="feature-box">'

            '<b>03 / MULTIDIMENSIONAL</b>'

            '<br><br>'

            'Slice pricing by procedure, geography, '

            'network, provider and source family.'

            '</div>',

            unsafe_allow_html=True

        )

    with c4:

        st.markdown(

            '<div class="feature-box">'

            '<b>04 / OUTLIER ANALYSIS</b>'

            '<br><br>'

            'Percentiles and window calculations expose '

            'unusual pricing across comparable populations.'

            '</div>',

            unsafe_allow_html=True

        )

    st.info(

        "Start with [S] SEED DEMO DATA, then walk through "

        "[1] → [5]. NLP / hybrid search is intentionally "

        "excluded from this demo."

    )


# ============================================================

# SOURCE VARIABILITY PANEL

# ============================================================

elif st.session_state.panel == "variability":

    st.markdown(

        '<div class="section-title">'

        '01 :: SOURCE VARIABILITY'

        '</div>',

        unsafe_allow_html=True

    )

    st.markdown(

        '<div class="schema">'

        '<span class="warn">TFW CHECK:</span> '

        'Different fee-source structures can coexist in one '

        'MongoDB collection without forcing a single rigid schema.'

        '</div>',

        unsafe_allow_html=True

    )

    raw1, raw2, raw3 = st.columns(3)

    with raw1:

        st.markdown(

            "**CMS STYLE**"

        )

        cms = get_source_example("CMS")

        if cms:

            st.json(

                serialize_doc(cms),

                expanded=True

            )

    with raw2:

        st.markdown(

            "**MEDICAID STYLE**"

        )

        med = get_source_example("MEDICAID")

        if med:

            st.json(

                serialize_doc(med),

                expanded=True

            )

    with raw3:

        st.markdown(

            "**COMMERCIAL CONTRACT STYLE**"

        )

        commercial = get_source_example(

            "COMMERCIAL"

        )

        if commercial:

            st.json(

                serialize_doc(commercial),

                expanded=True

            )

    st.markdown(

        '<div class="schema">'

        '<span class="warn">CAPABILITY:</span> '

        'Flexible Document Model / Polymorphic Data / '

        'Attribute-style modeling'

        '</div>',

        unsafe_allow_html=True

    )


# ============================================================

# ANALYTICS PANEL

# ============================================================

elif st.session_state.panel == "analytics":

    st.markdown(

        '<div class="section-title">'

        '02 / 03 :: CANONICAL VIEW + MULTIDIMENSIONAL ANALYSIS'

        '</div>',

        unsafe_allow_html=True

    )

    summary = run_multidimensional_summary(

        current_match

    )

    if not summary or not summary.get("summary"):

        st.warning(

            "No analytical rows match the selected dimensions."

        )

    else:

        stats = summary["summary"][0]

        percentiles = stats.get(

            "percentiles",

            [0, 0]

        )

        median = (

            percentiles[0]

            if len(percentiles) > 0

            else 0

        )

        p90 = (

            percentiles[1]

            if len(percentiles) > 1

            else 0

        )

        s1, s2, s3, s4, s5 = st.columns(5)

        s1.metric(

            "Matching Rates",

            stats.get("count", 0)

        )

        s2.metric(

            "Average",

            f"${stats.get('average', 0):,.2f}"

        )

        s3.metric(

            "Median / P50",

            f"${median:,.2f}"

        )

        s4.metric(

            "P90",

            f"${p90:,.2f}"

        )

        s5.metric(

            "Range",

            (

                f"${stats.get('minimum', 0):,.2f} "

                f"- ${stats.get('maximum', 0):,.2f}"

            )

        )

        left, right = st.columns(

            [

                1.25,

                1

            ]

        )

        with left:

            st.markdown(

                '<div class="section-title">'

                'AVERAGE RATE BY FEE SOURCE'

                '</div>',

                unsafe_allow_html=True

            )

            source_rows = summary.get(

                "bySource",

                []

            )

            if source_rows:

                source_frame = pd.DataFrame([

                    {

                        "Fee Source":

                            row["_id"],

                        "Average Rate":

                            round(

                                row["averageRate"],

                                2

                            ),

                        "Minimum":

                            round(

                                row["minimumRate"],

                                2

                            ),

                        "Maximum":

                            round(

                                row["maximumRate"],

                                2

                            ),

                        "Records":

                            row["records"]

                    }

                    for row in source_rows

                ])

                st.bar_chart(

                    source_frame.set_index(

                        "Fee Source"

                    )[["Average Rate"]],

                    use_container_width=True

                )

                st.dataframe(

                    source_frame,

                    use_container_width=True,

                    hide_index=True,

                    height=220

                )

        with right:

            st.markdown(

                '<div class="section-title">'

                'AGGREGATION PIPELINE'

                '</div>',

                unsafe_allow_html=True

            )

            st.code(

                "$match\n"

                "   ↓\n"

                "$facet\n"

                "   ├─ $group  → avg / min / max\n"

                "   ├─ $percentile → P50 / P90\n"

                "   ├─ by source family\n"

                "   └─ by network\n\n"

                "Materialized view:\n"

                "$project → $set → $merge",

                language=None

            )

            st.markdown(

                '<div class="schema">'

                '<span class="warn">TFW CHECK:</span> '

                'One canonical MongoDB analytical view can be '

                'sliced across multiple RATE dimensions.'

                '</div>',

                unsafe_allow_html=True

            )

        st.markdown(

            '<div class="section-title">'

            'CANONICAL PRICING VIEW :: SAMPLE ROWS'

            '</div>',

            unsafe_allow_html=True

        )

        rows = canonical_rows()

        if rows:

            st.dataframe(

                pd.DataFrame(rows),

                use_container_width=True,

                hide_index=True,

                height=260

            )


# ============================================================

# OUTLIERS PANEL

# ============================================================

elif st.session_state.panel == "outliers":

    st.markdown(

        '<div class="section-title">'

        '04 :: PRICING OUTLIER ANALYSIS'

        '</div>',

        unsafe_allow_html=True

    )

    summary = run_multidimensional_summary(

        current_match

    )

    rows = run_outlier_analysis(

        current_match

    )

    median = 0

    if (

        summary

        and summary.get("summary")

    ):

        values = (

            summary["summary"][0]

            .get(

                "percentiles",

                [0]

            )

        )

        if values:

            median = values[0]

    if not rows:

        st.info(

            "No high-side pricing outliers found for the selected dimensions. "

            "Try Procedure 99213 / TX / All / All."

        )

    else:

        outlier_frame = pd.DataFrame(rows)

        outlier_frame["Rate"] = (

            outlier_frame["calculatedRate"]

            .round(2)

        )

        outlier_frame["Population Avg"] = (

            outlier_frame["populationAverage"]

            .round(2)

        )

        outlier_frame["Z Score"] = (

            outlier_frame["zScore"]

            .round(2)

        )

        if median:

            outlier_frame["Variance vs Median"] = (

                (

                    (

                        outlier_frame[

                            "calculatedRate"

                        ]

                        - median

                    )

                    / median

                )

                * 100

            ).round(1)

        display_columns = [

            "feeSchedule",

            "sourceType",

            "network",

            "providerType",

            "Rate",

            "Population Avg",

            "Z Score"

        ]

        if "Variance vs Median" in outlier_frame.columns:

            display_columns.append(

                "Variance vs Median"

            )

        o1, o2, o3 = st.columns(3)

        o1.metric(

            "Median",

            f"${median:,.2f}"

        )

        o2.metric(

            "High-Side Outliers",

            len(outlier_frame)

        )

        highest = (

            outlier_frame["Rate"].max()

            if not outlier_frame.empty

            else 0

        )

        o3.metric(

            "Highest Rate",

            f"${highest:,.2f}"

        )

        st.dataframe(

            outlier_frame[display_columns],

            use_container_width=True,

            hide_index=True,

            height=330

        )

        st.markdown(

            '<div class="schema">'

            '<span class="warn">CAPABILITY:</span> '

            '$setWindowFields calculates population context, '

            'then MongoDB identifies unusual pricing within '

            'the selected comparison population.'

            '</div>',

            unsafe_allow_html=True

        )


# ============================================================

# COMPARISON PANEL

# ============================================================

elif st.session_state.panel == "compare":

    st.markdown(

        '<div class="section-title">'

        '05 :: FEE SOURCE COMPARISON MATRIX'

        '</div>',

        unsafe_allow_html=True

    )

    matrix = fee_source_comparison(

        selected_procedure,

        selected_state,

        selected_year

    )

    if matrix.empty:

        st.warning(

            "No comparison data available."

        )

    else:

        formatted = matrix.copy()

        for column in formatted.columns:

            formatted[column] = (

                formatted[column]

                .map(

                    lambda value:

                        f"${value:,.2f}"

                        if pd.notna(value)

                        else "--"

                )

            )

        st.dataframe(

            formatted,

            use_container_width=True,

            height=230

        )

        st.markdown(

            '<div class="schema">'

            '<span class="warn">TFW CHECK:</span> '

            'RATE can compare one procedure across multiple '

            'networks and heterogeneous fee-source families '

            'using a single analytical representation.'

            '</div>',

            unsafe_allow_html=True

        )

        source_average = (

            matrix

            .mean(axis=0)

            .sort_values()

            .to_frame(

                name="Average Rate"

            )

        )

        st.markdown(

            '<div class="section-title">'

            'SOURCE FAMILY BENCHMARK'

            '</div>',

            unsafe_allow_html=True

        )

        st.bar_chart(

            source_average,

            use_container_width=True

        )


# ============================================================

# LOWER DASHBOARD / CONSOLE

# ============================================================

st.markdown(

    '<div class="section-title">'

    'DEMO CONSOLE / CAPABILITY TRACE'

    '</div>',

    unsafe_allow_html=True

)

console_left, console_right = st.columns(

    [

        1.25,

        1

    ]

)

with console_left:

    console = "\n".join(

        st.session_state.logs

    )

    st.markdown(

        f'<div class="terminal">'

        f'{console}'

        f'</div>',

        unsafe_allow_html=True

    )

with console_right:

    st.code(

        "CAPABILITY STATUS\n"

        "────────────────────────────────\n"

        f"FLEXIBLE DOCUMENT MODEL : {'READY' if source_count else 'WAIT'}\n"

        f"POLYMORPHIC SOURCES      : {'READY' if family_count else 'WAIT'}\n"

        f"AGGREGATION FRAMEWORK    : {'READY' if analytics_count else 'WAIT'}\n"

        f"$facet / $group          : {'READY' if analytics_count else 'WAIT'}\n"

        f"$percentile              : {'READY' if analytics_count else 'WAIT'}\n"

        f"$setWindowFields         : {'READY' if analytics_count else 'WAIT'}\n"

        f"$merge / MATERIALIZED    : {'READY' if analytics_count else 'WAIT'}\n"

        "\n"

        "NLP / HYBRID SEARCH      : SEPARATE DEMO",

        language=None

    )


# ============================================================

# FOOTER

# ============================================================

st.markdown(

    '<div class="schema">'

    '<span class="warn">RATE AUTOMATION TFW:</span> '

    'Flexible fee-source modeling → canonical analytical view → '

    'multidimensional aggregation → pricing comparison → outlier analysis'

    '</div>',

    unsafe_allow_html=True

)
