db.Collection0.aggregate([
  {
    $match: {
      "bedrooms": 3,
      "review_scores.review_scores_rating": { $gt: 79 }
    }
  },
  {
    $lookup: {
      from: "federatedSource.movies",  // Target federated storage explicitly
      let: { title: "$name" },
      pipeline: [
        {
          $match: {
            $expr: { $eq: ["$title", "$$title"] }
          }
        }
      ],
      as: "movies"
    }
  },
  {
    $project: {
      _id: 0,
      name: 1,
      numProperties: { $count: "numProperties" },
      movies: 1
    }
  }
])
