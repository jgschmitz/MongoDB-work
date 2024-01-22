{
  "fields": [
    {
      "type": "vector",
      "path": "plot_embedding",
      "numDimensions": 1536,
      "similarity": "euclidean"
    },
    {
      "type": "filter",
      "path": "genres"
    },
    {
      "type": "filter",
      "path": "year"
    }
  ]
}
