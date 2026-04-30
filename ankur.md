Key recommendations
1. Keep source_code in filter

This is the right move. source_code is a hard eligibility condition, not a relevance signal. Putting it in filter reduces scoring work and avoids giving arbitrary score credit for source membership. MongoDB explicitly recommends placing non-scoring operators such as equals, range, and in in filter when they are used only to constrain the candidate set.

One cleanup: in the HCO examples you have both:

<code>
filter: [{ in: { path: "metaData.source_code", value: [..., "LNRS", ...] }}],
mustNot: [{ equals: { path: "metaData.source_code", value: "LNRS" }}]
</code>

That works logically, but it is contradictory-looking and may add avoidable work. Prefer removing LNRS from the in list if it should always be excluded.

2. Preserve scoring for identifiers / names

For identifiers, your use of multiple equals clauses inside should is appropriate because each matching identifier should add score. MongoDB’s equals operator uses constant scoring by default, and for array values, MongoDB Search can assign higher scores when more array values match the query.

Your weighting also makes sense:

NPI exact match = 1000
SRC match = 2
license match = 2

That makes NPI an overwhelming deterministic signal while still allowing secondary identifiers to contribute.

For first/last name and nickname arrays, keeping them in should is also correct if you want documents matching more aliases or tokens to rank higher.

3. zip is probably the biggest easy win

Current HCP zip queries use:

wildcard: {
  path: "searchFields.zip",
  query: "19422*",
  allowAnalyzedField: true
}

Because zip is already mapped as:

"type": "string",
"analyzer": "lucene.keyword"

you likely do not need allowAnalyzedField: true. The wildcard operator is term-level, meaning the query itself is not analyzed; allowAnalyzedField: true is specifically for allowing wildcard over analyzed fields and changes how filters/token filters are applied.

For performance, consider one of these instead:

Best for exact 5-digit ZIPs:

{
  "equals": {
    "path": "searchFields.zip",
    "value": "19422"
  }
}

Best for ZIP prefixes if values include ZIP+4:

Create a normalized field like:

searchFields.zip5: "19422"

Then query with equals or in:

{
  "in": {
    "path": "searchFields.zip5",
    "value": ["19422", "19423"]
  }
}

If ZIP is intended to contribute to relevance, put that equals / in under must or should. If ZIP is only a hard location constraint, move it to filter.

4. address autocomplete should be reviewed carefully

The address query uses:

autocomplete: {
  query: ["555 Redbird Cir Ste 300"],
  path: "searchFields.address",
  tokenOrder: "sequential"
}

autocomplete is designed for incomplete input strings and requires the queried field to be indexed as an autocomplete field type. In the pasted HCO mapping, I don’t see searchFields.address mapped, and dynamic is false, so please verify the actual deployed HCO index includes address as an autocomplete field. Otherwise the mapping snippet and query are out of sync.

For performance, address matching usually improves if you split signals:

should: [
  {
    autocomplete: {
      query: "555 Redbird Cir Ste 300",
      path: "searchFields.address_autocomplete",
      tokenOrder: "sequential",
      score: { boost: { value: 5 } }
    }
  },
  {
    text: {
      query: "555 Redbird Cir Ste 300",
      path: "searchFields.address",
      score: { boost: { value: 2 } }
    }
  },
  {
    equals: {
      path: "searchFields.zip5",
      value: "19422",
      score: { boost: { value: 3 } }
    }
  }
]

That keeps address relevance score-bearing, while using ZIP as either a boosted signal or a filter depending on the desired behavior.

5. orgName fuzzy text with maxEdits: 2 and maxExpansions: 50 may be expensive

This query is likely one of the more expensive ones:

text: {
  query: ["BELLIN MEMORIAL HOSPITAL INC"],
  path: "searchFields.orgName",
  fuzzy: {
    maxEdits: 2,
    prefixLength: 0,
    maxExpansions: 50
  }
}

The costly parts are:

maxEdits: 2
prefixLength: 0
maxExpansions: 50

For performance tuning, try:

fuzzy: {
  maxEdits: 1,
  prefixLength: 2,
  maxExpansions: 20
}

Then use exact or normalized org-name fields as higher-confidence signals:

should: [
  {
    equals: {
      path: "searchFields.orgName_normalized",
      value: "bellin memorial hospital inc",
      score: { boost: { value: 20 } }
    }
  },
  {
    text: {
      query: "BELLIN MEMORIAL HOSPITAL INC",
      path: "searchFields.orgName",
      score: { boost: { value: 5 } }
    }
  },
  {
    text: {
      query: "BELLIN MEMORIAL HOSPITAL INC",
      path: "searchFields.orgName",
      fuzzy: {
        maxEdits: 1,
        prefixLength: 2,
        maxExpansions: 20
      },
      score: { boost: { value: 1 } }
    }
  },
  {
    equals: {
      path: "searchFields.orgName_SOUNDEX",
      value: "B455",
      score: { boost: { value: 1 } }
    }
  }
]

This makes the query cheaper and more controlled: exact normalized matches dominate, plain text matches help, fuzzy catches typos, and Soundex contributes lightly.
