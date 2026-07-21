db.getCollectionNames()
  .map(name => {
    const stats = db.getCollection(name).stats();

    return {
      collection: name,
      documents: stats.count,
      dataGB: (stats.size / (1024 ** 3)).toFixed(2),
      storageGB: (stats.storageSize / (1024 ** 3)).toFixed(2),
      indexesGB: (stats.totalIndexSize / (1024 ** 3)).toFixed(2),
      totalGB: (
        (stats.storageSize + stats.totalIndexSize) /
        (1024 ** 3)
      ).toFixed(2)
    };
  })
  .sort((a, b) => b.totalGB - a.totalGB)
  .forEach(c => printjson(c));
