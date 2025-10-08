{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/schemas/benefit-plan.schema.json",
  "title": "Benefit Plan (Canonical)",
  "type": "object",
  "required": ["benefitPlan"],
  "properties": {
    "benefitPlan": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schemaVersion",
        "planId",
        "lineOfBusiness",
        "businessSegment",
        "effectivePeriod",
        "policyInfo",
        "benefits"
      ],
      "properties": {
        "schemaVersion": { "type": "string" },
        "planId": { "type": "string" },
        "lineOfBusiness": {
          "type": "string",
          "enum": ["E&I", "C&S", "IFP", "Medicare", "Medicaid", "Other"]
        },
        "businessSegment": { "type": "string" },
        "effectivePeriod": { "$ref": "#/$defs/Period" },
        "provenance": { "$ref": "#/$defs/Provenance" },
        "policyInfo": {
          "type": "object",
          "additionalProperties": false,
          "required": ["policyId"],
          "properties": {
            "policyId": { "type": "string" },
            "groupNumber": { "type": "string" },
            "productId": { "type": "string" }
          }
        },

        "benefits": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/Benefit" }
        },

        "deductible": { "$ref": "#/$defs/Deductible" },

        "outOfPocket": { "$ref": "#/$defs/OutOfPocket" },

        "planCsrInfo": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["infoType", "infoTypeDesc"],
            "properties": {
              "infoType": { "type": "string" },
              "infoTypeDesc": { "type": "string" }
            }
          }
        },

        "extensions": {
          "type": "object",
          "description": "Safe place for non-canonical fields",
          "additionalProperties": true,
          "properties": {
            "lobSpecific": { "type": "object", "additionalProperties": true },
            "internal": { "type": "object", "additionalProperties": true }
          }
        }
      }
    }
  },

  "$defs": {
    "Period": {
      "type": "object",
      "additionalProperties": false,
      "required": ["startDate"],
      "properties": {
        "startDate": { "type": "string", "format": "date" },
        "endDate": { "type": "string", "format": "date" }
      }
    },

    "Money": {
      "type": "object",
      "additionalProperties": false,
      "required": ["amount", "currency"],
      "properties": {
        "amount": { "type": "number", "minimum": 0 },
        "currency": { "type": "string", "default": "USD" }
      }
    },

    "Rate": {
      "type": "object",
      "additionalProperties": false,
      "required": ["percentage"],
      "properties": {
        "percentage": { "type": "number", "minimum": 0, "maximum": 100 }
      }
    },

    "CodeableConcept": {
      "type": "object",
      "additionalProperties": false,
      "required": ["code"],
      "properties": {
        "system": { "type": "string" },
        "code": { "type": "string" },
        "display": { "type": "string" }
      }
    },

    "AudienceText": {
      "type": "object",
      "additionalProperties": false,
      "required": ["audience", "locale", "markdown"],
      "properties": {
        "audience": { "type": "string", "enum": ["member", "provider", "broker", "internal"] },
        "locale": { "type": "string", "default": "en-US" },
        "markdown": { "type": "string" }
      }
    },

    "NetworkTier": {
      "type": "object",
      "additionalProperties": false,
      "required": ["networkType"],
      "properties": {
        "networkType": { "type": "string", "enum": ["INN", "OON"] },
        "tierName": { "type": "string" },
        "tierRank": { "type": "integer", "minimum": 1 }
      }
    },

    "UtilizationMgmt": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "priorAuthRequired": { "type": "boolean", "default": false },
        "referralRequired": { "type": "boolean", "default": false },
        "details": { "type": "string" }
      }
    },

    "CoveredService": {
      "type": "object",
      "additionalProperties": false,
      "required": ["service"],
      "properties": {
        "service": { "$ref": "#/$defs/CodeableConcept" },
        "included": { "type": "boolean", "default": true }
      }
    },

    "Limit": {
      "type": "object",
      "additionalProperties": false,
      "required": ["metric", "value"],
      "properties": {
        "metric": { "type": "string", "enum": ["visits", "days", "units", "age", "lifetime"] },
        "value": { "type": "number", "minimum": 0 },
        "period": { "type": "string", "enum": ["perCalendarYear", "perPlanYear", "perEpisode", "lifetime"] },
        "applies": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "deductible": { "type": "boolean" },
            "oopm": { "type": "boolean" },
            "rx": { "type": "boolean" }
          }
        }
      }
    },

    "AccumulatorRef": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "accumulatorType": { "type": "string", "enum": ["deductible", "oopm", "rxDeductible", "rxOopm"] },
        "accumulatorId": { "type": "string" }
      }
    },

    "CostShareBucket": {
      "type": "object",
      "additionalProperties": false,
      "required": ["type"],
      "properties": {
        "type": { "type": "string", "enum": ["copay", "coinsurance"] },
        "deductibleApplies": { "type": "boolean", "default": false },
        "primacyCode": { "type": "integer", "minimum": 1 },
        "utilizationMgmt": { "$ref": "#/$defs/UtilizationMgmt" },
        "placeOfService": { "$ref": "#/$defs/CodeableConcept" },
        "providerSpecialty": { "$ref": "#/$defs/CodeableConcept" },
        "limit": { "$ref": "#/$defs/Limit" },
        "coveredServices": {
          "type": "array",
          "items": { "$ref": "#/$defs/CoveredService" }
        },
        "accumulators": {
          "type": "array",
          "items": { "$ref": "#/$defs/AccumulatorRef" }
        }
      },
      "oneOf": [
        {
          "required": ["type", "amount"],
          "properties": {
            "type": { "const": "copay" },
            "amount": { "$ref": "#/$defs/Money" }
          }
        },
        {
          "required": ["type", "rate"],
          "properties": {
            "type": { "const": "coinsurance" },
            "rate": { "$ref": "#/$defs/Rate" }
          }
        }
      ]
    },

    "CostShare": {
      "type": "object",
      "additionalProperties": false,
      "required": ["networkTier", "buckets"],
      "properties": {
        "networkTier": { "$ref": "#/$defs/NetworkTier" },
        "audienceTexts": {
          "type": "array",
          "items": { "$ref": "#/$defs/AudienceText" }
        },
        "buckets": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/CostShareBucket" }
        },
        "benefitLimits": {
          "type": "array",
          "items": { "$ref": "#/$defs/Limit" }
        }
      }
    },

    "Benefit": {
      "type": "object",
      "additionalProperties": false,
      "required": ["benefitId", "benefitCategory", "effectivePeriod", "costShares"],
      "properties": {
        "benefitId": { "type": "string" },
        "benefitCategory": { "type": "string" },
        "benefitGroup": { "type": "string" },
        "effectivePeriod": { "$ref": "#/$defs/Period" },

        "coverageSummary": { "type": "string" },
        "coverageDetail": { "type": "string" },
        "benefitDefinition": { "type": "string" },

        "exceptionTexts": {
          "type": "array",
          "items": { "$ref": "#/$defs/AudienceText" }
        },

        "costShares": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/$defs/CostShare" }
        }
      }
    },

    "DeductibleTier": {
      "type": "object",
      "additionalProperties": false,
      "required": ["tier", "individual", "family"],
      "properties": {
        "tier": { "type": "string" },
        "individual": { "$ref": "#/$defs/Money" },
        "family": { "$ref": "#/$defs/Money" }
      }
    },

    "Deductible": {
      "type": "object",
      "additionalProperties": false,
      "required": ["embeddedType", "tiers"],
      "properties": {
        "embeddedType": { "type": "string", "enum": ["embedded", "aggregate"] },
        "rxDeductibleType": { "type": "string" },
        "carryOver": { "type": "string" },
        "definitions": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["term", "definition"],
            "properties": {
              "term": { "type": "string" },
              "definition": { "type": "string" }
            }
          }
        },
        "audienceTexts": {
          "type": "array",
          "items": { "$ref": "#/$defs/AudienceText" }
        },
        "limitsAndExceptionsTexts": {
          "type": "array",
          "items": { "$ref": "#/$defs/AudienceText" }
        },
        "tiers": {
          "type": "array",
          "items": { "$ref": "#/$defs/DeductibleTier" }
        }
      }
    },

    "OutOfPocketTier": {
      "type": "object",
      "additionalProperties": false,
      "required": ["tier", "individual", "family"],
      "properties": {
        "tier": { "type": "string" },
        "individual": { "$ref": "#/$defs/Money" },
        "family": { "$ref": "#/$defs/Money" }
      }
    },

    "OutOfPocket": {
      "type": "object",
      "additionalProperties": false,
      "required": ["tiers"],
      "properties": {
        "rxOopType": { "type": "string" },
        "carryOver": { "type": "string" },
        "tiers": {
          "type": "array",
          "items": { "$ref": "#/$defs/OutOfPocketTier" }
        }
      }
    },

    "Provenance": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "sourceSystem": { "type": "string", "enum": ["MRDP", "COM360", "PlanLibrary", "Other"] },
        "sourceRecordId": { "type": "string" },
        "ingestedAt": { "type": "string", "format": "date-time" },
        "transformedAt": { "type": "string", "format": "date-time" },
        "transformJobId": { "type": "string" },
        "stage": { "type": "string", "enum": ["bronze", "silver", "gold"] }
      }
    }
  }
}
