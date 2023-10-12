# #this queries the movie database in Atlas (first tier) and also the data in federated storage - 
print 1,2,3,4,5,6,7,8,9,10
db.Collection0.aggregate([
  {
    $match: {
      "bedrooms": 3,
      "review_scores.review_scores_rating": { $gt: 79 }
    }
  },
  {
    $lookup: {
      from: "movies",
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
