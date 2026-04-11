{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Remit835",
  "description": "HIPAA 835 Healthcare Claim Payment/Advice document schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "metadata", "remittance5010", "remittanceId"],
  "properties": {
    "id": { "type": "string", "description": "Unique document identifier" },
    "metadata": { "$ref": "#/$defs/Metadata" },
    "remittance5010": { "$ref": "#/$defs/Remittance5010" },
    "remittanceId": { "type": "string", "description": "Remittance transaction identifier" }
  },
  "$defs": {
    "Address": {
      "type": "object",
      "additionalProperties": false,
      "description": "Standard postal address",
      "properties": {
        "address1": { "type": "string" },
        "address2": { "type": ["string", "null"], "default": null },
        "city": { "type": "string" },
        "state": { "type": "string" },
        "postalCode": { "type": "string" }
      },
      "required": ["address1", "city", "state", "postalCode"]
    },
    "Communication": {
      "type": "object",
      "additionalProperties": false,
      "description": "Communication channel (TE=telephone, FX=fax, EM=email)",
      "properties": {
        "type": { "type": "string", "description": "Communication type qualifier" },
        "value": { "type": "string" }
      },
      "required": ["type", "value"]
    },
    "ReferenceIdentifier": {
      "type": "object",
      "additionalProperties": false,
      "description": "Reference identifier with type qualifier",
      "properties": {
        "refId": { "type": "string" },
        "refType": { "type": "string" }
      },
      "required": ["refId", "refType"]
    },
    "DateWithQualifier": {
      "type": "object",
      "additionalProperties": false,
      "description": "Date value with qualifier code",
      "properties": {
        "date": { "type": "string", "format": "date", "description": "Date in YYYYMMDD or ISO 8601 format" },
        "qualifier": { "type": "string", "description": "Date qualifier code per X12 spec" }
      },
      "required": ["date", "qualifier"]
    },
    "AmountWithType": {
      "type": "object",
      "additionalProperties": false,
      "description": "Monetary amount with type qualifier",
      "properties": {
        "amount": { "type": "number", "description": "Monetary amount" },
        "amountType": { "type": "string", "description": "Amount type qualifier" }
      },
      "required": ["amount", "amountType"]
    },
    "AdjustmentDetail": {
      "type": "object",
      "additionalProperties": false,
      "description": "Single adjustment reason/amount/quantity triplet from CAS segment",
      "properties": {
        "reasonCode": { "type": "string", "description": "Claim Adjustment Reason Code (CARC)" },
        "amount": { "type": "number", "description": "Adjustment amount" },
        "quantity": { "type": ["number", "null"], "default": null, "description": "Adjustment quantity" }
      },
      "required": ["reasonCode", "amount"]
    },
    "SupplementalQuantity": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "qualifier": { "type": "string" },
        "quantity": { "type": "number" }
      },
      "required": ["qualifier", "quantity"]
    },
    "RemarkCode": {
      "type": "object",
      "additionalProperties": false,
      "description": "Remark code with qualifier",
      "properties": {
        "codeQualifier": { "type": "string" },
        "codeValue": { "type": "string" }
      },
      "required": ["codeQualifier", "codeValue"]
    },
    "NamedContactInformation": {
      "type": "object",
      "additionalProperties": false,
      "description": "Contact information with name and communication channels",
      "properties": {
        "communications": {
          "type": "array",
          "items": { "$ref": "#/$defs/Communication" },
          "minItems": 1,
          "maxItems": 3,
          "description": "Normalized from communication1/communication2/communication3"
        },
        "functionCode": { "type": "string" },
        "name": { "type": "string" }
      },
      "required": ["communications", "functionCode", "name"]
    },
    "PatientEntity": {
      "type": "object",
      "additionalProperties": false,
      "description": "Patient entity with name and identifiers",
      "properties": {
        "entityCategory": { "type": "string" },
        "entityId": { "type": "string" },
        "entityIdType": { "type": "string" },
        "entityType": { "type": "string" },
        "firstName": { "type": "string" },
        "lastOrOrgName": { "type": "string" },
        "middleName": { "type": ["string", "null"], "default": null },
        "nameSuffix": { "type": ["string", "null"], "default": null }
      },
      "required": ["entityCategory", "entityId", "entityIdType", "entityType", "firstName", "lastOrOrgName"]
    },
    "PersonEntity": {
      "type": "object",
      "additionalProperties": false,
      "description": "Person entity (insured, subscriber) with name details",
      "properties": {
        "entityCategory": { "type": "string" },
        "entityId": { "type": "string" },
        "entityIdType": { "type": "string" },
        "entityType": { "type": "string" },
        "firstName": { "type": "string" },
        "lastOrOrgName": { "type": "string" },
        "middleName": { "type": ["string", "null"], "default": null }
      },
      "required": ["entityCategory", "entityId", "entityIdType", "entityType", "firstName", "lastOrOrgName"]
    },
    "CorrectedInsuredEntity": {
      "type": "object",
      "additionalProperties": false,
      "description": "Corrected insured entity (may have partial information)",
      "properties": {
        "entityCategory": { "type": "string" },
        "entityType": { "type": "string" },
        "entityId": { "type": ["string", "null"], "default": null },
        "entityIdType": { "type": ["string", "null"], "default": null },
        "firstName": { "type": ["string", "null"], "default": null },
        "lastOrOrgName": { "type": ["string", "null"], "default": null },
        "middleName": { "type": ["string", "null"], "default": null }
      },
      "required": ["entityCategory", "entityType"]
    },
    "OrganizationEntity": {
      "type": "object",
      "additionalProperties": false,
      "description": "Organization entity (crossover carrier, corrected priority payer)",
      "properties": {
        "entityCategory": { "type": "string" },
        "entityId": { "type": "string" },
        "entityIdType": { "type": "string" },
        "entityType": { "type": "string" },
        "lastOrOrgName": { "type": "string" }
      },
      "required": ["entityCategory", "entityId", "entityIdType", "entityType", "lastOrOrgName"]
    },
    "BaseEntity": {
      "type": "object",
      "additionalProperties": false,
      "description": "Basic entity with identifiers only (other subscriber)",
      "properties": {
        "entityCategory": { "type": "string" },
        "entityId": { "type": "string" },
        "entityIdType": { "type": "string" },
        "entityType": { "type": "string" }
      },
      "required": ["entityCategory", "entityId", "entityIdType", "entityType"]
    },
    "ServiceProviderEntity": {
      "type": "object",
      "additionalProperties": false,
      "description": "Service/rendering provider entity",
      "properties": {
        "entityCategory": { "type": "string" },
        "entityId": { "type": "string" },
        "entityIdType": { "type": "string" },
        "entityType": { "type": "string" },
        "firstName": { "type": ["string", "null"], "default": null },
        "lastOrOrgName": { "type": ["string", "null"], "default": null }
      },
      "required": ["entityCategory", "entityId", "entityIdType", "entityType"]
    },
    "PayeeIdentification": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "entityCode": { "type": "string" },
        "entityId": { "type": "string" },
        "entityIdType": { "type": "string" },
        "name": { "type": "string" }
      },
      "required": ["entityCode", "entityId", "entityIdType", "name"]
    },
    "SimplePayerIdentification": {
      "type": "object",
      "additionalProperties": false,
      "description": "Payer identification (entityCode + name only)",
      "properties": {
        "entityCode": { "type": "string" },
        "name": { "type": "string" }
      },
      "required": ["entityCode", "name"]
    },

    "Metadata": {
      "type": "object",
      "additionalProperties": false,
      "description": "Document-level metadata for the 835 remittance",
      "properties": {
        "batchId": { "type": "string" },
        "batchTotalTransactionCount": { "type": ["integer", "null"], "default": null },
        "documentType": { "type": "string" },
        "processDateCT": { "type": "integer", "description": "Process date as epoch timestamp in CT timezone" },
        "properties": { "$ref": "#/$defs/MetadataProperties" },
        "senderId": { "type": "string" },
        "status": {
          "type": "string",
          "description": "Processing status"
        },
        "tenantId": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "transactionId": { "type": "string" }
      },
      "required": ["batchId", "documentType", "processDateCT", "properties", "senderId", "status", "tenantId", "timestamp", "transactionId"]
    },
    "MetadataProperties": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "isTenant": { "type": "boolean", "description": "Changed from string to boolean" },
        "read": { "type": "boolean", "description": "Changed from string to boolean" },
        "receiverId": { "type": "string" },
        "senderId": { "type": "string" },
        "sourceSystem": { "type": "string" }
      },
      "required": ["isTenant", "read", "receiverId", "senderId", "sourceSystem"]
    },

    "Remittance5010": {
      "type": "object",
      "additionalProperties": false,
      "description": "5010 format remittance transaction content",
      "properties": {
        "claimPaymentInfoCount": { "type": "integer" },
        "claimPaymentInfoDetails": {
          "type": "array",
          "items": { "$ref": "#/$defs/ClaimPaymentInfoDetailsItem" },
          "description": "WARNING: Unbounded array - consider bucket pattern or separate collection for large remittances"
        },
        "headerInformation": { "$ref": "#/$defs/HeaderInformation" },
        "providerAdjustments": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/ProviderAdjustment" } },
            { "type": "null" }
          ],
          "default": null
        },
        "transactionType": { "type": "string" }
      },
      "required": ["claimPaymentInfoCount", "claimPaymentInfoDetails", "headerInformation", "transactionType"]
    },

    "ClaimPaymentInfoDetailsItem": {
      "type": "object",
      "additionalProperties": false,
      "description": "Individual claim payment information within the remittance",
      "properties": {
        "claimMatchDetails": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/ClaimMatchDetail" } },
            { "type": "null" }
          ],
          "default": null
        },
        "claimPaymentInfoDetail": { "$ref": "#/$defs/ClaimPaymentInfoDetail" },
        "claimPaymentSeq": { "type": "integer" },
        "id": { "type": "string" },
        "metadata": { "$ref": "#/$defs/ClaimItemMetadata" },
        "remittanceId": { "type": "string" }
      },
      "required": ["claimPaymentInfoDetail", "claimPaymentSeq", "id", "metadata", "remittanceId"]
    },
    "ClaimMatchDetail": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "claimId": { "type": "string" },
        "createTSTP": { "type": "string", "format": "date-time" },
        "matchType": { "type": "string" }
      },
      "required": ["claimId", "createTSTP", "matchType"]
    },

    "ClaimPaymentInfoDetail": {
      "type": "object",
      "additionalProperties": false,
      "description": "Claim payment detail wrapper including payer/payee and claim info",
      "properties": {
        "assignedNumber": { "type": "string" },
        "checkNumber": { "type": "string" },
        "claimPaymentInfo": { "$ref": "#/$defs/ClaimPaymentInfo" },
        "payeeDetail": { "$ref": "#/$defs/PayeeDetail" },
        "payerIdentification": { "$ref": "#/$defs/SimplePayerIdentification" },
        "providerSummaryInformation": {
          "anyOf": [
            { "$ref": "#/$defs/ProviderSummaryInformation" },
            { "type": "null" }
          ],
          "default": null
        },
        "providerSupplementSummaryInformation": {
          "anyOf": [
            { "$ref": "#/$defs/ProviderSupplementSummaryInformation" },
            { "type": "null" }
          ],
          "default": null
        }
      },
      "required": ["assignedNumber", "checkNumber", "claimPaymentInfo", "payeeDetail", "payerIdentification"]
    },
    "PayeeDetail": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "payeeIdentification": { "$ref": "#/$defs/PayeeIdentification" },
        "payeeTaxId": { "type": "string" }
      },
      "required": ["payeeIdentification", "payeeTaxId"]
    },

    "ClaimPaymentInfo": {
      "type": "object",
      "additionalProperties": false,
      "description": "Detailed claim payment information including patient, adjustments, and service lines",
      "properties": {
        "adjustments": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/ClaimAdjustment" } },
            { "type": "null" }
          ],
          "default": null,
          "description": "Claim-level adjustments (CAS segments) - normalized from numbered fields"
        },
        "claimIdentifiers": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/ReferenceIdentifier" } },
            { "type": "null" }
          ],
          "default": null
        },
        "claimPayment": { "$ref": "#/$defs/ClaimPayment" },
        "claimPaymentId": { "type": "string" },
        "contactInformations": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/ClaimContactInformation" } },
            { "type": "null" }
          ],
          "default": null
        },
        "correctedInsured": {
          "anyOf": [
            { "$ref": "#/$defs/CorrectedInsuredEntity" },
            { "type": "null" }
          ],
          "default": null
        },
        "correctedPriorityPayers": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/OrganizationEntity" } },
            { "type": "null" }
          ],
          "default": null
        },
        "crossoverCarrier": {
          "anyOf": [
            { "$ref": "#/$defs/OrganizationEntity" },
            { "type": "null" }
          ],
          "default": null
        },
        "expirationDate": {
          "anyOf": [
            { "$ref": "#/$defs/DateWithQualifier" },
            { "type": "null" }
          ],
          "default": null
        },
        "inpatientAdjudication": {
          "anyOf": [
            { "$ref": "#/$defs/InpatientAdjudication" },
            { "type": "null" }
          ],
          "default": null
        },
        "insured": {
          "anyOf": [
            { "$ref": "#/$defs/PersonEntity" },
            { "type": "null" }
          ],
          "default": null
        },
        "otherSubscriber": {
          "anyOf": [
            { "$ref": "#/$defs/BaseEntity" },
            { "type": "null" }
          ],
          "default": null
        },
        "outpatientAdjudication": {
          "anyOf": [
            { "$ref": "#/$defs/OutpatientAdjudication" },
            { "type": "null" }
          ],
          "default": null
        },
        "patient": { "$ref": "#/$defs/PatientEntity" },
        "receivedDate": { "$ref": "#/$defs/DateWithQualifier" },
        "serviceAdjustments": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/ServiceAdjustment" } },
            { "type": "null" }
          ],
          "default": null,
          "description": "Service line level adjustments"
        },
        "serviceProvider": {
          "anyOf": [
            { "$ref": "#/$defs/ServiceProviderEntity" },
            { "type": "null" }
          ],
          "default": null
        },
        "statementFromAndToDate": {
          "type": "array",
          "items": { "$ref": "#/$defs/DateWithQualifier" }
        },
        "supplementalAmounts": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/AmountWithType" } },
            { "type": "null" }
          ],
          "default": null
        },
        "supplementalQuantities": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/SupplementalQuantity" } },
            { "type": "null" }
          ],
          "default": null
        }
      },
      "required": ["claimPayment", "claimPaymentId", "patient", "receivedDate", "statementFromAndToDate"]
    },

    "ClaimPayment": {
      "type": "object",
      "additionalProperties": false,
      "description": "CLP segment - Claim payment information",
      "properties": {
        "claimFilingIndicatorCode": { "type": "string", "description": "CLP06 - Claim filing indicator" },
        "claimFrequencyCode": { "type": ["string", "null"], "default": null },
        "claimPaymentAmount": { "type": "number", "description": "CLP04 - Claim payment amount (was string)" },
        "claimPlaceOfService": { "type": ["string", "null"], "default": null },
        "claimStatusCode": {
          "type": "string",
          "description": "CLP02 - Claim status code (1=Processed Primary, 2=Processed Secondary, 3=Processed Tertiary, 4=Denied, 19=Processed Primary-Forwarded, 20=Processed Secondary-Forwarded, 21=Processed Tertiary-Forwarded, 22=Reversal, 23=Not Our Claim, 25=Predetermination Pricing)"
        },
        "claimTotalChargeAmount": { "type": "number", "description": "CLP03 - Total claim charge amount (was string)" },
        "drgCode": { "type": ["string", "null"], "default": null, "description": "Renamed from dRGCode" },
        "drgWeight": { "type": ["number", "null"], "default": null, "description": "Renamed from dRGWeight, changed from string to number" },
        "dischargeFraction": { "type": ["number", "null"], "default": null, "description": "Changed from string to number" },
        "patientControlNumber": { "type": "string", "description": "CLP01 - Patient control number" },
        "patientResponsibilityAmount": { "type": ["number", "null"], "default": null, "description": "Changed from string to number" },
        "payerClaimControlNumber": { "type": "string", "description": "CLP07 - Payer claim control number" }
      },
      "required": ["claimFilingIndicatorCode", "claimPaymentAmount", "claimStatusCode", "claimTotalChargeAmount", "patientControlNumber", "payerClaimControlNumber"]
    },

    "ClaimAdjustment": {
      "type": "object",
      "additionalProperties": false,
      "description": "Claim-level CAS segment - normalized from numbered amount1/reasonCode1/quantity1 fields into array",
      "properties": {
        "groupCode": {
          "type": "string",
          "description": "Claim adjustment group code",
          "enum": ["CO", "PR", "OA", "PI", "CR"]
        },
        "details": {
          "type": "array",
          "items": { "$ref": "#/$defs/AdjustmentDetail" },
          "minItems": 1,
          "maxItems": 6,
          "description": "Adjustment reason/amount/quantity triplets (was amount1/reasonCode1/quantity1, amount2/reasonCode2/quantity2, etc.)"
        }
      },
      "required": ["groupCode", "details"]
    },

    "ClaimContactInformation": {
      "type": "object",
      "additionalProperties": false,
      "description": "Claim contact info - normalized from communication1 field to communications array",
      "properties": {
        "communications": {
          "type": "array",
          "items": { "$ref": "#/$defs/Communication" },
          "minItems": 1,
          "maxItems": 3
        },
        "functionCode": { "type": "string" }
      },
      "required": ["communications", "functionCode"]
    },

    "InpatientAdjudication": {
      "type": "object",
      "additionalProperties": false,
      "description": "MIA segment - Inpatient adjudication information",
      "properties": {
        "coveredDaysOrVisits": { "type": "number", "description": "Changed from string to number" },
        "remarkCodes": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1,
          "maxItems": 5,
          "description": "Normalized from remarkCode/remarkCode2/remarkCode3/remarkCode4 into array"
        },
        "claimDRGAmount": { "type": ["number", "null"], "default": null },
        "claimIndirectTeachingAmount": { "type": ["number", "null"], "default": null },
        "claimPPSCapitalAmount": { "type": ["number", "null"], "default": null },
        "costReportDayCount": { "type": ["number", "null"], "default": null },
        "disproportionateShareAmount": { "type": ["number", "null"], "default": null },
        "lifetimeReserveDays": { "type": ["number", "null"], "default": null },
        "ppsCapitalDSHDRGAmount": { "type": ["number", "null"], "default": null },
        "ppsCapitalFSPDRGAmount": { "type": ["number", "null"], "default": null },
        "ppsCapitalIMEAmount": { "type": ["number", "null"], "default": null },
        "ppsOperatingFederalSpecificDRGAmount": { "type": ["number", "null"], "default": null },
        "ppsOperatingHospitalDRGAmount": { "type": ["number", "null"], "default": null }
      },
      "required": ["coveredDaysOrVisits", "remarkCodes"]
    },

    "OutpatientAdjudication": {
      "type": "object",
      "additionalProperties": false,
      "description": "MOA segment - Outpatient adjudication information",
      "properties": {
        "remarkCodes": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1,
          "maxItems": 5,
          "description": "Normalized from remarkCode1/remarkCode2/remarkCode3 into array"
        },
        "hcpcsPayableAmount": { "type": ["number", "null"], "default": null },
        "outpatientReimbursementRate": { "type": ["number", "null"], "default": null }
      },
      "required": ["remarkCodes"]
    },

    "ServiceAdjustment": {
      "type": "object",
      "additionalProperties": false,
      "description": "Service line level adjustment information",
      "properties": {
        "lineItemControlIdentifier": {
          "anyOf": [
            { "$ref": "#/$defs/ReferenceIdentifier" },
            { "type": "null" }
          ],
          "default": null
        },
        "remarkCodes": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/RemarkCode" } },
            { "type": "null" }
          ],
          "default": null
        },
        "serviceAdjustments": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/ServiceLineAdjustment" } },
            { "type": "null" }
          ],
          "default": null
        },
        "serviceDates": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/DateWithQualifier" } },
            { "type": "null" }
          ],
          "default": null
        },
        "serviceIdentifiers": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/ReferenceIdentifier" } },
            { "type": "null" }
          ],
          "default": null
        },
        "servicePaymentInformation": { "$ref": "#/$defs/ServicePaymentInformation" },
        "supplementalAmounts": {
          "anyOf": [
            { "type": "array", "items": { "$ref": "#/$defs/AmountWithType" } },
            { "type": "null" }
          ],
          "default": null
        }
      },
      "required": ["servicePaymentInformation"]
    },

    "ServiceLineAdjustment": {
      "type": "object",
      "additionalProperties": false,
      "description": "Service line CAS segment - normalized from numbered fields into details array",
      "properties": {
        "groupCode": {
          "type": "string",
          "enum": ["CO", "PR", "OA", "PI", "CR"]
        },
        "details": {
          "type": "array",
          "items": { "$ref": "#/$defs/AdjustmentDetail" },
          "minItems": 1,
          "maxItems": 6
        }
      },
      "required": ["groupCode", "details"]
    },

    "ServicePaymentInformation": {
      "type": "object",
      "additionalProperties": false,
      "description": "SVC segment - Service payment information",
      "properties": {
        "adjudicatedProcedureCode": { "type": "string" },
        "adjudicatedProcedureModifiers": {
          "type": "array",
          "items": { "type": "string" },
          "maxItems": 4,
          "description": "Normalized from adjudicatedProcedureModifier1 through adjudicatedProcedureModifier4"
        },
        "adjudicatedProcedureType": { "type": "string" },
        "consideredRevenueCode": { "type": ["string", "null"], "default": null },
        "originalProcedureCode": { "type": ["string", "null"], "default": null },
        "originalProcedureDescription": { "type": ["string", "null"], "default": null },
        "originalProcedureModifier": { "type": ["string", "null"], "default": null },
        "originalProcedureType": { "type": ["string", "null"], "default": null },
        "originalServiceAmount": { "type": "number", "description": "Changed from string to number" },
        "originalServiceUnits": { "type": ["number", "null"], "default": null },
        "paidServiceAmount": { "type": "number", "description": "Changed from string to number" },
        "paidServiceUnits": { "type": ["number", "null"], "default": null }
      },
      "required": ["adjudicatedProcedureCode", "adjudicatedProcedureType", "originalServiceAmount", "paidServiceAmount"]
    },

    "ProviderSummaryInformation": {
      "type": "object",
      "additionalProperties": false,
      "description": "TS3 segment - Provider summary information",
      "properties": {
        "fiscalYearEndDate": { "type": "string", "format": "date" },
        "providerID": { "type": "string" },
        "providerPlaceOfService": { "type": "string" },
        "totalClaimChargeAmount": { "type": "number", "description": "Changed from string to number" },
        "totalClaimCount": { "type": "integer", "description": "Changed from string to integer" },
        "totalHCPCSPayableAmount": { "type": ["number", "null"], "default": null },
        "totalHCPCSReportedChargeAmount": { "type": ["number", "null"], "default": null },
        "totalMSPPatientLiabilityMetAmount": { "type": ["number", "null"], "default": null },
        "totalMSPPayerAmount": { "type": ["number", "null"], "default": null },
        "totalNonLabChargeAmount": { "type": ["number", "null"], "default": null },
        "totalPatientReimbursementAmount": { "type": ["number", "null"], "default": null }
      },
      "required": ["fiscalYearEndDate", "providerID", "providerPlaceOfService", "totalClaimChargeAmount", "totalClaimCount"]
    },

    "ProviderSupplementSummaryInformation": {
      "type": "object",
      "additionalProperties": false,
      "description": "TS2 segment - Provider supplement summary information. All fields changed from string to number.",
      "properties": {
        "averageDRGLengthOfStay": { "type": ["number", "null"], "default": null },
        "averageDRGWeight": { "type": ["number", "null"], "default": null },
        "totalCapitalAmount": { "type": ["number", "null"], "default": null },
        "totalCostOutlierAmount": { "type": ["number", "null"], "default": null },
        "totalCostReportDayCount": { "type": ["number", "null"], "default": null },
        "totalCoveredDayCount": { "type": ["number", "null"], "default": null },
        "totalDRGAmount": { "type": ["number", "null"], "default": null },
        "totalDischargeCount": { "type": ["number", "null"], "default": null },
        "totalDisproportionateShareAmount": { "type": ["number", "null"], "default": null },
        "totalFederalSpecificAmount": { "type": ["number", "null"], "default": null },
        "totalHospitalSpecificAmount": { "type": ["number", "null"], "default": null },
        "totalIndirectMedicalEducationAmount": { "type": ["number", "null"], "default": null },
        "totalNoncoveredDayCount": { "type": ["number", "null"], "default": null },
        "totalOutlierDayAmount": { "type": ["number", "null"], "default": null },
        "totalPPSCapitalFSPDRGAmount": { "type": ["number", "null"], "default": null },
        "totalPPSDSHDRGAmount": { "type": ["number", "null"], "default": null }
      }
    },

    "ClaimItemMetadata": {
      "type": "object",
      "additionalProperties": false,
      "description": "Metadata for individual claim payment items (consolidated with root Metadata - consider single shared definition)",
      "properties": {
        "batchId": { "type": "string" },
        "batchTotalTransactionCount": { "type": ["integer", "null"], "default": null },
        "documentType": { "type": "string" },
        "processDateCT": { "type": "integer" },
        "properties": { "$ref": "#/$defs/ClaimItemMetadataProperties" },
        "status": { "type": "string" },
        "tenantId": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "transactionId": { "type": "string" }
      },
      "required": ["batchId", "documentType", "processDateCT", "properties", "status", "tenantId", "timestamp", "transactionId"]
    },
    "ClaimItemMetadataProperties": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "isTenant": { "type": "boolean", "description": "Changed from string to boolean" },
        "sourceSystem": { "type": "string" }
      },
      "required": ["isTenant", "sourceSystem"]
    },

    "HeaderInformation": {
      "type": "object",
      "additionalProperties": false,
      "description": "Transaction set header information",
      "properties": {
        "financialInformation": { "$ref": "#/$defs/FinancialInformation" },
        "functionalGroup": { "$ref": "#/$defs/FunctionalGroup" },
        "interchange": { "$ref": "#/$defs/Interchange" },
        "payee": { "$ref": "#/$defs/HeaderPayee" },
        "payer": { "$ref": "#/$defs/HeaderPayer" },
        "productionDate": { "$ref": "#/$defs/DateWithQualifier" },
        "reassociationTraceNumber": { "$ref": "#/$defs/ReassociationTraceNumber" },
        "receiverIdentification": {
          "anyOf": [
            { "$ref": "#/$defs/ReferenceIdentifier" },
            { "type": "null" }
          ],
          "default": null
        },
        "transactionSetControlNumber": { "type": "string" },
        "transactionSetIdCode": { "type": "string" },
        "versionIdentification": {
          "anyOf": [
            { "$ref": "#/$defs/ReferenceIdentifier" },
            { "type": "null" }
          ],
          "default": null
        }
      },
      "required": ["financialInformation", "functionalGroup", "interchange", "payee", "payer", "productionDate", "reassociationTraceNumber", "transactionSetControlNumber", "transactionSetIdCode"]
    },

    "FinancialInformation": {
      "type": "object",
      "additionalProperties": false,
      "description": "BPR segment - Financial information",
      "properties": {
        "handlingCode": { "type": "string", "description": "BPR01 - Transaction handling code" },
        "orgCoDfiIdNumQualifier": { "type": ["string", "null"], "default": null },
        "payeeAccountNumber": { "type": ["string", "null"], "default": null },
        "payeeAccountType": { "type": ["string", "null"], "default": null },
        "payeeBankID": { "type": ["string", "null"], "default": null },
        "payerAccountNumber": { "type": ["string", "null"], "default": null },
        "payerAccountType": { "type": ["string", "null"], "default": null },
        "payerAdditionalID": { "type": ["string", "null"], "default": null },
        "payerBankID": { "type": ["string", "null"], "default": null },
        "payerTaxID": { "type": ["string", "null"], "default": null },
        "paymentEffectiveDate": { "type": "string", "format": "date", "description": "Changed from plain string to date format" },
        "paymentFormatCode": { "type": ["string", "null"], "default": null },
        "paymentMethodCode": {
          "type": "string",
          "description": "BPR04 - Payment method code",
          "enum": ["ACH", "BOP", "CHK", "FWT", "NON"]
        },
        "providerCredit": { "type": "number", "description": "Changed from string to number" },
        "rcvrDfiIdNumQualifier": { "type": ["string", "null"], "default": null },
        "totalAmount": { "type": "number", "description": "BPR02 - Total remittance amount (changed from string to number)" }
      },
      "required": ["handlingCode", "paymentEffectiveDate", "paymentMethodCode", "providerCredit", "totalAmount"]
    },

    "FunctionalGroup": {
      "type": "object",
      "additionalProperties": false,
      "description": "GS segment - Functional group header",
      "properties": {
        "applicationReceiverCode": { "type": "string" },
        "applicationSenderCode": { "type": "string" },
        "date": { "type": "string", "format": "date" },
        "groupControlNumber": { "type": "string" },
        "idCode": { "type": "string" },
        "responsibleAgencyCode": { "type": "string" },
        "time": { "type": "string" },
        "versionIDCode": { "type": "string" }
      },
      "required": ["applicationReceiverCode", "applicationSenderCode", "date", "groupControlNumber", "idCode", "responsibleAgencyCode", "time", "versionIDCode"]
    },

    "Interchange": {
      "type": "object",
      "additionalProperties": false,
      "description": "ISA segment - Interchange control header",
      "properties": {
        "acknowledgmentRequested": { "type": "string" },
        "authorizationInfo": { "type": "string" },
        "authorizationInfoType": { "type": "string" },
        "controlNumber": { "type": "string" },
        "controlVersionNumber": { "type": "string" },
        "date": { "type": "string", "format": "date" },
        "elementSeparator": { "type": "string" },
        "receiverId": { "type": "string" },
        "receiverIdType": { "type": "string" },
        "repetitionSeparator": { "type": "string", "description": "Fixed typo: was repititionSeparator" },
        "securityInfo": { "type": "string" },
        "securityInfoType": { "type": "string" },
        "segmentTerminator": { "type": "string" },
        "senderId": { "type": "string" },
        "senderIdType": { "type": "string" },
        "subElementSeparator": { "type": "string" },
        "time": { "type": "string" },
        "usageIndicator": { "type": "string" }
      },
      "required": ["acknowledgmentRequested", "authorizationInfo", "authorizationInfoType", "controlNumber", "controlVersionNumber", "date", "elementSeparator", "receiverId", "receiverIdType", "repetitionSeparator", "securityInfo", "securityInfoType", "segmentTerminator", "senderId", "senderIdType", "subElementSeparator", "time", "usageIndicator"]
    },

    "HeaderPayee": {
      "type": "object",
      "additionalProperties": false,
      "description": "N1-PE loop - Payee identification",
      "properties": {
        "address": {
          "anyOf": [
            { "$ref": "#/$defs/Address" },
            { "type": "null" }
          ],
          "default": null
        },
        "payeeIdentification": { "$ref": "#/$defs/PayeeIdentification" },
        "payeeIdentifiers": {
          "type": "array",
          "items": { "$ref": "#/$defs/ReferenceIdentifier" }
        }
      },
      "required": ["payeeIdentification", "payeeIdentifiers"]
    },

    "HeaderPayer": {
      "type": "object",
      "additionalProperties": false,
      "description": "N1-PR loop - Payer identification",
      "properties": {
        "address": { "$ref": "#/$defs/Address" },
        "businessContactInformation": {
          "anyOf": [
            { "$ref": "#/$defs/NamedContactInformation" },
            { "type": "null" }
          ],
          "default": null
        },
        "payerIdentification": { "$ref": "#/$defs/SimplePayerIdentification" },
        "payerIdentifiers": {
          "type": "array",
          "items": { "$ref": "#/$defs/ReferenceIdentifier" }
        },
        "technicalContactInformation": {
          "type": "array",
          "items": { "$ref": "#/$defs/NamedContactInformation" },
          "description": "Normalized: was array of objects each with communication1/2/3 - now uses shared NamedContactInformation with communications array"
        }
      },
      "required": ["address", "payerIdentification", "payerIdentifiers", "technicalContactInformation"]
    },

    "ReassociationTraceNumber": {
      "type": "object",
      "additionalProperties": false,
      "description": "TRN segment - Reassociation trace number",
      "properties": {
        "payerAdditionalID": { "type": ["string", "null"], "default": null },
        "payerTaxID": { "type": "string" },
        "paymentTraceNumber": { "type": "string" },
        "traceTypeCode": { "type": "string" }
      },
      "required": ["payerTaxID", "paymentTraceNumber", "traceTypeCode"]
    },

    "ProviderAdjustment": {
      "type": "object",
      "additionalProperties": false,
      "description": "PLB segment - Provider-level adjustment",
      "properties": {
        "adjustments": {
          "type": "array",
          "items": { "$ref": "#/$defs/ProviderAdjustmentDetail" }
        },
        "fiscalPeriodDate": { "type": "string", "format": "date" },
        "providerIdentifier": { "type": "string" }
      },
      "required": ["adjustments", "fiscalPeriodDate", "providerIdentifier"]
    },
    "ProviderAdjustmentDetail": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "adjustedAmount": { "type": "number", "description": "Changed from string to number" },
        "adjustmentIdentifier": { "type": ["string", "null"], "default": null },
        "reasonCode": { "type": "string" }
      },
      "required": ["adjustedAmount", "reasonCode"]
    }
  }
}
