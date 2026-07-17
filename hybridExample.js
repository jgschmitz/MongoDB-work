db.members.aggregate([
  {
    "$search": {
      "compound": {
        // Track 1: Deterministic Overrides (Highest priority matches)
        "should": [
          { "text": { "query": "999887777", "path": "identifiers.ssn" } },
          { "text": { "query": "1EG4-TE5-MK72", "path": "identifiers.mbi" } }
        ],
        // Track 2: Split Semantic Voyage Vectors
        "must": [
          {
            "knnBeta": {
              "vector": [ /* Voyage Name Query Vector */ ],
              "path": "embeddings.name_vector",
              "k": 50
            }
          },
          {
            "knnBeta": {
              "vector": [ /* Voyage Location Query Vector */ ],
              "path": "embeddings.loc_vector",
              "k": 50
            }
          }
        ]
      }
    }
  },
  // Track 3: Native Hybrid Fusion
  {
    "$rankFusion": {
      "mode": "rrf" // Reciprocal Rank Fusion combines text and vector positions natively
    }
  },
  { "$limit": 20 }
])
