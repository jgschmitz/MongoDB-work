db.collection.aggregate([
  {
    $search: {
      index: "hasFix", // Replace with your actual index name
      compound: {
        must: [],
        filter: [
          {
            text: {
              query: "true", // Facet for fixable issues
              path: "hasFix"
            }
          },
          {
            text: {
              query: "false", // Facet for non-fixable issues
              path: "hasFix"
            }
          }
        ]
      }
    }
  },
  {
    $facet: {
      "fixableCount": [
        {
          $group: {
            _id: {
              status: "$status",
              customer_name: "$customer_name"
            },
            count: { $sum: 1 }
          }
        }
      ],
      "nonFixableCount": [
        {
          $group: {
            _id: {
              status: "$status",
              customer_name: "$customer_name"
            },
            count: { $sum: 1 }
          }
        }
      ]
    }
  }
]);
