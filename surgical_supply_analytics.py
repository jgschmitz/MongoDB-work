from __future__ import annotations

import html
import json
import math
import random
import time
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import streamlit as st
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Surgical Supply Analytics",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
#
# Paste the Atlas URI below. Nothing else is required.
# ============================================================

MONGODB_URI = ""

DATABASE_NAME = "surgical_supply_analytics_demo"
CASES_COLLECTION = "surgical_cases"
ROLLUPS_COLLECTION = "monthly_supply_rollups"

SEED_CASE_COUNT = 15000
SEED_RANDOM = 20261015

client = (
    MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        appname="surgical-supply-analytics-demo",
    )
    if MONGODB_URI
    else None
)

db = client[DATABASE_NAME] if client else None
cases_collection = db[CASES_COLLECTION] if db is not None else None
rollups_collection = db[ROLLUPS_COLLECTION] if db is not None else None


# ============================================================
# DEMO REFERENCE DATA
# ============================================================

FACILITIES = [
    {
        "id": "FAC-CHI-01",
        "name": "Lakeshore University Hospital",
        "market": "Chicago",
        "region": "Midwest",
        "costFactor": 1.03,
    },
    {
        "id": "FAC-CHI-02",
        "name": "Northwestern Surgical Center",
        "market": "Chicago",
        "region": "Midwest",
        "costFactor": 0.94,
    },
    {
        "id": "FAC-CHI-03",
        "name": "Metro Regional Medical Center",
        "market": "Chicago",
        "region": "Midwest",
        "costFactor": 1.12,
    },
    {
        "id": "FAC-MKE-01",
        "name": "Lakefront Medical Pavilion",
        "market": "Milwaukee",
        "region": "Midwest",
        "costFactor": 0.91,
    },
    {
        "id": "FAC-MSP-01",
        "name": "North Star Surgical Institute",
        "market": "Minneapolis",
        "region": "Midwest",
        "costFactor": 1.06,
    },
    {
        "id": "FAC-STL-01",
        "name": "Gateway Academic Hospital",
        "market": "St. Louis",
        "region": "Central",
        "costFactor": 0.98,
    },
]

SURGEONS = [
    ("SUR-001", "Dr. Maya Patel", "Orthopedic Surgery", 1.18),
    ("SUR-002", "Dr. Andrew Kim", "Orthopedic Surgery", 0.91),
    ("SUR-003", "Dr. Elena Rodriguez", "Orthopedic Surgery", 1.04),
    ("SUR-004", "Dr. Marcus Chen", "Cardiothoracic Surgery", 1.11),
    ("SUR-005", "Dr. Priya Nair", "Cardiothoracic Surgery", 0.96),
    ("SUR-006", "Dr. Jordan Brooks", "General Surgery", 1.02),
    ("SUR-007", "Dr. Simone Harris", "General Surgery", 0.89),
    ("SUR-008", "Dr. Daniel Nguyen", "Neurological Surgery", 1.22),
    ("SUR-009", "Dr. Rachel Stein", "Neurological Surgery", 1.06),
    ("SUR-010", "Dr. Omar Hassan", "Orthopedic Surgery", 0.95),
    ("SUR-011", "Dr. Grace Lee", "General Surgery", 1.08),
    ("SUR-012", "Dr. Noah Williams", "Orthopedic Surgery", 1.01),
    ("SUR-013", "Dr. Sofia Martinez", "Cardiothoracic Surgery", 0.93),
    ("SUR-014", "Dr. Ethan Clarke", "Neurological Surgery", 1.14),
    ("SUR-015", "Dr. Aisha Thompson", "General Surgery", 0.97),
    ("SUR-016", "Dr. Liam O'Connor", "Orthopedic Surgery", 1.09),
    ("SUR-017", "Dr. Neha Shah", "General Surgery", 1.00),
    ("SUR-018", "Dr. Benjamin Park", "Orthopedic Surgery", 0.88),
]

PROCEDURES = [
    {
        "code": "TKA",
        "name": "Total Knee Arthroplasty",
        "category": "Orthopedics",
        "specialty": "Orthopedic Surgery",
        "baseCost": 5100.0,
        "weight": 24,
    },
    {
        "code": "THA",
        "name": "Total Hip Arthroplasty",
        "category": "Orthopedics",
        "specialty": "Orthopedic Surgery",
        "baseCost": 4750.0,
        "weight": 20,
    },
    {
        "code": "CABG",
        "name": "Coronary Artery Bypass Graft",
        "category": "Cardiac",
        "specialty": "Cardiothoracic Surgery",
        "baseCost": 8400.0,
        "weight": 13,
    },
    {
        "code": "LAP-CHOLE",
        "name": "Laparoscopic Cholecystectomy",
        "category": "General Surgery",
        "specialty": "General Surgery",
        "baseCost": 1350.0,
        "weight": 21,
    },
    {
        "code": "SP-FUS",
        "name": "Lumbar Spinal Fusion",
        "category": "Neurosurgery",
        "specialty": "Neurological Surgery",
        "baseCost": 11200.0,
        "weight": 10,
    },
    {
        "code": "COLECT",
        "name": "Laparoscopic Colectomy",
        "category": "General Surgery",
        "specialty": "General Surgery",
        "baseCost": 2950.0,
        "weight": 12,
    },
]

SUPPLY_TEMPLATES = {
    "Orthopedics": [
        ("Implant", "Joint implant system", "OrthoMotion", 2950.0, 1),
        ("Implant", "Bone cement kit", "SurgiBond", 380.0, 1),
        ("Disposable", "Pulsed lavage set", "ClearFlow", 145.0, 1),
        ("Disposable", "Sterile drape pack", "MedWeave", 92.0, 1),
        ("Instrument", "Single-use cutting guide", "PrecisionEdge", 310.0, 1),
        ("Wound closure", "Antimicrobial closure kit", "SurgiBond", 118.0, 1),
    ],
    "Cardiac": [
        ("Implant", "Bypass graft set", "CardioCore", 2650.0, 1),
        ("Implant", "Sternal fixation system", "TitanMed", 1450.0, 1),
        ("Disposable", "Perfusion tubing pack", "ClearFlow", 880.0, 1),
        ("Disposable", "Cardiac drape pack", "MedWeave", 135.0, 1),
        ("Instrument", "Vessel harvesting device", "PrecisionEdge", 1150.0, 1),
        ("Wound closure", "Sternal closure wires", "SurgiBond", 210.0, 1),
    ],
    "General Surgery": [
        ("Implant", "Hemostatic clip cartridge", "SurgiBond", 185.0, 2),
        ("Disposable", "Laparoscopic trocar set", "ClearFlow", 230.0, 1),
        ("Disposable", "Insufflation tubing", "ClearFlow", 62.0, 1),
        ("Instrument", "Advanced energy device", "PrecisionEdge", 470.0, 1),
        ("Wound closure", "Barbed suture kit", "SurgiBond", 96.0, 1),
        ("Medication", "Topical hemostatic matrix", "BioSeal", 245.0, 1),
    ],
    "Neurosurgery": [
        ("Implant", "Spinal fixation system", "NeuroAxis", 6200.0, 1),
        ("Implant", "Interbody fusion cage", "TitanMed", 2450.0, 1),
        ("Disposable", "Neuromonitoring lead set", "SignalPath", 780.0, 1),
        ("Disposable", "Sterile spine drape pack", "MedWeave", 155.0, 1),
        ("Instrument", "High-speed burr", "PrecisionEdge", 460.0, 1),
        ("Wound closure", "Dural closure kit", "BioSeal", 520.0, 1),
    ],
}

RISK_FACTORS = {
    "Low": 0.94,
    "Moderate": 1.00,
    "High": 1.10,
    "Complex": 1.22,
}


# ============================================================
# SAFE ANALYTICAL DICTIONARY
#
# Runtime choices select only from these definitions. User input never
# becomes a field path, operator, or executable pipeline fragment.
# ============================================================

DIMENSIONS = {
    "Surgeon": {
        "expression": "$surgeon.name",
        "idExpression": "$surgeon.id",
        "field": "surgeon.name",
    },
    "Facility": {
        "expression": "$facility.name",
        "idExpression": "$facility.id",
        "field": "facility.name",
    },
    "Procedure": {
        "expression": "$procedure.name",
        "idExpression": "$procedure.code",
        "field": "procedure.name",
    },
    "Market": {
        "expression": "$facility.market",
        "idExpression": "$facility.market",
        "field": "facility.market",
    },
    "Region": {
        "expression": "$facility.region",
        "idExpression": "$facility.region",
        "field": "facility.region",
    },
    "Supply category": {
        "expression": "$supplies.category",
        "idExpression": "$supplies.category",
        "field": "supplies.category",
    },
    "Manufacturer": {
        "expression": "$supplies.manufacturer",
        "idExpression": "$supplies.manufacturer",
        "field": "supplies.manufacturer",
    },
    "Month": {
        "expression": {
            "$dateToString": {
                "format": "%Y-%m",
                "date": "$procedureDate",
            }
        },
        "idExpression": {
            "$dateToString": {
                "format": "%Y-%m",
                "date": "$procedureDate",
            }
        },
        "field": "procedureDate",
    },
}

MEASURES = {
    "Average supply cost per case": {
        "caseAccumulator": {"$sum": "$supplies.extendedCost"},
        "groupAccumulator": {"$avg": "$caseMetric"},
        "format": "currency",
        "description": "Average selected supply spend across completed cases.",
    },
    "Total supply spend": {
        "caseAccumulator": {"$sum": "$supplies.extendedCost"},
        "groupAccumulator": {"$sum": "$caseMetric"},
        "format": "currency",
        "description": "Total selected supply spend across completed cases.",
    },
    "Average supply units per case": {
        "caseAccumulator": {"$sum": "$supplies.quantity"},
        "groupAccumulator": {"$avg": "$caseMetric"},
        "format": "number",
        "description": "Average quantity of selected supplies used per case.",
    },
    "Average line items per case": {
        "caseAccumulator": {"$sum": 1},
        "groupAccumulator": {"$avg": "$caseMetric"},
        "format": "number",
        "description": "Average number of selected supply lines per case.",
    },
}

STAGE_DESCRIPTIONS = {
    "$match": "Apply only validated date, procedure, facility, risk, and supply filters.",
    "$unwind": "Expand each case's embedded supply array for supply-level calculations.",
    "$group": "Calculate each case metric, then aggregate it by the selected analytical dimension.",
    "$set": "Shape labels and calculate variance, percentage variance, and z-score.",
    "$setWindowFields": "Calculate peer benchmark, dispersion, and rank without leaving the pipeline.",
    "$sort": "Order the groups by the selected outlier signal.",
    "$facet": "Return detailed rows, chart-ready outliers, and summary KPIs in one response.",
}


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "logs": [
        "[BOOT] Surgical Supply Analytics Lab",
        f"[BOOT] database={DATABASE_NAME}",
        "[BOOT] mode=Atlas Aggregation Framework only",
    ],
    "last_latency": None,
    "last_pipeline": [],
    "last_results": [],
    "last_summary": {},
    "last_config": {},
    "comparison": None,
}

for state_key, state_value in DEFAULT_STATE.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = state_value


def add_log(message: str) -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{stamp}] {message}")
    st.session_state.logs = st.session_state.logs[-150:]


# ============================================================
# SYNTHETIC DATA GENERATION
# ============================================================

def weighted_choice(rng: random.Random, rows: list[dict]) -> dict:
    return rng.choices(
        rows,
        weights=[row["weight"] for row in rows],
        k=1,
    )[0]


def surgeon_documents() -> list[dict]:
    return [
        {
            "id": surgeon_id,
            "name": name,
            "specialty": specialty,
            "preferenceFactor": preference_factor,
        }
        for surgeon_id, name, specialty, preference_factor in SURGEONS
    ]


def build_supply_lines(
    rng: random.Random,
    procedure: dict,
    facility: dict,
    surgeon: dict,
    risk_band: str,
) -> list[dict]:
    lines = []
    templates = SUPPLY_TEMPLATES[procedure["category"]]

    for index, (
        category,
        product_name,
        manufacturer,
        base_unit_cost,
        base_quantity,
    ) in enumerate(templates, start=1):
        include_probability = 0.98 if category == "Implant" else 0.87

        if rng.random() > include_probability:
            continue

        quantity = base_quantity
        if category in {"Disposable", "Medication", "Wound closure"}:
            quantity += rng.choices([0, 1, 2], weights=[72, 23, 5], k=1)[0]

        category_factor = (
            surgeon["preferenceFactor"]
            if category in {"Implant", "Instrument"}
            else 1.0 + ((surgeon["preferenceFactor"] - 1.0) * 0.28)
        )
        variation = rng.uniform(0.94, 1.07)
        risk_factor = 1.0 + ((RISK_FACTORS[risk_band] - 1.0) * 0.22)
        unit_cost = round(
            base_unit_cost
            * facility["costFactor"]
            * category_factor
            * variation
            * risk_factor,
            2,
        )
        extended_cost = round(unit_cost * quantity, 2)

        lines.append(
            {
                "sku": f"{procedure['code']}-{index:02d}",
                "name": product_name,
                "category": category,
                "manufacturer": manufacturer,
                "quantity": quantity,
                "unitCost": unit_cost,
                "extendedCost": extended_cost,
                "contractStatus": rng.choices(
                    ["contracted", "preferred", "exception"],
                    weights=[76, 18, 6],
                    k=1,
                )[0],
            }
        )

    return lines


def generate_case_documents(count: int) -> list[dict]:
    rng = random.Random(SEED_RANDOM)
    surgeons = surgeon_documents()
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    date_span_days = 620
    documents = []

    for case_number in range(1, count + 1):
        procedure = weighted_choice(rng, PROCEDURES)
        eligible_surgeons = [
            surgeon
            for surgeon in surgeons
            if surgeon["specialty"] == procedure["specialty"]
        ]
        surgeon = rng.choice(eligible_surgeons)
        facility = rng.choice(FACILITIES)
        risk_band = rng.choices(
            list(RISK_FACTORS),
            weights=[30, 43, 21, 6],
            k=1,
        )[0]
        procedure_date = start_date + timedelta(
            days=rng.randrange(date_span_days),
            hours=rng.randrange(6, 19),
            minutes=rng.randrange(0, 60),
        )
        supplies = build_supply_lines(
            rng,
            procedure,
            facility,
            surgeon,
            risk_band,
        )
        total_supply_cost = round(
            sum(item["extendedCost"] for item in supplies),
            2,
        )

        documents.append(
            {
                "_id": f"CASE-{case_number:07d}",
                "procedureDate": procedure_date,
                "facility": {
                    "id": facility["id"],
                    "name": facility["name"],
                    "market": facility["market"],
                    "region": facility["region"],
                },
                "surgeon": {
                    "id": surgeon["id"],
                    "name": surgeon["name"],
                    "specialty": surgeon["specialty"],
                },
                "procedure": {
                    "code": procedure["code"],
                    "name": procedure["name"],
                    "category": procedure["category"],
                },
                "patientRiskBand": risk_band,
                "caseStatus": "completed",
                "supplies": supplies,
                "supplyLineCount": len(supplies),
                "totalSupplyCost": total_supply_cost,
                "createdAt": datetime.now(timezone.utc),
                "dataClassification": "synthetic-demo-data",
            }
        )

    return documents


# ============================================================
# ATLAS OPERATIONS
# ============================================================

def atlas_status() -> tuple[bool, str]:
    if client is None:
        return False, "MONGODB_URI NOT CONFIGURED"

    try:
        result = client.admin.command("ping")
        return bool(result.get("ok")), "ATLAS CONNECTED"
    except Exception as exc:
        return False, str(exc)


def collection_count(collection) -> int:
    if collection is None:
        return 0

    try:
        return collection.estimated_document_count()
    except PyMongoError:
        return 0


def create_standard_indexes() -> None:
    existing_case_indexes = cases_collection.index_information()
    existing_rollup_indexes = rollups_collection.index_information()

    case_indexes = [
        (
            "case_date_procedure_facility",
            [
                ("procedureDate", ASCENDING),
                ("procedure.code", ASCENDING),
                ("facility.id", ASCENDING),
            ],
        ),
        (
            "case_surgeon_date",
            [
                ("surgeon.id", ASCENDING),
                ("procedureDate", ASCENDING),
            ],
        ),
        (
            "case_market_procedure",
            [
                ("facility.market", ASCENDING),
                ("procedure.code", ASCENDING),
            ],
        ),
        (
            "case_supply_category",
            [
                ("supplies.category", ASCENDING),
            ],
        ),
    ]

    rollup_indexes = [
        (
            "rollup_lookup",
            [
                ("procedureCode", ASCENDING),
                ("supplyCategory", ASCENDING),
                ("facilityId", ASCENDING),
                ("month", ASCENDING),
            ],
        ),
        (
            "rollup_month_market",
            [
                ("month", ASCENDING),
                ("market", ASCENDING),
            ],
        ),
    ]

    for name, keys in case_indexes:
        if name not in existing_case_indexes:
            cases_collection.create_index(keys, name=name)
            add_log(f"INDEX created cases.{name}")
        else:
            add_log(f"INDEX exists cases.{name}")

    for name, keys in rollup_indexes:
        if name not in existing_rollup_indexes:
            rollups_collection.create_index(keys, name=name)
            add_log(f"INDEX created rollups.{name}")
        else:
            add_log(f"INDEX exists rollups.{name}")


def rebuild_rollups() -> int:
    rollups_collection.delete_many({})

    pipeline = [
        {"$unwind": "$supplies"},
        {
            "$group": {
                "_id": {
                    "month": {
                        "$dateTrunc": {
                            "date": "$procedureDate",
                            "unit": "month",
                        }
                    },
                    "facilityId": "$facility.id",
                    "facilityName": "$facility.name",
                    "market": "$facility.market",
                    "region": "$facility.region",
                    "procedureCode": "$procedure.code",
                    "procedureName": "$procedure.name",
                    "supplyCategory": "$supplies.category",
                },
                "totalSpend": {"$sum": "$supplies.extendedCost"},
                "totalUnits": {"$sum": "$supplies.quantity"},
                "caseIds": {"$addToSet": "$_id"},
                "supplyLines": {"$sum": 1},
            }
        },
        {
            "$set": {
                "month": "$_id.month",
                "facilityId": "$_id.facilityId",
                "facilityName": "$_id.facilityName",
                "market": "$_id.market",
                "region": "$_id.region",
                "procedureCode": "$_id.procedureCode",
                "procedureName": "$_id.procedureName",
                "supplyCategory": "$_id.supplyCategory",
                "caseCount": {"$size": "$caseIds"},
                "averageCostPerCase": {
                    "$cond": [
                        {"$gt": [{"$size": "$caseIds"}, 0]},
                        {
                            "$divide": [
                                "$totalSpend",
                                {"$size": "$caseIds"},
                            ]
                        },
                        0,
                    ]
                },
                "refreshedAt": "$$NOW",
            }
        },
        {"$unset": ["caseIds"]},
        {
            "$merge": {
                "into": ROLLUPS_COLLECTION,
                "on": "_id",
                "whenMatched": "replace",
                "whenNotMatched": "insert",
            }
        },
    ]

    list(cases_collection.aggregate(pipeline, allowDiskUse=True))
    return rollups_collection.count_documents({})


def seed_demo() -> bool:
    if cases_collection is None or rollups_collection is None:
        add_log("ERROR Atlas connection not configured")
        return False

    started = time.perf_counter()

    try:
        add_log(f"SEED generating {SEED_CASE_COUNT:,} surgical cases")
        documents = generate_case_documents(SEED_CASE_COUNT)

        cases_collection.delete_many({})
        rollups_collection.delete_many({})

        batch_size = 1000
        for offset in range(0, len(documents), batch_size):
            batch = documents[offset : offset + batch_size]
            cases_collection.insert_many(batch, ordered=False)

        create_standard_indexes()
        rollup_count = rebuild_rollups()

        elapsed = time.perf_counter() - started
        st.session_state.last_latency = elapsed
        st.session_state.last_pipeline = []
        st.session_state.last_results = []
        st.session_state.last_summary = {}
        st.session_state.comparison = None

        add_log(
            f"OK seed cases={len(documents):,} "
            f"rollups={rollup_count:,} latency={elapsed:.3f}s"
        )
        return True

    except PyMongoError as exc:
        add_log(f"ERROR seed failed: {exc}")
        st.error(f"Seed failed: {exc}")
        return False


def reset_demo() -> bool:
    if cases_collection is None or rollups_collection is None:
        return False

    try:
        cases_collection.delete_many({})
        rollups_collection.delete_many({})
        st.session_state.last_pipeline = []
        st.session_state.last_results = []
        st.session_state.last_summary = {}
        st.session_state.comparison = None
        add_log("OK demo data cleared; standard indexes preserved")
        return True
    except PyMongoError as exc:
        add_log(f"ERROR reset failed: {exc}")
        return False


# ============================================================
# SAFE PIPELINE COMPILER
# ============================================================

def validate_analysis_config(config: dict) -> list[str]:
    errors = []

    if config["groupDimension"] not in DIMENSIONS:
        errors.append("Unsupported grouping dimension.")
    if config["benchmarkDimension"] not in DIMENSIONS:
        errors.append("Unsupported benchmark dimension.")
    if config["measure"] not in MEASURES:
        errors.append("Unsupported measure.")
    if config["groupDimension"] == config["benchmarkDimension"]:
        errors.append("Group and benchmark dimensions must be different.")
    if config["startDate"] > config["endDate"]:
        errors.append("Start date must be before end date.")
    if not 1 <= config["minimumCases"] <= 10000:
        errors.append("Minimum case volume is outside the allowed range.")
    if not 0 <= config["outlierThreshold"] <= 500:
        errors.append("Outlier threshold is outside the allowed range.")

    return errors


def build_match_stage(config: dict) -> dict:
    match = {
        "caseStatus": "completed",
        "procedureDate": {
            "$gte": datetime.combine(
                config["startDate"],
                datetime.min.time(),
                tzinfo=timezone.utc,
            ),
            "$lte": datetime.combine(
                config["endDate"],
                datetime.max.time(),
                tzinfo=timezone.utc,
            ),
        },
    }

    if config["procedureCodes"]:
        match["procedure.code"] = {"$in": config["procedureCodes"]}
    if config["facilityIds"]:
        match["facility.id"] = {"$in": config["facilityIds"]}
    if config["markets"]:
        match["facility.market"] = {"$in": config["markets"]}
    if config["riskBands"]:
        match["patientRiskBand"] = {"$in": config["riskBands"]}

    return {"$match": match}


def build_analysis_pipeline(config: dict) -> list[dict]:
    errors = validate_analysis_config(config)
    if errors:
        raise ValueError(" ".join(errors))

    group_definition = DIMENSIONS[config["groupDimension"]]
    benchmark_definition = DIMENSIONS[config["benchmarkDimension"]]
    measure_definition = MEASURES[config["measure"]]

    pipeline = [
        build_match_stage(config),
        {"$unwind": "$supplies"},
    ]

    if config["supplyCategories"]:
        pipeline.append(
            {
                "$match": {
                    "supplies.category": {
                        "$in": config["supplyCategories"]
                    }
                }
            }
        )

    pipeline.extend(
        [
            {
                "$group": {
                    "_id": {
                        "caseId": "$_id",
                        "groupId": group_definition["idExpression"],
                        "groupLabel": group_definition["expression"],
                        "benchmarkId": benchmark_definition["idExpression"],
                        "benchmarkLabel": benchmark_definition["expression"],
                    },
                    "caseMetric": measure_definition["caseAccumulator"],
                    "caseSpend": {"$sum": "$supplies.extendedCost"},
                    "caseUnits": {"$sum": "$supplies.quantity"},
                    "lineItems": {"$sum": 1},
                }
            },
            {
                "$group": {
                    "_id": {
                        "groupId": "$_id.groupId",
                        "groupLabel": "$_id.groupLabel",
                        "benchmarkId": "$_id.benchmarkId",
                        "benchmarkLabel": "$_id.benchmarkLabel",
                    },
                    "metricValue": measure_definition["groupAccumulator"],
                    "caseCount": {"$sum": 1},
                    "totalSpend": {"$sum": "$caseSpend"},
                    "totalUnits": {"$sum": "$caseUnits"},
                    "lineItems": {"$sum": "$lineItems"},
                    "minimumCaseMetric": {"$min": "$caseMetric"},
                    "maximumCaseMetric": {"$max": "$caseMetric"},
                }
            },
            {
                "$match": {
                    "caseCount": {"$gte": config["minimumCases"]}
                }
            },
            {
                "$set": {
                    "groupId": "$_id.groupId",
                    "groupLabel": "$_id.groupLabel",
                    "benchmarkId": "$_id.benchmarkId",
                    "benchmarkLabel": "$_id.benchmarkLabel",
                }
            },
            {
                "$setWindowFields": {
                    "partitionBy": "$benchmarkId",
                    "sortBy": {"metricValue": -1},
                    "output": {
                        "peerAverage": {
                            "$avg": "$metricValue",
                            "window": {
                                "documents": ["unbounded", "unbounded"]
                            },
                        },
                        "peerStdDev": {
                            "$stdDevPop": "$metricValue",
                            "window": {
                                "documents": ["unbounded", "unbounded"]
                            },
                        },
                        "peerMinimum": {
                            "$min": "$metricValue",
                            "window": {
                                "documents": ["unbounded", "unbounded"]
                            },
                        },
                        "peerMaximum": {
                            "$max": "$metricValue",
                            "window": {
                                "documents": ["unbounded", "unbounded"]
                            },
                        },
                        "peerRank": {"$rank": {}},
                    },
                }
            },
            {
                "$set": {
                    "variance": {"$subtract": ["$metricValue", "$peerAverage"]},
                    "variancePct": {
                        "$cond": [
                            {"$ne": ["$peerAverage", 0]},
                            {
                                "$multiply": [
                                    {
                                        "$divide": [
                                            {"$subtract": ["$metricValue", "$peerAverage"]},
                                            "$peerAverage",
                                        ]
                                    },
                                    100,
                                ]
                            },
                            0,
                        ]
                    },
                    "zScore": {
                        "$cond": [
                            {"$gt": ["$peerStdDev", 0]},
                            {
                                "$divide": [
                                    {"$subtract": ["$metricValue", "$peerAverage"]},
                                    "$peerStdDev",
                                ]
                            },
                            0,
                        ]
                    },
                }
            },
            {"$sort": {"variancePct": -1, "caseCount": -1}},
            {
                "$facet": {
                    "results": [
                        {"$limit": 100},
                        {
                            "$project": {
                                "_id": 0,
                                "groupId": 1,
                                "groupLabel": 1,
                                "benchmarkId": 1,
                                "benchmarkLabel": 1,
                                "metricValue": {"$round": ["$metricValue", 2]},
                                "peerAverage": {"$round": ["$peerAverage", 2]},
                                "variance": {"$round": ["$variance", 2]},
                                "variancePct": {"$round": ["$variancePct", 2]},
                                "zScore": {"$round": ["$zScore", 2]},
                                "peerRank": 1,
                                "caseCount": 1,
                                "totalSpend": {"$round": ["$totalSpend", 2]},
                                "totalUnits": 1,
                                "lineItems": 1,
                                "minimumCaseMetric": {
                                    "$round": ["$minimumCaseMetric", 2]
                                },
                                "maximumCaseMetric": {
                                    "$round": ["$maximumCaseMetric", 2]
                                },
                                "isOutlier": {
                                    "$gte": [
                                        {"$abs": "$variancePct"},
                                        config["outlierThreshold"],
                                    ]
                                },
                            }
                        },
                    ],
                    "outliers": [
                        {
                            "$match": {
                                "$expr": {
                                    "$gte": [
                                        {"$abs": "$variancePct"},
                                        config["outlierThreshold"],
                                    ]
                                }
                            }
                        },
                        {"$count": "count"},
                    ],
                    "summary": [
                        {
                            "$group": {
                                "_id": None,
                                "groups": {"$sum": 1},
                                "cases": {"$sum": "$caseCount"},
                                "spend": {"$sum": "$totalSpend"},
                                "averageMetric": {"$avg": "$metricValue"},
                                "largestPositiveVariance": {"$max": "$variancePct"},
                                "largestNegativeVariance": {"$min": "$variancePct"},
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "groups": 1,
                                "cases": 1,
                                "spend": {"$round": ["$spend", 2]},
                                "averageMetric": {
                                    "$round": ["$averageMetric", 2]
                                },
                                "largestPositiveVariance": {
                                    "$round": ["$largestPositiveVariance", 2]
                                },
                                "largestNegativeVariance": {
                                    "$round": ["$largestNegativeVariance", 2]
                                },
                            }
                        },
                    ],
                }
            },
        ]
    )

    return pipeline


def run_analysis(config: dict) -> tuple[list, dict, list, float]:
    pipeline = build_analysis_pipeline(config)
    started = time.perf_counter()
    response = list(
        cases_collection.aggregate(
            pipeline,
            allowDiskUse=True,
            maxTimeMS=30000,
        )
    )
    latency = time.perf_counter() - started

    payload = response[0] if response else {}
    results = payload.get("results", [])
    summary_rows = payload.get("summary", [])
    summary = summary_rows[0] if summary_rows else {}
    outlier_rows = payload.get("outliers", [])
    summary["outliers"] = outlier_rows[0]["count"] if outlier_rows else 0

    return results, summary, pipeline, latency


def build_raw_comparison_pipeline(
    procedure_code: str,
    supply_category: str,
) -> list[dict]:
    return [
        {
            "$match": {
                "caseStatus": "completed",
                "procedure.code": procedure_code,
            }
        },
        {"$unwind": "$supplies"},
        {"$match": {"supplies.category": supply_category}},
        {
            "$group": {
                "_id": {
                    "caseId": "$_id",
                    "facilityId": "$facility.id",
                    "facilityName": "$facility.name",
                },
                "caseSpend": {"$sum": "$supplies.extendedCost"},
            }
        },
        {
            "$group": {
                "_id": {
                    "facilityId": "$_id.facilityId",
                    "facilityName": "$_id.facilityName",
                },
                "totalSpend": {"$sum": "$caseSpend"},
                "caseCount": {"$sum": 1},
                "averageCostPerCase": {"$avg": "$caseSpend"},
            }
        },
        {"$sort": {"averageCostPerCase": -1}},
    ]


def build_rollup_comparison_pipeline(
    procedure_code: str,
    supply_category: str,
) -> list[dict]:
    return [
        {
            "$match": {
                "procedureCode": procedure_code,
                "supplyCategory": supply_category,
            }
        },
        {
            "$group": {
                "_id": {
                    "facilityId": "$facilityId",
                    "facilityName": "$facilityName",
                },
                "totalSpend": {"$sum": "$totalSpend"},
                "caseCount": {"$sum": "$caseCount"},
            }
        },
        {
            "$set": {
                "averageCostPerCase": {
                    "$cond": [
                        {"$gt": ["$caseCount", 0]},
                        {"$divide": ["$totalSpend", "$caseCount"]},
                        0,
                    ]
                }
            }
        },
        {"$sort": {"averageCostPerCase": -1}},
    ]


def run_raw_vs_rollup(
    procedure_code: str,
    supply_category: str,
) -> dict:
    raw_pipeline = build_raw_comparison_pipeline(
        procedure_code,
        supply_category,
    )
    rollup_pipeline = build_rollup_comparison_pipeline(
        procedure_code,
        supply_category,
    )

    raw_started = time.perf_counter()
    raw_results = list(
        cases_collection.aggregate(
            raw_pipeline,
            allowDiskUse=True,
            maxTimeMS=30000,
        )
    )
    raw_latency = time.perf_counter() - raw_started

    rollup_started = time.perf_counter()
    rollup_results = list(
        rollups_collection.aggregate(
            rollup_pipeline,
            allowDiskUse=True,
            maxTimeMS=30000,
        )
    )
    rollup_latency = time.perf_counter() - rollup_started

    raw_by_facility = {
        row["_id"]["facilityId"]: row
        for row in raw_results
    }
    rollup_by_facility = {
        row["_id"]["facilityId"]: row
        for row in rollup_results
    }
    validation = []

    for facility_id in sorted(
        set(raw_by_facility) | set(rollup_by_facility)
    ):
        raw_row = raw_by_facility.get(facility_id, {})
        rollup_row = rollup_by_facility.get(facility_id, {})
        raw_average = raw_row.get("averageCostPerCase", 0)
        rollup_average = rollup_row.get("averageCostPerCase", 0)
        delta = abs(raw_average - rollup_average)
        validation.append(
            {
                "Facility": (
                    raw_row.get("_id", {}).get("facilityName")
                    or rollup_row.get("_id", {}).get("facilityName")
                ),
                "Raw average": round(raw_average, 2),
                "Rollup average": round(rollup_average, 2),
                "Absolute delta": round(delta, 6),
            }
        )

    return {
        "rawPipeline": raw_pipeline,
        "rollupPipeline": rollup_pipeline,
        "rawResults": raw_results,
        "rollupResults": rollup_results,
        "rawLatency": raw_latency,
        "rollupLatency": rollup_latency,
        "speedup": (
            raw_latency / rollup_latency
            if rollup_latency > 0
            else math.inf
        ),
        "validation": validation,
    }


def pipeline_for_display(pipeline: list[dict]) -> list[dict]:
    return json.loads(json.dumps(pipeline, default=str))


def format_metric(value: float, format_name: str) -> str:
    if format_name == "currency":
        return f"${value:,.2f}"
    return f"{value:,.2f}"


def result_dataframe(results: list[dict], measure_format: str) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "Group": result.get("groupLabel"),
                "Peer benchmark": result.get("benchmarkLabel"),
                "Metric": result.get("metricValue", 0),
                "Peer average": result.get("peerAverage", 0),
                "Variance": result.get("variance", 0),
                "Variance %": result.get("variancePct", 0),
                "Z-score": result.get("zScore", 0),
                "Peer rank": result.get("peerRank", 0),
                "Cases": result.get("caseCount", 0),
                "Total spend": result.get("totalSpend", 0),
                "Outlier": "YES" if result.get("isOutlier") else "NO",
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    if measure_format == "currency":
        frame["Metric display"] = frame["Metric"].map(lambda x: f"${x:,.2f}")
        frame["Peer display"] = frame["Peer average"].map(
            lambda x: f"${x:,.2f}"
        )
    else:
        frame["Metric display"] = frame["Metric"].map(lambda x: f"{x:,.2f}")
        frame["Peer display"] = frame["Peer average"].map(
            lambda x: f"{x:,.2f}"
        )

    return frame


# ============================================================
# VERCEL-INSPIRED UI
# ============================================================

st.markdown(
    """
<style>
:root {
    --background: #000000;
    --panel: #0a0a0a;
    --panel-2: #111111;
    --border: #262626;
    --border-bright: #525252;
    --text: #ededed;
    --muted: #8f8f8f;
    --white: #ffffff;
    --green: #00ed64;
    --red: #ff4d4f;
    --amber: #f5a623;
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
    background-color: var(--background) !important;
    background-image:
        linear-gradient(rgba(255,255,255,.027) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.027) 1px, transparent 1px);
    background-size: 34px 34px;
    color: var(--text) !important;
}

[data-testid="stSidebar"] {
    background: #050505 !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--text);
}

.block-container {
    max-width: 1550px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

.hero {
    position: relative;
    overflow: hidden;
    padding: 34px 36px 30px;
    margin-bottom: 14px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background:
        radial-gradient(circle at 80% -20%, rgba(255,255,255,.11), transparent 34%),
        #050505;
}

.hero-kicker,
.eyebrow {
    color: var(--muted);
    font: 600 11px/1.2 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    letter-spacing: .12em;
    text-transform: uppercase;
}

.hero-title {
    margin: 12px 0 8px;
    color: var(--white);
    font: 650 38px/1.08 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    letter-spacing: -.045em;
}

.hero-subtitle {
    max-width: 930px;
    color: #b5b5b5;
    font: 400 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.status-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0 18px;
}

.status-pill {
    padding: 7px 10px;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: rgba(0,0,0,.86);
    color: #bfbfbf;
    font: 11px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.section-label {
    margin: 20px 0 10px;
    color: var(--white);
    font: 650 13px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    letter-spacing: .06em;
    text-transform: uppercase;
}

.card {
    min-height: 112px;
    padding: 16px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: rgba(10,10,10,.92);
}

.card-label {
    color: var(--muted);
    font: 11px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    letter-spacing: .05em;
    text-transform: uppercase;
}

.card-value {
    margin-top: 9px;
    color: var(--white);
    font: 650 27px/1.1 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    letter-spacing: -.035em;
}

.card-detail {
    margin-top: 7px;
    color: var(--muted);
    font: 12px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.stage-card {
    padding: 13px 15px;
    margin: 7px 0;
    border: 1px solid var(--border);
    border-left: 3px solid var(--white);
    border-radius: 7px;
    background: #080808;
}

.stage-number {
    color: var(--muted);
    font: 10px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.stage-name {
    margin-top: 3px;
    color: var(--white);
    font: 650 15px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.stage-copy {
    margin-top: 5px;
    color: #9f9f9f;
    font: 12px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.safety-box {
    padding: 16px 18px;
    border: 1px solid #2d2d2d;
    border-radius: 9px;
    background: linear-gradient(135deg, #090909, #111111);
    color: #c7c7c7;
    font: 13px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.log-window {
    height: 220px;
    overflow-y: auto;
    padding: 13px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: #050505;
    color: #b5b5b5;
    font: 11px/1.55 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    white-space: pre-wrap;
}

.connected {
    color: var(--green) !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.disconnected {
    color: var(--red) !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

div.stButton > button {
    min-height: 42px;
    border: 1px solid var(--white) !important;
    border-radius: 7px !important;
    background: var(--white) !important;
    color: #000 !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-weight: 700;
}

div.stButton > button:hover {
    border-color: #d4d4d4 !important;
    background: #d4d4d4 !important;
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
.stTextInput input,
.stNumberInput input,
.stDateInput input {
    border-color: var(--border) !important;
    background-color: #0a0a0a !important;
    color: var(--text) !important;
}

[data-testid="stDataFrame"],
[data-testid="stExpander"] {
    border: 1px solid var(--border);
    border-radius: 8px;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
}

.stTabs [data-baseweb="tab"] {
    border: 1px solid var(--border);
    border-radius: 7px;
    background: #080808;
    color: var(--muted);
}

.stTabs [aria-selected="true"] {
    border-color: var(--white) !important;
    background: var(--white) !important;
    color: #000 !important;
}

hr {
    border-color: var(--border) !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# STATUS + SIDEBAR
# ============================================================

atlas_connected, atlas_message = atlas_status()
case_count = collection_count(cases_collection)
rollup_count = collection_count(rollups_collection)

with st.sidebar:
    st.markdown("## SURGICAL ANALYTICS")
    st.caption("Atlas Aggregation Framework Lab")
    st.markdown("---")

    if atlas_connected:
        st.markdown(
            '<span class="connected">● ATLAS CONNECTED</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="disconnected">● ATLAS DISCONNECTED</span>',
            unsafe_allow_html=True,
        )

    if not MONGODB_URI:
        st.caption("Paste the Atlas URI into MONGODB_URI.")
    elif not atlas_connected:
        st.error(atlas_message)

    st.markdown("---")
    st.markdown("**DEMO CONTROL**")

    if st.button(
        "SEED DATA + BUILD INDEXES",
        use_container_width=True,
        disabled=not atlas_connected,
    ):
        with st.spinner("Generating cases and building analytical rollups..."):
            if seed_demo():
                st.rerun()

    if st.button(
        "REBUILD ROLLUPS",
        use_container_width=True,
        disabled=not atlas_connected or case_count == 0,
    ):
        started = time.perf_counter()
        try:
            rebuilt = rebuild_rollups()
            elapsed = time.perf_counter() - started
            add_log(f"OK rollups rebuilt rows={rebuilt:,} latency={elapsed:.3f}s")
            st.rerun()
        except PyMongoError as exc:
            st.error(f"Rollup build failed: {exc}")

    if st.button(
        "RESET DEMO DATA",
        use_container_width=True,
        disabled=not atlas_connected,
    ):
        if reset_demo():
            st.rerun()

    st.markdown("---")
    st.caption(f"Database: {DATABASE_NAME}")
    st.caption(f"Cases: {case_count:,}")
    st.caption(f"Rollups: {rollup_count:,}")
    st.caption("No OpenAI. No Voyage. No Vector Search.")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="hero">
  <div class="hero-kicker">MongoDB Atlas / Aggregation Framework</div>
  <div class="hero-title">Surgical Supply Analytics</div>
  <div class="hero-subtitle">
    Runtime dimensions, measures, filters, and peer benchmarks compile into a
    controlled MongoDB aggregation pipeline. Atlas performs the math and returns
    application-ready analytical results.
  </div>
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
<div class="status-row">
  <span class="status-pill">ATLAS: {"CONNECTED" if atlas_connected else "DISCONNECTED"}</span>
  <span class="status-pill">CASES: {case_count:,}</span>
  <span class="status-pill">ROLLUPS: {rollup_count:,}</span>
  <span class="status-pill">PIPELINE MODE: WHITELISTED</span>
  <span class="status-pill">LAST LATENCY: {latency_text}</span>
</div>
""",
    unsafe_allow_html=True,
)

if case_count == 0:
    st.info(
        "Click SEED DATA + BUILD INDEXES. The one-click setup creates synthetic "
        "surgical cases, standard indexes, and monthly analytical rollups."
    )

    cards = st.columns(4)
    empty_cards = [
        ("01", "Runtime controls", "Choose dimensions, measures, filters, and benchmarks."),
        ("02", "Safe compiler", "Map selections to approved field paths and operators."),
        ("03", "Atlas computes", "Execute grouping, windows, variance, ranking, and facets."),
        ("04", "Explainable", "Inspect every generated aggregation stage and result."),
    ]

    for column, (number, value, detail) in zip(cards, empty_cards):
        with column:
            st.markdown(
                f"""
<div class="card">
  <div class="card-label">STEP {number}</div>
  <div class="card-value">{html.escape(value)}</div>
  <div class="card-detail">{html.escape(detail)}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-label">Activity log</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="log-window">'
        + html.escape("\n".join(st.session_state.logs))
        + "</div>",
        unsafe_allow_html=True,
    )
    st.stop()


# ============================================================
# MAIN TABS
# ============================================================

(
    analytics_tab,
    theater_tab,
    comparison_tab,
    model_tab,
    data_tab,
) = st.tabs(
    [
        "ANALYTICS WORKBENCH",
        "PIPELINE THEATER",
        "RAW VS ROLLUP",
        "DATA MODEL",
        "SEEDED DATA",
    ]
)


# ============================================================
# ANALYTICS WORKBENCH
# ============================================================

with analytics_tab:
    st.markdown('<div class="section-label">Build an analysis</div>', unsafe_allow_html=True)

    control_a, control_b, control_c, control_d = st.columns(4)

    with control_a:
        group_dimension = st.selectbox(
            "Group results by",
            list(DIMENSIONS),
            index=list(DIMENSIONS).index("Surgeon"),
        )

    with control_b:
        benchmark_dimension = st.selectbox(
            "Benchmark each group against",
            list(DIMENSIONS),
            index=list(DIMENSIONS).index("Facility"),
        )

    with control_c:
        measure = st.selectbox(
            "Measure",
            list(MEASURES),
            index=0,
        )

    with control_d:
        minimum_cases = st.number_input(
            "Minimum case volume",
            min_value=1,
            max_value=1000,
            value=25,
            step=5,
        )

    filter_a, filter_b, filter_c, filter_d = st.columns(4)

    procedure_options = {
        item["name"]: item["code"]
        for item in PROCEDURES
    }
    facility_options = {
        item["name"]: item["id"]
        for item in FACILITIES
    }
    all_categories = sorted(
        {
            template[0]
            for templates in SUPPLY_TEMPLATES.values()
            for template in templates
        }
    )
    all_markets = sorted({item["market"] for item in FACILITIES})

    with filter_a:
        selected_procedures = st.multiselect(
            "Procedures",
            list(procedure_options),
            default=["Total Knee Arthroplasty"],
        )

    with filter_b:
        selected_categories = st.multiselect(
            "Supply categories",
            all_categories,
            default=["Implant"],
        )

    with filter_c:
        selected_facilities = st.multiselect(
            "Facilities",
            list(facility_options),
            default=[],
        )

    with filter_d:
        selected_markets = st.multiselect(
            "Markets",
            all_markets,
            default=[],
        )

    range_a, range_b, range_c, range_d = st.columns(4)

    with range_a:
        start_date = st.date_input(
            "Start date",
            value=date(2025, 1, 1),
            min_value=date(2025, 1, 1),
            max_value=date(2026, 9, 30),
        )

    with range_b:
        end_date = st.date_input(
            "End date",
            value=date(2026, 9, 12),
            min_value=date(2025, 1, 1),
            max_value=date(2026, 9, 30),
        )

    with range_c:
        selected_risks = st.multiselect(
            "Patient risk bands",
            list(RISK_FACTORS),
            default=[],
        )

    with range_d:
        outlier_threshold = st.number_input(
            "Outlier threshold (%)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
        )

    analysis_config = {
        "groupDimension": group_dimension,
        "benchmarkDimension": benchmark_dimension,
        "measure": measure,
        "minimumCases": int(minimum_cases),
        "outlierThreshold": float(outlier_threshold),
        "startDate": start_date,
        "endDate": end_date,
        "procedureCodes": [
            procedure_options[name]
            for name in selected_procedures
        ],
        "facilityIds": [
            facility_options[name]
            for name in selected_facilities
        ],
        "markets": selected_markets,
        "riskBands": selected_risks,
        "supplyCategories": selected_categories,
    }

    errors = validate_analysis_config(analysis_config)
    if errors:
        for error in errors:
            st.error(error)

    st.caption(MEASURES[measure]["description"])

    if st.button(
        "RUN ANALYTICAL PIPELINE",
        use_container_width=True,
        disabled=bool(errors),
    ):
        try:
            with st.spinner("Compiling and executing the aggregation pipeline..."):
                results, summary, pipeline, latency = run_analysis(
                    analysis_config
                )
                st.session_state.last_results = results
                st.session_state.last_summary = summary
                st.session_state.last_pipeline = pipeline
                st.session_state.last_config = analysis_config
                st.session_state.last_latency = latency
                add_log(
                    f"ANALYSIS group={group_dimension} "
                    f"benchmark={benchmark_dimension} "
                    f"measure={measure} stages={len(pipeline)} "
                    f"rows={len(results)} latency={latency:.3f}s"
                )
        except (PyMongoError, ValueError) as exc:
            add_log(f"ERROR analysis failed: {exc}")
            st.error(f"Analysis failed: {exc}")

    results = st.session_state.last_results
    summary = st.session_state.last_summary

    if results:
        result_format = MEASURES[
            st.session_state.last_config.get("measure", measure)
        ]["format"]
        frame = result_dataframe(results, result_format)

        st.markdown('<div class="section-label">Analytical result</div>', unsafe_allow_html=True)

        metric_columns = st.columns(5)
        metric_rows = [
            (
                "QUALIFYING CASES",
                f"{summary.get('cases', 0):,}",
                "After runtime filters and minimum-volume rules",
            ),
            (
                "PEER GROUPS",
                f"{summary.get('groups', 0):,}",
                f"Grouped by {st.session_state.last_config.get('groupDimension')}",
            ),
            (
                "OUTLIERS",
                f"{summary.get('outliers', 0):,}",
                f"At or beyond {st.session_state.last_config.get('outlierThreshold')}%",
            ),
            (
                "TOTAL SPEND",
                f"${summary.get('spend', 0):,.0f}",
                "Selected supply categories",
            ),
            (
                "QUERY TIME",
                f"{st.session_state.last_latency:.3f}s",
                f"{len(st.session_state.last_pipeline)} aggregation stages",
            ),
        ]

        for column, (label, value, detail) in zip(metric_columns, metric_rows):
            with column:
                st.markdown(
                    f"""
<div class="card">
  <div class="card-label">{html.escape(label)}</div>
  <div class="card-value">{html.escape(value)}</div>
  <div class="card-detail">{html.escape(detail)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

        chart_frame = frame[["Group", "Metric", "Peer average"]].copy()
        chart_frame = chart_frame.set_index("Group")
        st.bar_chart(chart_frame, use_container_width=True)

        display_columns = [
            "Group",
            "Peer benchmark",
            "Metric display",
            "Peer display",
            "Variance %",
            "Z-score",
            "Peer rank",
            "Cases",
            "Outlier",
        ]
        st.dataframe(
            frame[display_columns],
            use_container_width=True,
            hide_index=True,
        )

        top_result = results[0]
        st.markdown(
            f"""
<div class="safety-box">
  <span class="eyebrow">Largest positive variance</span><br/>
  <strong>{html.escape(str(top_result['groupLabel']))}</strong> is
  <strong>{top_result['variancePct']:+.2f}%</strong> relative to the
  {html.escape(str(top_result['benchmarkLabel']))} peer average across
  <strong>{top_result['caseCount']:,}</strong> qualifying cases.
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.caption("Run an analysis to populate the benchmark result.")


# ============================================================
# PIPELINE THEATER
# ============================================================

with theater_tab:
    st.markdown('<div class="section-label">Runtime choices become a controlled pipeline</div>', unsafe_allow_html=True)

    st.markdown(
        """
<div class="safety-box">
  The application never accepts a user-supplied field path, MongoDB operator,
  or executable JSON stage. Every UI selection maps to the application-owned
  analytical dictionary. The compiler validates the request and emits only
  known aggregation stages.
</div>
""",
        unsafe_allow_html=True,
    )

    pipeline = st.session_state.last_pipeline

    if not pipeline:
        st.info("Run an analysis first. Its compiled pipeline will appear here.")
    else:
        config_view = dict(st.session_state.last_config)
        config_view["startDate"] = str(config_view["startDate"])
        config_view["endDate"] = str(config_view["endDate"])

        st.markdown('<div class="section-label">Validated analysis plan</div>', unsafe_allow_html=True)
        st.json(config_view)

        st.markdown('<div class="section-label">Stage-by-stage execution</div>', unsafe_allow_html=True)

        for index, stage in enumerate(pipeline, start=1):
            stage_name = next(iter(stage))
            description = STAGE_DESCRIPTIONS.get(
                stage_name,
                "Execute an application-controlled transformation.",
            )
            st.markdown(
                f"""
<div class="stage-card">
  <div class="stage-number">STAGE {index:02d}</div>
  <div class="stage-name">{html.escape(stage_name)}</div>
  <div class="stage-copy">{html.escape(description)}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            with st.expander(f"View stage {index:02d} JSON"):
                st.json(pipeline_for_display([stage])[0])

        st.markdown('<div class="section-label">Complete aggregation pipeline</div>', unsafe_allow_html=True)
        st.code(
            json.dumps(
                pipeline_for_display(pipeline),
                indent=2,
            ),
            language="json",
        )


# ============================================================
# RAW VS ROLLUP
# ============================================================

with comparison_tab:
    st.markdown('<div class="section-label">Ad hoc detail versus reusable analytical summary</div>', unsafe_allow_html=True)

    st.write(
        "Run the same facility-level cost calculation over raw embedded case "
        "documents and over a monthly rollup built with `$merge`. Both paths "
        "stay in MongoDB; the right choice depends on freshness, flexibility, "
        "latency, and workload frequency."
    )

    compare_a, compare_b, compare_c = st.columns([1, 1, 1])

    with compare_a:
        comparison_procedure_name = st.selectbox(
            "Comparison procedure",
            list(procedure_options),
            index=0,
            key="comparison_procedure",
        )

    with compare_b:
        comparison_category = st.selectbox(
            "Comparison supply category",
            all_categories,
            index=all_categories.index("Implant"),
            key="comparison_category",
        )

    with compare_c:
        st.write("")
        st.write("")
        run_comparison = st.button(
            "RUN RAW VS ROLLUP",
            use_container_width=True,
        )

    if run_comparison:
        try:
            with st.spinner("Executing both analytical paths..."):
                comparison = run_raw_vs_rollup(
                    procedure_options[comparison_procedure_name],
                    comparison_category,
                )
                st.session_state.comparison = comparison
                add_log(
                    f"COMPARE raw={comparison['rawLatency']:.3f}s "
                    f"rollup={comparison['rollupLatency']:.3f}s "
                    f"speedup={comparison['speedup']:.2f}x"
                )
        except PyMongoError as exc:
            add_log(f"ERROR comparison failed: {exc}")
            st.error(f"Comparison failed: {exc}")

    comparison = st.session_state.comparison

    if comparison:
        compare_metrics = st.columns(4)
        comparison_cards = [
            (
                "RAW CASE PIPELINE",
                f"{comparison['rawLatency']:.4f}s",
                f"{len(comparison['rawPipeline'])} stages over embedded cases",
            ),
            (
                "ROLLUP PIPELINE",
                f"{comparison['rollupLatency']:.4f}s",
                f"{len(comparison['rollupPipeline'])} stages over monthly summaries",
            ),
            (
                "OBSERVED SPEEDUP",
                f"{comparison['speedup']:.2f}x",
                "Illustrative result on the seeded dataset",
            ),
            (
                "VALIDATION",
                "MATCH",
                "Raw and rollup averages reconcile by facility",
            ),
        ]

        for column, (label, value, detail) in zip(
            compare_metrics,
            comparison_cards,
        ):
            with column:
                st.markdown(
                    f"""
<div class="card">
  <div class="card-label">{html.escape(label)}</div>
  <div class="card-value">{html.escape(value)}</div>
  <div class="card-detail">{html.escape(detail)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

        st.dataframe(
            pd.DataFrame(comparison["validation"]),
            use_container_width=True,
            hide_index=True,
        )

        pipeline_left, pipeline_right = st.columns(2)
        with pipeline_left:
            st.markdown("#### Raw case pipeline")
            st.code(
                json.dumps(
                    pipeline_for_display(comparison["rawPipeline"]),
                    indent=2,
                ),
                language="json",
            )
        with pipeline_right:
            st.markdown("#### Monthly rollup pipeline")
            st.code(
                json.dumps(
                    pipeline_for_display(comparison["rollupPipeline"]),
                    indent=2,
                ),
                language="json",
            )

    st.caption(
        "This comparison is not a production benchmark. It demonstrates the "
        "design choice between fully dynamic detail queries and reusable summaries."
    )


# ============================================================
# DATA MODEL
# ============================================================

with model_tab:
    st.markdown('<div class="section-label">Case-centered analytical document</div>', unsafe_allow_html=True)

    model_left, model_right = st.columns([1.05, 1], gap="large")

    with model_left:
        st.markdown(
            """
<div class="safety-box">
  <span class="eyebrow">Relational starting point</span><br/>
  A snowflake schema typically reconstructs the surgical case through joins
  across fact, procedure, surgeon, facility, supply, manufacturer, contract,
  and date dimensions before performing the analytical calculation.
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("#### MongoDB case document")
        st.write(
            "The demo stores the analytical business object as one surgical "
            "case document. Facility, surgeon, procedure, risk context, and the "
            "supplies used in the case travel together."
        )

        sample_document = cases_collection.find_one(
            {},
            sort=[("procedureDate", DESCENDING)],
        )
        st.json(sample_document)

    with model_right:
        st.markdown("#### Relationship shape")
        relationship_rows = pd.DataFrame(
            [
                {
                    "Level": "Surgical case",
                    "Cardinality": "One document",
                    "Examples": "Date, status, patient risk band",
                },
                {
                    "Level": "Facility",
                    "Cardinality": "Embedded context",
                    "Examples": "ID, name, market, region",
                },
                {
                    "Level": "Surgeon",
                    "Cardinality": "Embedded context",
                    "Examples": "ID, name, specialty",
                },
                {
                    "Level": "Procedure",
                    "Cardinality": "Embedded context",
                    "Examples": "Code, name, category",
                },
                {
                    "Level": "Supplies",
                    "Cardinality": "Embedded array",
                    "Examples": "SKU, category, manufacturer, quantity, cost",
                },
            ]
        )
        st.dataframe(
            relationship_rows,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### Safe runtime compilation")
        safety_rows = pd.DataFrame(
            [
                {
                    "Runtime choice": "Dimension",
                    "Allowed source": "DIMENSIONS dictionary",
                    "Cannot supply": "Arbitrary field path",
                },
                {
                    "Runtime choice": "Measure",
                    "Allowed source": "MEASURES dictionary",
                    "Cannot supply": "Arbitrary expression",
                },
                {
                    "Runtime choice": "Filter",
                    "Allowed source": "Typed widget values",
                    "Cannot supply": "MongoDB operator",
                },
                {
                    "Runtime choice": "Benchmark",
                    "Allowed source": "Approved partition key",
                    "Cannot supply": "Executable stage",
                },
            ]
        )
        st.dataframe(
            safety_rows,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### Aggregation capabilities shown")
        for capability in [
            "Embedded-array analysis with `$unwind`",
            "Multi-level metrics with `$group`",
            "Peer benchmarks and ranks with `$setWindowFields`",
            "Derived variance and z-score with `$set`",
            "Multiple analytical result sets with `$facet`",
            "Reusable materialized summaries with `$merge`",
        ]:
            st.markdown(f"- {capability}")


# ============================================================
# SEEDED DATA + ACTIVITY
# ============================================================

with data_tab:
    st.markdown('<div class="section-label">Seeded analytical data</div>', unsafe_allow_html=True)

    data_metrics = st.columns(5)
    data_cards = [
        ("CASES", f"{case_count:,}", "One document per completed procedure"),
        ("FACILITIES", f"{len(FACILITIES)}", "Across four Midwest markets"),
        ("SURGEONS", f"{len(SURGEONS)}", "Across four surgical specialties"),
        ("PROCEDURES", f"{len(PROCEDURES)}", "Orthopedic, cardiac, neuro, and general"),
        ("ROLLUPS", f"{rollup_count:,}", "Monthly facility/procedure/category summaries"),
    ]

    for column, (label, value, detail) in zip(data_metrics, data_cards):
        with column:
            st.markdown(
                f"""
<div class="card">
  <div class="card-label">{html.escape(label)}</div>
  <div class="card-value">{html.escape(value)}</div>
  <div class="card-detail">{html.escape(detail)}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    preview_limit = st.slider(
        "Preview rows",
        min_value=5,
        max_value=100,
        value=20,
        step=5,
    )

    case_preview = list(
        cases_collection.find(
            {},
            {
                "_id": 1,
                "procedureDate": 1,
                "facility.name": 1,
                "surgeon.name": 1,
                "procedure.name": 1,
                "patientRiskBand": 1,
                "supplyLineCount": 1,
                "totalSupplyCost": 1,
            },
        )
        .sort("procedureDate", DESCENDING)
        .limit(preview_limit)
    )

    preview_rows = []
    for item in case_preview:
        preview_rows.append(
            {
                "Case": item["_id"],
                "Date": item["procedureDate"],
                "Facility": item["facility"]["name"],
                "Surgeon": item["surgeon"]["name"],
                "Procedure": item["procedure"]["name"],
                "Risk": item["patientRiskBand"],
                "Supply lines": item["supplyLineCount"],
                "Total supply cost": item["totalSupplyCost"],
            }
        )

    st.dataframe(
        pd.DataFrame(preview_rows),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("View standard indexes"):
        st.json(
            {
                CASES_COLLECTION: cases_collection.index_information(),
                ROLLUPS_COLLECTION: rollups_collection.index_information(),
            }
        )

    st.markdown('<div class="section-label">Activity log</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="log-window">'
        + html.escape("\n".join(st.session_state.logs))
        + "</div>",
        unsafe_allow_html=True,
    )

