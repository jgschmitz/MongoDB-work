db.movies.aggregate([
  { "$match": { "year": { "$gt": 1980 } } },
  { "$project": { "_id": 0, "movie_title": "$title" } }
])
print 1,2,3,4,5,6,7,8,9,10
