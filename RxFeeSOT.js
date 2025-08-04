{
  "id": "auto_increment",  // Unique ID for the fee catalog entry
  "serviceKey": "CS001",
  "serviceVersion": "1.2.3",
  "createdBy": "user@example.com",

  "serviceName": "Comprehensive Clinical Review",
  "serviceType": "component",  // Enum: component, product, taxonomy_product
  "serviceID": "SRV001",
  "serviceCategory": "Clinical Expertise & Healthcare Outcomes",
  "serviceDescription": "Clinical review for high-risk prescriptions exceeding $10k annually.",
  "serviceReviewFrequency": "Quarterly",
  "isServiceStandard": true,

  "costDetails": {
    "costAmountType": "per_member",  // Enum: per_review, per_member, per_rx, other
    "costAmount": "25.00",
    "costType": "Cost per member"
  },

  "fee": {
    "feeAmountType": "$",
    "feeAmount": "12.50",
    "feeBasis": "per member per month",
    "feeBasisOther": null,

    // AI metadata
    "aiSuggested": false,
    "confidenceScore": null,
    "lastReviewedByAI": null,
    "explanation": null  // Optional text from AI about why this fee was chosen
  },

  "lobID": "LOB_MAIN",  // Primary Line of Business (inherited fee)
  
  "applicableLobs": [
    {
      "applicableLobId": "LOB001",  // Commercial
      "overrideFee": false  // Inherits from base fee
    },
    {
      "applicableLobId": "LOB002",  // Medicare
      "overrideFee": true,
      "overrideFields": {
        "feeAmount": "10.00",
        "feeAmountType": "$",
        "feeBasis": "per impacted rx",
        "feeBasisOther": null,

        // AI override info
        "aiSuggested": true,
        "confidenceScore": 0.92,
        "lastReviewedByAI": "2025-08-01T00:00:00Z",
        "explanation": "Recommended based on similar Medicare clients in Tier 2 with >85% Rx utilization."
      }
    }
  ]
}
