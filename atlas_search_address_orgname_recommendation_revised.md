# Revised Atlas Search Recommendation: Address Autocomplete vs Text/Phrase and orgName Fuzzy

## Executive summary

The address autocomplete query is structurally valid with the current Atlas Search mapping, and the provided explain plan does not show it as the immediate runtime hotspot. However, the search specialist's concern is valid: the sample query uses complete addresses, not partial user-entered prefixes. For complete address matching, `autocomplete` is probably not the best default operator or index shape.

The revised recommendation is:

- Use `autocomplete` only when the input is truly partial, such as typeahead or prefix matching.
- For complete address strings, benchmark `phrase` and `text` on a normal string-mapped address field.
- Add a normalized exact address token field for deterministic complete-address matches.
- Keep source-code eligibility in `filter`.
- Continue treating orgName fuzzy text as the larger performance concern, especially when fuzzy expansion creates hundreds of thousands of matched/scored candidates.

## Why the original autocomplete recommendation needs nuance

The original Elasticsearch query used `match_phrase_prefix`, so translating it to Atlas Search `autocomplete` with `tokenOrder: "sequential"` is conceptually understandable. Atlas Search autocomplete can behave like a prefix-oriented phrase match, and the explain plan showed internally generated pieces similar to a prefix term plus a slop-0 phrase query.

However, the sample they gave shows a full address being put into the search, for example:

```js
autocomplete: {
  query: "825 Old Lancaster Rd Ste 410",
  tokenOrder: "sequential",
  path: "searchFields.address"
}
```

That is different from a true typeahead or partial-prefix use case like:

```js
autocomplete: {
  query: "825 Old Lanc",
  tokenOrder: "sequential",
  path: "searchFields.address"
}
```

Autocomplete is useful for partial matches. If the application is usually passing complete addresses, then autocomplete may be doing unnecessary work and may require a larger index than needed.

## Search specialist concern

The search specialist's objection is fair:

> Why autocomplete instead of a text operator? Autocomplete indexes for this will be quite large, and that is a lot of matching.

That should be incorporated into the recommendation. The right answer is not simply "autocomplete is correct because Elasticsearch used `match_phrase_prefix`." A better answer is:

> Autocomplete is a reasonable migration equivalent for Elasticsearch `match_phrase_prefix` only if prefix behavior is actually required. If the input is a complete address, we should test `phrase` and `text` on a normal address string field and add an exact normalized address token. Autocomplete should be reserved for true partial-prefix behavior.

## Current mapping issue

The current mapping exposes `searchFields.address` as an autocomplete field:

```js
address: {
  type: "autocomplete",
  minGrams: 3,
  maxGrams: 12,
  tokenization: "edgeGram"
}
```

That makes the current autocomplete query valid, but it also means the team does not currently have a normal text/phrase address path to compare against unless another mapped field exists.

A better mapping for evaluation would provide separate paths for separate matching behaviors:

```js
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
```

This gives the team three distinct address signals:

| Field | Purpose |
|---|---|
| `searchFields.address` | Prefix/typeahead matching via autocomplete |
| `searchFields.address.text` | Full-text or phrase matching for complete addresses |
| `searchFields.address.keyword` | Keyword-style exact text matching |
| `searchFields.address_normalized` | Deterministic normalized exact matching |

## Recommended query pattern for complete addresses

For complete address input, prioritize exact and phrase-style matching before considering autocomplete.

### 1. Exact normalized address match

Normalize the input in the application, for example:

```text
825 Old Lancaster Rd Ste 410
```

becomes:

```text
825 old lancaster rd ste 410
```

Then query a normalized token field:

```js
{
  equals: {
    path: "searchFields.address_normalized",
    value: "825 old lancaster rd ste 410",
    score: {
      boost: {
        value: 20
      }
    }
  }
}
```

This should be the highest-confidence and likely lowest-cost signal for complete address matching.

### 2. Phrase match on normal address text

Use phrase matching when the address is complete but exact normalization may differ slightly:

```js
{
  phrase: {
    query: "825 Old Lancaster Rd Ste 410",
    path: "searchFields.address.text",
    slop: 0,
    score: {
      boost: {
        value: 8
      }
    }
  }
}
```

This captures the idea that the address tokens should appear together in order, without needing an autocomplete edge-gram index.

### 3. Text fallback

Use a lower-boost text fallback when phrase/exact matching is too strict:

```js
{
  text: {
    query: "825 Old Lancaster Rd Ste 410",
    path: "searchFields.address.text",
    score: {
      boost: {
        value: 3
      }
    }
  }
}
```

### 4. ZIP as a structured signal or filter

If ZIP is a hard eligibility condition, put it in `filter`:

```js
{
  equals: {
    path: "searchFields.zip",
    value: "19010"
  }
}
```

If ZIP should contribute to ranking but not exclude candidates, put it in `should` with a modest boost:

```js
{
  equals: {
    path: "searchFields.zip",
    value: "19010",
    score: {
      boost: {
        value: 3
      }
    }
  }
}
```

## Complete-address query example

```js
db.hco_fragment_resource_latest.aggregate([
  {
    $search: {
      index: "hco_fragment_resource_latest_idx_v2",
      compound: {
        should: [
          {
            equals: {
              path: "searchFields.address_normalized",
              value: "825 old lancaster rd ste 410",
              score: {
                boost: {
                  value: 20
                }
              }
            }
          },
          {
            phrase: {
              query: "825 Old Lancaster Rd Ste 410",
              path: "searchFields.address.text",
              slop: 0,
              score: {
                boost: {
                  value: 8
                }
              }
            }
          },
          {
            text: {
              query: "825 Old Lancaster Rd Ste 410",
              path: "searchFields.address.text",
              score: {
                boost: {
                  value: 3
                }
              }
            }
          }
        ],
        minimumShouldMatch: 1,
        filter: [
          {
            in: {
              path: "metaData.source_code",
              value: [
                "EPIM_RESOURCE",
                "EPIM",
                "NPPES",
                "RX_IRIS",
                "UHC_NDB"
              ]
            }
          }
        ]
      }
    }
  },
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      score: { $meta: "searchScore" },
      address: "$searchFields.address",
      address_normalized: "$searchFields.address_normalized",
      source_code: "$metaData.source_code"
    }
  }
])
```

## Prefix/typeahead query example

Keep autocomplete for partial user input, such as:

```text
825 Old Lanc
```

Query:

```js
db.hco_fragment_resource_latest.aggregate([
  {
    $search: {
      index: "hco_fragment_resource_latest_idx_v2",
      compound: {
        should: [
          {
            autocomplete: {
              query: "825 Old Lanc",
              path: "searchFields.address",
              tokenOrder: "sequential",
              score: {
                boost: {
                  value: 5
                }
              }
            }
          }
        ],
        minimumShouldMatch: 1,
        filter: [
          {
            in: {
              path: "metaData.source_code",
              value: [
                "EPIM_RESOURCE",
                "EPIM",
                "NPPES",
                "RX_IRIS",
                "UHC_NDB"
              ]
            }
          }
        ]
      }
    }
  },
  { $limit: 10 }
])
```

## How to evaluate the two approaches

Test the current autocomplete version against the proposed complete-address version using the same sample inputs and the same `source_code` filter.

Compare:

1. Total execution time estimate.
2. Number of matched/scored/collected documents.
3. Relevance of top 10 results.
4. Index size impact.
5. Whether the input is usually complete address data or partial user-entered prefixes.

The decision rule should be:

| Use case | Recommended operator/path |
|---|---|
| Complete normalized address | `equals` on `address_normalized` |
| Complete address with minor variation | `phrase` on `address.text` |
| Full address with token overlap tolerance | `text` on `address.text` |
| Partial prefix/typeahead | `autocomplete` on `address` |

## Revised conclusion

The address autocomplete query is valid under the current mapping, and the provided explain plan does not make it look like the immediate performance hotspot. However, the search specialist's point is important: the samples show complete addresses, and autocomplete is mainly useful for partial-prefix matching. Autocomplete indexes can also be large because they store edge grams for prefix matching.

Therefore, the recommendation should be revised:

> Do not default to autocomplete for complete address matching just because the Elasticsearch source query used `match_phrase_prefix`. Add and benchmark a normal string-mapped address field plus a normalized exact address token. Use exact/phrase/text for complete addresses, and keep autocomplete only for partial address prefixes or typeahead behavior.

## orgName remains the larger runtime concern

The orgName fuzzy query still appears to be the larger runtime hotspot in the provided explain data. Even with fuzzy settings such as:

```js
fuzzy: {
  maxEdits: 1,
  prefixLength: 2,
  maxExpansions: 25
}
```

it can still expand into many term variants and lead to hundreds of thousands of candidate traversals/scores. The orgName recommendation remains:

- Add a normalized exact org-name token field.
- Use exact/keyword matches as high-confidence signals.
- Use non-fuzzy text as a medium-confidence signal.
- Use fuzzy text as a low-boost fallback.
- Consider tighter fuzzy settings, such as `prefixLength: 3` and `maxExpansions: 10`, if relevance allows.

Example:

```js
compound: {
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
      equals: {
        path: "searchFields.orgName_SOUNDEX",
        value: "B455",
        score: {
          boost: {
            value: 1
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
          prefixLength: 3,
          maxExpansions: 10
        },
        score: {
          boost: {
            value: 0.5
          }
        }
      }
    }
  ],
  minimumShouldMatch: 1,
  filter: [
    {
      in: {
        path: "metaData.source_code",
        value: [
          "EPIM_RESOURCE",
          "EPIM",
          "NPPES",
          "RX_IRIS",
          "UHC_NDB"
        ]
      }
    }
  ]
}
```
