# Ulta Beauty Vector Search Recommendations

## Executive Recommendation

Do **not** create independent embeddings in the SKU, product, brand, and category collections for the primary product-discovery experience.

Keep those collections as the operational sources of truth, then create a separate denormalized search collection, such as:

```text
catalog_search
```

Use **one search document per sellable SKU**.

SKU is the recommended retrieval grain because color, shade, size, price, promotions, availability, and other variant-level attributes may differ even when multiple SKUs belong to the same parent product.

```text
SKU Collection ───────┐
Product Collection ───┤
Brand Collection ─────┼── Enrichment and embedding pipeline ──> catalog_search
Category Collection ──┘
```

The `catalog_search` collection becomes the optimized retrieval layer for:

- Vector search
- Full-text search
- Hybrid search
- Faceting
- Filtering
- Result grouping
- Product ranking

---

## Why a Separate Search Collection

The current catalog information is distributed across multiple collections:

- Product
- SKU
- Brand
- Category

A search request should not need to perform runtime joins across all four collections before searching.

A materialized search collection provides several advantages:

- Product, SKU, brand, and category data is already combined.
- Search documents can be shaped specifically for retrieval.
- Frequently changing fields can be updated without regenerating embeddings.
- Vector, text, filter, and facet fields can be indexed together.
- Search results can be returned at the SKU level and grouped by product.
- Search workloads remain separate from the operational catalog model.

---

## Recommended Retrieval Grain

### One document per sellable SKU

A SKU-level document allows the search system to distinguish between:

- Colors
- Shades
- Sizes
- Forms
- Finishes
- Prices
- Sale status
- Promotions
- Inventory status
- Coupon eligibility
- Variant-specific descriptions

For example, a customer searching for:

> dark blue glossy press-on nails that do not require glue

should retrieve the exact matching SKU rather than only the parent product.

The application can group search results by `productId` after retrieval so that many variants of the same product do not dominate the result set.

---

## Fields That Should Be Embedded

The embedding should describe:

- What the product is
- What it does
- Its important characteristics
- The customer concern or need it addresses
- Its relevant variant attributes
- Its position within the product taxonomy

Recommended semantic fields include:

| Source field | Recommendation |
|---|---|
| `product_name` | Embed and full-text index |
| `brand` | Embed and exact/text index |
| Product `description` | Embed |
| SKU `description1` feature content | Embed |
| Category names tier 1–3 | Embed and filter |
| Full category path | Embed and filter |
| `color` | Embed and filter |
| `shade_description` | Embed and filter |
| `color_accessories` | Embed and filter |
| `color_eyes` | Embed and filter |
| `color_hair` | Embed and filter |
| `color_lips` | Embed and filter |
| `color_nails` | Embed and filter |
| `finish` and specialized finish fields | Embed and filter |
| `form` and specialized form fields | Embed and filter |
| `concerns_hair` | Embed and filter |
| `concerns_skin` | Embed and filter |
| Benefits | Embed and filter |
| Coverage | Embed and filter |
| Skin type | Embed and filter |
| Treatment | Embed and filter |
| Scent | Embed and filter |
| SPF value | Embed when populated and also filter |
| Positive product attributes | Embed as descriptors and also filter |

Do not send the complete raw JSON document directly to the embedding model.

Instead, construct a deliberate, readable text representation.

---

## Example Embedding Text

For the sample nail SKU, the text sent to the embedding model could look like this:

```text
Product: WICKED X imPRESS Press On Nails
Brand: KISS
Category: Nail > Artificial Nails > Press-On Nails
Description: A set of 30 short, dark blue squoval press-on nails with a glossy
chrome and gold gel flocking effect. Pre-applied adhesive provides an instant,
no-glue manicure with up to 10-day hold.
Color: Blue
Shade: Dark blue glossy
Variant: Welcome To Shiz
Form: Press-on nails
Features: No glue, pre-applied adhesive, up to 10-day hold, manicure tools included
Attributes: Sustainable packaging, positive impact
```

This text gives the embedding model strong semantic material for searches such as:

- dark blue press-on nails
- nails that do not need glue
- quick manicure with adhesive already applied
- glossy blue artificial nails
- press-on nails with long hold

---

## Important Boolean Handling

Only include a boolean attribute in the embedding text when the value is positive and useful.

### Recommended

```text
Attributes: Vegan, cruelty-free, sustainable packaging
```

### Not recommended

```text
Vegan: false
Cruelty-free: false
Clean ingredients: false
```

Embedding negative labels can still associate the product with those concepts.

For example, including `vegan: false` may unintentionally increase similarity for a query containing the word `vegan`.

Keep the actual boolean values as structured filter fields regardless of whether they are included in the embedding text.

---

## Fields That Should Remain Structured Filters

The following fields should generally not be embedded because they are:

- Identifiers
- Exact values
- Rapidly changing values
- Transactional values
- Eligibility constraints
- Operational status values
- Better handled through filtering or lexical search

Recommended filter or exact-match fields include:

```text
sku
product_id
brand_id
category_ids
price
on_sale_price
new_arrival
on_sale
average_rating
is_coupon_eligible
in_stock
promo_events
gwp
bmsm
prestige
pricing_category
live_status
approval_status
launch_date
start_date
end_date
hazmat_code
max_quantity
upc_number
fsa_hsa_eligible
subscription_eligible
clearance
ulta_exclusive
```

These fields can be included as filter fields in the Vector Search index or indexed in MongoDB Search for exact matching, filtering, and faceting.

---

## Example Filtered Vector Query

```javascript
db.catalog_search.aggregate([
  {
    $vectorSearch: {
      index: "catalog_vector_index",
      path: "productEmbedding",
      queryVector: queryEmbedding,
      numCandidates: 200,
      limit: 20,
      filter: {
        inStock: true,
        liveStatus: "LIVE",
        price: { $lte: 25.00 },
        categoryKeys: "c10119"
      }
    }
  }
])
```

The prefilter ensures that only products meeting the customer's hard constraints participate in the semantic search.

---

## Proposed `catalog_search` Document

```javascript
{
  _id: "2643568",

  sku: "2643568",
  productId: "pimprod2052659",

  productName: "WICKED X imPRESS Press On Nails",
  brandId: "1471",
  brandName: "KISS",

  categoryKeys: [
    "nail",
    "artificial-nails",
    "press-on-nails"
  ],

  categoryPath: [
    "Nail",
    "Artificial Nails",
    "Press-On Nails"
  ],

  description:
    "A set of 30 short, blue, squoval press-on nails...",

  features: [
    "No glue",
    "Pre-applied adhesive",
    "Up to 10-day hold",
    "No damage to natural nails"
  ],

  variant: {
    type: "Color",
    value: "Welcome To Shiz",
    color: ["Blue"],
    shadeDescription: "dark blue glossy"
  },

  attributes: {
    vegan: false,
    crueltyFree: false,
    cleanIngredients: false,
    sustainablePackaging: true,
    positiveImpact: true,
    hasCBD: false,
    couponEligible: true
  },

  merchandising: {
    pricingCategory: "Mass",
    originalPrice: 10.99,
    salePrice: null,
    onSale: false,
    inStock: true,
    newArrival: true,
    averageRating: null
  },

  embeddingText:
    "Product: WICKED X imPRESS Press On Nails ...",

  productEmbedding: [
    /* embedding vector */
  ],

  embeddingContentHash: "sha256-value",
  embeddingModel: "model-name-and-version",
  embeddingUpdatedAt: ISODate("2026-08-04T00:00:00Z"),

  sourceUpdatedAt: ISODate("2026-07-29T00:37:41.647Z")
}
```

---

## Product Collection Responsibilities

Use the product collection to provide:

- Parent product name
- Product-level description
- Product type
- Review count
- Average rating
- Category relationships
- Product URL
- Associated SKU IDs
- Product live and approval status

These values should be copied into the SKU-level search document where relevant.

---

## SKU Collection Responsibilities

Use the SKU collection to provide:

- Detailed feature descriptions
- Ingredients
- How-to-use instructions
- Color and shade
- Variant type and value
- Form
- Finish
- Product concerns
- Benefits
- Price
- Sale status
- Promotion eligibility
- Inventory availability
- Coupon eligibility
- Clean, vegan, cruelty-free, and sustainability attributes
- Launch and availability dates
- UPC and exact SKU identifiers

Not every SKU field should be placed in the embedding text. Many belong only as structured search fields.

---

## Brand Collection Responsibilities

For the main shopping search experience, the brand collection generally does not require a separate vector.

Copy the following into each relevant catalog search document:

- Brand ID
- Brand name
- Brand-level clean ingredient status
- Brand-level cruelty-free status
- Brand-level vegan status
- Brand-level sustainable packaging status
- Brand live and approval status

A separate brand embedding would only be justified for a standalone brand-discovery experience such as:

> Show me brands focused on sustainable luxury skincare.

That experience would also require richer brand descriptions than the sample brand document currently contains.

---

## Category Collection Responsibilities

Use the category collection to resolve:

- Category ID
- Category name
- Parent category
- Ancestor hierarchy
- Full category path
- SEO description
- Category state
- Category start and end dates

The category sample contains ancestor keys but does not contain all ancestor names inside the same document.

The enrichment pipeline should resolve those keys against the category collection and persist the completed category path.

Example:

```text
Beauty > Body Care > Self-Care & Wellness > Intimate Wellness
```

The full path is valuable both semantically and structurally:

- Embed it for intent matching.
- Index it as a filter.
- Use it for facets and navigation.
- Use it for category-aware ranking.

---

## Recommended Search Strategy

Use hybrid search rather than vector-only search.

Product discovery contains many exact lexical signals:

- Brand names
- Product names
- Shade names
- Category names
- Ingredient names
- SKUs
- UPC numbers
- Product IDs
- Promotional terminology

These signals are often best handled by full-text or exact search.

Semantic intent is best handled by vector search.

Examples of semantic queries include:

- something for dry damaged curls
- gentle cleanser for sensitive skin
- long-lasting glossy red lip product
- quick manicure without nail glue
- lightweight foundation for oily skin

The strongest experience combines:

1. Full-text search
2. Vector search
3. Structured filters
4. Business ranking signals
5. Result grouping by product

---

## Suggested Hybrid Ranking Signals

After text and vector retrieval, ranking can incorporate:

- Vector similarity
- Text relevance
- Exact brand match
- Exact product-name match
- Exact shade match
- Category match
- In-stock status
- Product live status
- Average rating
- Review count
- New-arrival status
- Promotion status
- Ulta-exclusive status
- Business merchandising rules

Price, inventory, and promotions should influence filtering or ranking, but they should not require generating a new embedding.

---

## Embedding Refresh Strategy

Do not regenerate embeddings every time the source document changes.

Regenerate an embedding only when semantic content changes, such as:

- Product name
- Product description
- SKU feature descriptions
- Brand name
- Category path
- Color
- Shade description
- Form
- Finish
- Concerns
- Benefits
- Ingredients, when included
- Positive product attributes

Do not regenerate embeddings for changes to:

- Price
- Sale price
- Inventory
- Promotion status
- Coupon eligibility
- Average rating
- Review count
- Maximum quantity
- Notification status

These fields should be updated directly in the search document.

---

## Embedding Content Hash

Store a deterministic hash of the normalized embedding input:

```javascript
embeddingContentHash: "sha256-value"
```

Recommended process:

1. Build the normalized embedding text.
2. Generate a SHA-256 hash.
3. Compare it with the stored hash.
4. Skip embedding generation when the hash has not changed.
5. Generate a new embedding only when the hash changes.
6. Store the model name and embedding timestamp.

This avoids unnecessary embedding cost and processing.

---

## Recommended Data Flow

```text
Operational catalog collections
        |
        | Product, SKU, brand, or category change
        v
Change detection or scheduled enrichment process
        |
        | Resolve product, brand, category, and SKU data
        v
Build normalized catalog search document
        |
        | Compare semantic content hash
        +-------------------------------+
        |                               |
        | Semantic content changed      | Only dynamic fields changed
        v                               v
Generate new embedding          Update structured fields only
        |                               |
        +---------------+---------------+
                        v
                 catalog_search
                        |
                        v
         Text + Vector + Filters + Ranking
```

Possible implementation patterns include:

- Change Streams
- Scheduled batch enrichment
- Event-driven catalog pipeline
- Existing catalog publication workflow
- Initial bulk backfill followed by incremental updates

---

## Initial Backfill Process

A practical initial implementation would be:

1. Read all eligible live products.
2. Resolve their associated SKUs.
3. Resolve brand information.
4. Resolve full category paths.
5. Construct one normalized document per sellable SKU.
6. Create the normalized embedding text.
7. Generate embeddings in batches.
8. Insert or update documents in `catalog_search`.
9. Build the Search and Vector Search indexes.
10. Validate retrieval using real customer queries.

---

## Eligibility Rules for Search Documents

Only include SKUs that are eligible for the customer-facing search experience.

Potential rules include:

```text
Product state = PUBLISHED
Product live status = LIVE
Product approval status = APPROVED
SKU state = PUBLISHED
SKU live status = LIVE
SKU approval status = APPROVED
Current date is within start and end dates
SKU is dot-com sellable
```

The exact rules should be confirmed with the Ulta catalog team.

A product or SKU that becomes ineligible can either:

- Be removed from `catalog_search`, or
- Remain in the collection with `searchEligible: false`

Keeping it with an eligibility flag may simplify auditing and incremental updates.

---

## Recommended Index Responsibilities

### Vector Search index

Index:

- `productEmbedding` as a vector field
- Availability and eligibility fields as filters
- Price fields as filters
- Category IDs as filters
- Brand IDs as filters
- Product attributes as filters

### MongoDB Search index

Index:

- Product name
- Brand name
- Description
- Features
- Shade description
- Category path
- Ingredient names
- SKU
- UPC
- Product ID
- Promotional terms

Also configure facets where needed for:

- Brand
- Category
- Price range
- Rating
- Product attributes
- Color
- Form
- Finish
- Concern
- Availability

---

## Important Design Principle

The embedding is not the complete search index.

It should represent semantic meaning.

Structured fields should continue to handle:

- Hard constraints
- Exact identifiers
- Facets
- Sorting
- Inventory
- Price
- Promotions
- Eligibility
- Operational status

A strong product search architecture uses each search technique for the type of signal it handles best.

---

## Final Recommendation

Ulta should create a denormalized, SKU-level `catalog_search` collection that combines selected data from the product, SKU, brand, and category collections.

Each search document should contain:

- A carefully constructed semantic product description
- One product embedding
- Full-text searchable fields
- Exact identifiers
- Category hierarchy
- Filterable product attributes
- Dynamic merchandising fields
- Embedding metadata and a content hash

The customer-facing search experience should use hybrid retrieval:

```text
Full-text relevance
        +
Vector similarity
        +
Structured filters
        +
Business ranking
        +
Product-level result grouping
```

This design preserves the operational catalog model while creating a purpose-built retrieval layer that supports semantic product discovery without unnecessary embeddings or runtime joins.
