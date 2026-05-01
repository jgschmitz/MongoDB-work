# Atlas Search Address
OrgName Query Recommendation

Actually sharing the Elastic Query was actually super helpful 
Im thinking org-name fuzzy might actually be the problem here instead of the auto complete stage - 

The mapping confirms `searchFields.address` is correctly mapped as `autocomplete` with `edgeGram`, `minGrams: 3`, and `maxGrams: 12`; `orgName` is mapped as `string` with `lucene.standard`, plus a `keyword` multi-field; and `orgName_SOUNDEX` is a lowercase `token`.

For the address query, the explain shows the autocomplete clauses are being rewritten internally into a `TermQuery` prefix-ish piece plus a `PhraseQuery` with `slop: 0`. That is actually a pretty good conceptual translation from Elasticsearch `match_phrase_prefix`. Example: one address clause becomes a `TermQuery` on something like `825 old lanc` plus a `PhraseQuery` for `[825, old, lancaster, rd, ste, 440]` with `slop: 0`.

Performance-wise, the address query does not look bad. One shard shows around `5ms` context, around `0.6–1.0ms` match, and less than `0.4ms` scoring; total estimated time is around `65ms`, with only dozens of docs scored/collected, not hundreds of thousands.

The `orgName` query is the expensive one. Even after they tuned fuzzy to:

```js
fuzzy: {
  maxEdits: 1,
  prefixLength: 2,
  maxExpansions: 25
}
```

The explain still shows very high match and scoring work: roughly `259k–262k` `nextDoc` calls and around `214k–215k` scores/collects on shards, with estimated execution around `367–394ms`.

## Revised Recommendation

The address autocomplete mapping/query is structurally valid and the explain plan suggests Atlas Search is translating it in a way that resembles ES `match_phrase_prefix`: prefix term + slop-0 phrase. I would not prioritize address autocomplete unless relevance is wrong. The bigger performance concern is `orgName` fuzzy text, which is expanding into many term variants and causing hundreds of thousands of scored candidates.

## Address Query Recommendation

For the address query, I’d make only small changes:

```js
autocomplete: {
  query: "825 Old Lancaster Rd Ste 410",
  tokenOrder: "sequential",
  path: "searchFields.address"
}
```

Use a string, not a single-element array. Also, if multiple addresses are alternatives, the current nested `must -> should` shape is logically okay, but I’d make the intent explicit:

```js
compound: {
  should: [
    {
      autocomplete: {
        query: "2901 Dutton Mill Rd Ste 110",
        tokenOrder: "sequential",
        path: "searchFields.address"
      }
    },
    {
      autocomplete: {
        query: "825 Old Lancaster Rd Ste 410",
        tokenOrder: "sequential",
        path: "searchFields.address"
      }
    }
  ],
  minimumShouldMatch: 1,
  filter: [
    {
      in: {
        path: "metaData.source_code",
        value: [...]
      }
    }
  ]
}
```

## OrgName Query Recommendation

For `orgName`, I’d push harder on changing the query shape. Right now it is:

```js
should: [
  { equals: { path: "searchFields.orgName_SOUNDEX", value: "B455" } },
  { equals: { path: "searchFields.orgName_SOUNDEX", value: "PLNM" } },
  {
    text: {
      query: ["FMC EAST DEPERE"],
      path: "searchFields.orgName",
      fuzzy: { maxEdits: 1, prefixLength: 2, maxExpansions: 25 }
    }
  },
  {
    text: {
      query: ["BELLIN MEMORIAL HOSPITAL INC"],
      path: "searchFields.orgName",
      fuzzy: { maxEdits: 1, prefixLength: 2, maxExpansions: 25 }
    }
  }
]
```

I would split it into confidence tiers:

```js
compound: {
  should: [
    {
      text: {
        query: "BELLIN MEMORIAL HOSPITAL INC",
        path: "searchFields.orgName.keyword",
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
      equals: {
        path: "searchFields.orgName_SOUNDEX",
        value: "B455",
        score: { boost: { value: 1 } }
      }
    },
    {
      text: {
        query: "BELLIN MEMORIAL HOSPITAL INC",
        path: "searchFields.orgName",
        fuzzy: {
          maxEdits: 1,
          prefixLength: 3,
          maxExpansions: 10
        },
        score: { boost: { value: 0.5 } }
      }
    }
  ],
  minimumShouldMatch: 1,
  filter: [...]
}
```

Even better: add a normalized exact org-name token field, because `orgName.keyword` as a `string` with `lucene.keyword` is okay for exact-ish text scoring, but a lowercase normalized `token` field would be cleaner for deterministic equality:

```js
orgName_normalized: {
  type: "token",
  normalizer: "lowercase"
}
```

Then query:

```js
equals: {
  path: "searchFields.orgName_normalized",
  value: "bellin memorial hospital inc",
  score: { boost: { value: 20 } }
}
```

## Final Read

**Address:** mapping is valid; conversion from ES `match_phrase_prefix` to Atlas `autocomplete + tokenOrder: sequential` is reasonable. Clean up query array to string and keep validating relevance.

**OrgName:** still the main hotspot. The explain plan supports the original concern: fuzzy text is producing a lot of candidate traversal and scoring. Reduce fuzzy breadth further, make exact/normalized matches first-class, and avoid using fuzzy org-name as a high-weight primary signal.

Also add Text operator here is an example

```js
So one thing our search specialist is recommending is keep autocomplete, but add normal text + normalized exact fields

db.getCollection("hco_fragment_resource_latest").createSearchIndexes([
  {
    name: "hco_fragment_resource_latest_idx_v2",
    definition: {
      mappings: {
        dynamic: false,
        fields: {
          metaData: {
            type: "document",
            fields: {
              source_code: {
                type: "token",
                normalizer: "lowercase"
              }
            }
          },
          searchFields: {
            type: "document",
            fields: {
              address: {
                type: "autocomplete",
                minGrams: 3,
                maxGrams: 12,
                tokenization: "edgeGram",
                multi: {
                  text: {
                    type: "string",
                    analyzer: "lucene.standard"
                  },
                  keyword: {
                    type: "string",
                    analyzer: "lucene.keyword"
                  }
                }
              },
              address_normalized: {
                type: "token",
                normalizer: "lowercase"
              },
              zip: {
                type: "token",
                normalizer: "lowercase"
              }
            }
          }
        }
      }
    }
  }
])
```
