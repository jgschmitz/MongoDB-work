db.getCollectionNames().forEach(function(collectionName) {
  var stats = db[collectionName].aggregate([
    {
      $indexStats: {}
    },
    {
      $group: {
        _id: null,
        count: { $sum: 1 },
        totalOps: { $sum: "$accesses.ops" },
        totalSince: { $sum: "$accesses.since" },
        totalTime: { $sum: "$accesses.elapsedMicros" },
        totalMisses: { $sum: "$accesses.missRatio" },
        totalHitRatio: { $avg: "$accesses.hitRatio" },
        totalMissRatio: { $avg: "$accesses.missRatio" },
        totalCollScan: { $sum: "$executionStats.totalDocsExamined" },
        totalIndexScan: { $sum: "$executionStats.totalKeysExamined" }
      }
    }
  ]);
  print("Collection: " + collectionName);
  printjson(stats.toArray());
});
