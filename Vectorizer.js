db.collection.aggregate([
  {
    $search: {
      vector: {
        path: "vectorField",  // Replace with the actual field name storing vectors
        query: [-1.4445269107818604, -0.9201499819755554, -0.8022271990776062, 0.7475156784057617, 5.6226630210876465, -0.002624714048579335, 1.1049622297286987, 4.964395999908447, -0.48481523990631104, -1.4167524576187134, 5.99568510055542, 1.1963698863983154],
        neighbors: {
          $query: {},  // Additional query conditions for filtering (optional)
          $limit: 10   // Number of nearest neighbors to retrieve
        }
      }
    }
  }
])
