function getCollectionIndexStats(db) {
  // Iterate over all collections in the database
  db.getCollectionNames().forEach((collectionName) => {
    try {
      const stats = db[collectionName].aggregate([
        {
          $indexStats: {}
        },
        {
          $group: {
            _id: null,
            totalIndexes: { $sum: 1 },
            totalOps: { $sum: "$accesses.ops" },
            totalSince: { $sum: "$accesses.since" },
            totalElapsedTimeMicros: { $sum: "$accesses.elapsedMicros" },
            totalMissRatio: { $avg: "$accesses.missRatio" },
            avgHitRatio: { $avg: "$accesses.hitRatio" },
            totalDocsExamined: { $sum: "$executionStats.totalDocsExamined" },
            totalKeysExamined: { $sum: "$executionStats.totalKeysExamined" }
          }
        }
      ]).toArray();

      // Output the results
      if (stats.length > 0) {
        print(`Collection: ${collectionName}`);
        printjson(stats[0]);
      } else {
        print(`Collection: ${collectionName} has no index statistics.`);
      }
    } catch (error) {
      print(`Error processing collection ${collectionName}: ${error.message}`);
    }
  });
}

// Call the function with the current database
getCollectionIndexStats(db);

