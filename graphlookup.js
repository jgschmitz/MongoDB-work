(() => {
  const categories = db.getCollection("product_categories");

  // 1. Seed data — safe to rerun without duplicate-key errors.
  const sampleData = [
    { _id: 1, name: "Products", parent_id: null },
    { _id: 2, name: "Digital & Electronics", parent_id: 1 },
    { _id: 3, name: "Clothing", parent_id: 1 },
    { _id: 4, name: "Books", parent_id: 1 },
    { _id: 5, name: "Mobile Phone", parent_id: 2 },
    { _id: 6, name: "Mobile Phone Accessories", parent_id: 5 },
    { _id: 7, name: "Mobile Phone Pouch Covers", parent_id: 6 },
    { _id: 8, name: "Mobile Phone Power Banks", parent_id: 6 }
  ];

  categories.bulkWrite(
    sampleData.map(({ _id, ...fields }) => ({
      updateOne: {
        filter: { _id },
        update: { $set: fields },
        upsert: true
      }
    }))
  );

  // 2. Support downward traversal.
  // Upward traversal uses the existing _id index.
  categories.createIndex({ parent_id: 1 });

  // 3. Immediate children — a simple find is sufficient.
  function getChildren(categoryId) {
    return categories
      .find(
        { parent_id: categoryId },
        { _id: 1, name: 1, parent_id: 1 }
      )
      .sort({ name: 1, _id: 1 })
      .toArray();
  }

  // 4. All descendants — nearest levels first.
  function getDescendants(categoryId) {
    return categories.aggregate([
      { $match: { _id: categoryId } },
      {
        $graphLookup: {
          from: categories.getName(),
          startWith: "$_id",
          connectFromField: "_id",
          connectToField: "parent_id",
          as: "descendants",
          depthField: "depth"
        }
      },
      {
        $set: {
          descendants: {
            $sortArray: {
              input: "$descendants",
              sortBy: { depth: 1, name: 1, _id: 1 }
            }
          }
        }
      },
      {
        $project: {
          name: 1,
          descendantCount: { $size: "$descendants" },
          "descendants._id": 1,
          "descendants.name": 1,
          "descendants.parent_id": 1,
          "descendants.depth": 1
        }
      }
    ]).toArray();
  }

  // 5. All ancestors — root first, plus a readable breadcrumb.
  function getAncestors(categoryId) {
    return categories.aggregate([
      { $match: { _id: categoryId } },
      {
        $graphLookup: {
          from: categories.getName(),
          startWith: "$parent_id",
          connectFromField: "parent_id",
          connectToField: "_id",
          as: "ancestors",
          depthField: "depth"
        }
      },
      {
        $set: {
          ancestors: {
            $sortArray: {
              input: "$ancestors",
              sortBy: { depth: -1, _id: 1 }
            }
          }
        }
      },
      {
        $project: {
          name: 1,
          "ancestors._id": 1,
          "ancestors.name": 1,
          "ancestors.depth": 1,
          breadcrumb: {
            $reduce: {
              input: {
                $concatArrays: ["$ancestors.name", ["$name"]]
              },
              initialValue: "",
              in: {
                $cond: [
                  { $eq: ["$$value", ""] },
                  "$$this",
                  { $concat: ["$$value", " > ", "$$this"] }
                ]
              }
            }
          }
        }
      }
    ]).toArray();
  }

  // 6. Run the examples.
  print("\nImmediate children of Products:");
  printjson(getChildren(1));

  print("\nAll descendants of Products:");
  printjson(getDescendants(1));

  print("\nAncestors and breadcrumb for Mobile Phone Accessories:");
  printjson(getAncestors(6));
})();
