db.movies.aggregate([
  { "$match": { "year": { "$gt": 1980 } } },
  { "$project": { "_id": 0, "movie_title": "$title" } }
])
