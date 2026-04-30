# Key Recommendations

## Keep `source_code` in `filter`

This is the right move. `source_code` is a hard eligibility condition, not a relevance signal. Putting it in `filter` reduces scoring work and avoids giving arbitrary score credit for source membership.

MongoDB explicitly recommends placing non-scoring operators such as `equals`, `range`, and `in` in `filter` when they are used only to constrain the candidate set.

### Cleanup Recommendation

In the HCO examples, you currently have both:

```js
filter: [
  {
    in: {
      path: "metaData.source_code",
      value: [..., "LNRS", ...]
    }
  }
],
mustNot: [
  {
    equals: {
      path: "metaData.source_code",
      value: "LNRS"
    }
  }
]
```

That works logically, but it is contradictory-looking and may add avoidable work.

Prefer removing `LNRS` from the `in` list if it should always be excluded.

---

## Preserve Scoring for Identifiers and Names

For `identifiers`, using multiple `equals` clauses inside `should` is appropriate because each matching identifier should add score.

MongoDB Search's `equals` operator uses constant scoring by default, and for array values, MongoDB Search can assign higher scores when more array values match the query.

Your weighting also makes sense:

```text
NPI exact match = 1000
SRC match       = 2
license match   = 2
```

That makes NPI an overwhelming deterministic signal while still allowing secondary identifiers to contribute.

For `firstName`, `lastName`, and nickname arrays, keeping them in `should` is also correct if you want documents matching more aliases or tokens to rank higher.

---

## `zip` Is Probably the Biggest Easy Win

Current HCP `zip` queries use:

```js
wildcard: {
  path: "searchFields.zip",
  query: "19422*",
  allowAnalyzedField: true
}
```

Because `zip` is already mapped as:

```json
{
  "type": "string",
  "analyzer": "lucene.keyword"
}
```

you likely do **not** need `allowAnalyzedField: true`.

The `wildcard` operator is term-level, meaning the query itself is not analyzed. `allowAnalyzedField: true` is specifically for allowing `wildcard` over analyzed fields and changes how filters/token filters are applied.

### Option 1: Exact 5-Digit ZIP Match

Best for exact 5-digit ZIPs:

```js
{
  equals: {
    path: "searchFields.zip",
    value: "19422"
  }
}
```

### Option 2: Normalized ZIP Prefix Match

Best for ZIP prefixes if values include ZIP+4.

Create a normalized field like:

```js
searchFields.zip5: "19422"
```

Then query with `equals` or `in`:

```js
{
  in: {
    path: "searchFields.zip5",
    value: ["19422", "19423"]
  }
}
```

If ZIP is intended to contribute to relevance, put that `equals` or `in` clause under `must` or `should`.

If ZIP is only a hard location constraint, move it to `filter`.

---

## Address Autocomplete Should Be Reviewed Carefully

The address query uses:

```js
autocomplete: {
  query: ["555 Redbird Cir Ste 300"],
  path: "searchFields.address",
  tokenOrder: "sequential"
}
```

`autocomplete` is designed for incomplete input strings and requires the queried field to be indexed as an `autocomplete` field type.

In the pasted HCO mapping, `searchFields.address` does not appear to be mapped, and `dynamic` is set to `false`.

Please verify that the actual deployed HCO index includes `address` as an `autocomplete` field. Otherwise, the mapping snippet and query are out of sync.

### Suggested Address Scoring Structure

For performance, address matching usually improves if you split signals:

```js
should: [
  {
    autocomplete: {
      query: "555 Redbird Cir Ste 300",
      path: "searchFields.address_autocomplete",
      tokenOrder: "sequential",
      score: {
        boost: {
          value: 5
        }
      }
    }
  },
  {
    text: {
      query: "555 Redbird Cir Ste 300",
      path: "searchFields.address",
      score: {
        boost: {
          value: 2
        }
      }
    }
  },
  {
    equals: {
      path: "searchFields.zip5",
      value: "19422",
      score: {
        boost: {
          value: 3
        }
      }
    }
  }
]
```

This keeps address relevance score-bearing, while using ZIP as either a boosted signal or a filter depending on the desired behavior.

---

## `orgName` Fuzzy Text May Be Expensive

The following query is likely one of the more expensive ones:

```js
text: {
  query: ["BELLIN MEMORIAL HOSPITAL INC"],
  path: "searchFields.orgName",
  fuzzy: {
    maxEdits: 2,
    prefixLength: 0,
    maxExpansions: 50
  }
}
```

The costly parts are:

```js
maxEdits: 2
prefixLength: 0
maxExpansions: 50
```

### Suggested Fuzzy Settings

For performance tuning, try:

```js
fuzzy: {
  maxEdits: 1,
  prefixLength: 2,
  maxExpansions: 20
}
```

### Suggested `orgName` Scoring Structure

Then use exact or normalized organization-name fields as higher-confidence signals:

```js
should: [
  {
    equals: {
      path: "searchFields.orgName_normalized",
      value: "bellin memorial hospital inc",
      score: {
        boost: {
          value: 20
        }
      }
    }
  },
  {
    text: {
      query: "BELLIN MEMORIAL HOSPITAL INC",
      path: "searchFields.orgName",
      score: {
        boost: {
          value: 5
        }
      }
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
      score: {
        boost: {
          value: 1
        }
      }
    }
  },
  {
    equals: {
      path: "searchFields.orgName_SOUNDEX",
      value: "B455",
      score: {
        boost: {
          value: 1
        }
      }
    }
  }
]
```

This makes the query cheaper and more controlled:

- Exact normalized matches dominate.
- Plain text matches help.
- Fuzzy matching catches typos.
- Soundex contributes lightly.
