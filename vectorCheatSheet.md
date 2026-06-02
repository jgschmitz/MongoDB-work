# Vector & Hybrid Search: A Discovery Guide

A field guide for figuring out whether a customer needs vector search, hybrid
search, or nothing at all — and how to talk about it.

---

## 1. Does this customer need vector search?

Use these discovery questions, grouped by what you're trying to uncover.

### Understanding their data
- What kind of data are you searching over? (text, images, audio, code, documents)
  Unstructured data is the strongest signal for vector search.
- Is the *meaning* of the content more important than the exact words?
- Do your users describe what they want in their own words rather than exact keywords?

### Understanding the search problem
- When users search today, do they miss results because they used different words
  than what's in the data? (synonyms, paraphrasing)
- Do you need "find similar items" / recommendations (similar products, related
  documents, near-duplicate detection)?
- Is keyword/full-text search already "good enough" for your users?
- Do you need exact matching (SKUs, IDs, names, legal/financial terms)?

### AI / LLM signals
- Are you building (or planning) a chatbot, RAG system, or LLM-powered feature?
- Do you need to ground an LLM in your own private/proprietary data?

### Scale and practicality
- How much data, and how fast does it change?
- What latency and accuracy do you need?
- Do you have a way to generate embeddings, or is that a gap?

### Quick decision heuristics
- **Likely needs vector search:** unstructured data, semantic/natural-language
  queries, similarity/recommendations, RAG/LLM grounding.
- **Probably doesn't (yet):** structured data with exact filters, keyword search
  already works well, strict exact-match requirements.
- **Often the best answer is hybrid search** (vector + keyword).

---

## 2. Fuzzy search vs. vector search (they're not the same)

Fuzzy search and vector search solve different problems. They overlap only a little.

### What fuzzy search does — character-level / lexical variation
- Typos / misspellings: "recieve" → "receive"
- Minor variations: "color" vs "colour", plural/singular
- Edit distance (Levenshtein): how many character changes between two strings

It still needs the **same word** present, just spelled slightly differently.

### What fuzzy search does NOT do
- **Synonyms:** "car" won't find "automobile" or "vehicle."
- **Paraphrasing / concepts:** "how do I cancel my subscription" won't match
  "steps to end your membership."
- **Intent:** "affordable laptop for video editing" matching "budget notebook
  with strong GPU."

Vector search captures **meaning** (semantic similarity via embeddings), so it
matches concepts even with zero shared words.

### Side-by-side
| Query | Fuzzy match? | Vector match? |
|---|---|---|
| "recieve" → "receive" | Yes | Yes (but overkill) |
| "car" → "automobile" | No | Yes |
| "end my membership" → "cancel subscription" | No | Yes |
| "SKU-12345" → "SKU-12354" | Yes | Not reliably |

### Sharper discovery questions
- "When users use a completely different word for the same concept (synonyms,
  plain-language descriptions), do they still need to find the right result?"
  → that's vector, not fuzzy.
- "Are your search misses mostly typos, or mostly 'right idea, wrong words'?"
  Typos = fuzzy is enough. Wrong-words/concepts = vector.

---

## 3. A concrete vector search example

### The setup: a help-center search
A support knowledge base with these articles (each becomes an embedding):

| Article | Text |
|---|---|
| A | "How to cancel your subscription" |
| B | "Resetting your account password" |
| C | "Updating your billing payment method" |
| D | "Steps to end your membership and get a refund" |

### Step 1: Embed the documents
An embedding model turns each article into a vector (simplified to 3 numbers;
real ones have 768–3072 dimensions):

```
A → [0.91, 0.10, 0.05]
B → [0.05, 0.88, 0.12]
C → [0.20, 0.15, 0.80]
D → [0.89, 0.08, 0.14]
```

### Step 2: A user searches
Query: "how do I stop being billed every month"
(shares almost no keywords with any article — keyword/fuzzy would struggle)

```
Query → [0.88, 0.12, 0.20]
```

### Step 3: Compare by similarity (cosine similarity)
```
Query vs A ("cancel subscription")      → 0.97   best
Query vs D ("end membership + refund")  → 0.95   very close
Query vs C ("billing payment method")   → 0.71
Query vs B ("reset password")           → 0.18   unrelated
```

### Step 4: Return ranked results
```
1. How to cancel your subscription
2. Steps to end your membership and get a refund
3. Updating your billing payment method
```

The winning result shares **zero words** with the query. Fuzzy search would
never connect them; vector search did because their embeddings landed near each
other in meaning-space.

---

## 4. Why use hybrid search in Atlas

Hybrid search combines **Atlas Search** (full-text/keyword, BM25) with **Atlas
Vector Search** (semantic embeddings), fused via reciprocal rank fusion
(natively via `$rankFusion`).

1. **You need both meaning AND exact terms** — semantic recall without losing
   precision on must-match terms (SKUs, codes, names, legal/medical terms).
2. **Out-of-vocabulary / domain-specific terms** — embeddings are weak on
   internal product names, part numbers, jargon, brand-new terminology; keyword
   covers those gaps.
3. **RAG quality and grounding** — hybrid retrieval improves relevance of
   retrieved chunks and reduces "it was in the docs but we didn't retrieve it."
4. **Mixed query styles** — real queries blend both: "affordable SKU-4471 laptop
   for video editing."
5. **Better, more robust ranking** — fusing BM25 + vector similarity is more
   stable than either alone.
6. **Operational simplicity (Atlas-specific)** — both indexes live in the same
   cluster alongside operational data; one aggregation pipeline; combine with
   normal filters, `$match`, joins; one platform, one query language, one
   security/ops model.
7. **Graceful fallback** — if one method is poor for a niche query, the other
   still surfaces relevant results.

**Rule of thumb:** use hybrid when data has *both* unstructured natural-language
content *and* high-value exact tokens (IDs, names, codes), or when powering RAG
and you want maximum retrieval recall.

---

## 5. "We don't need search"

Usually one of three things: they mean keyword search specifically, they've
narrowly defined "search," or they genuinely don't have a retrieval problem.

### Reframe what "search" means
The same technology powers things they're probably already doing:
- Recommendations ("similar products," "related articles," "people also viewed")
- RAG / chatbots / AI assistants grounded in their own data
- Duplicate / near-duplicate detection (fraud, dedup, moderation)
- Classification, clustering, anomaly detection
- Personalization and matching (jobs↔candidates, content↔users)
- "Find similar" on images, audio, code

> "When I say search, I don't just mean a search box. I mean any time your app
> needs to find the most relevant items for a user or for an AI. Do any of those
> show up in your roadmap?"

### Diagnostic questions to surface hidden needs
- "Are you building anything with LLMs or planning to?"
- "How do users currently find things in your app?"
- "Do you ever need to show 'similar' or 'related' items?"
- "When a user can't find something, what happens?"
- "How do you handle unstructured data — documents, images, free text?"

### When they genuinely don't need it
Signals of a true "no":
- Purely transactional/structured workloads with exact-key lookups only.
- Small, static datasets where a simple filter is enough.
- No AI plans, no unstructured data, no "find similar" requirement.

Accept it gracefully and plant a seed:
> "Makes sense. If LLM features or recommendations ever land on your roadmap,
> this becomes relevant — happy to revisit then."

### Strategic angle
- **Don't sell search — sell the outcome:** lower support volume, higher
  conversion, a working AI assistant, less manual tagging.
- **Tie it to a current pain.** No pain and no roadmap need → accept the "no";
  credibility now earns the conversation later.

**One-liner for the room:**
> "Good to hear it's not a pain today. Quick gut check — are you doing anything
> with AI assistants, recommendations, or 'find similar' features? Those are
> search under the hood, and that's usually where teams discover they needed it
> without calling it search."
