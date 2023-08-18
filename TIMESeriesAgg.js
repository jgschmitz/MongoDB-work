db.network_data.aggregate([
  {
    $match: {
      // Add your filtering criteria here if needed
    }
  },
  {
    $group: {
      _id: "$_source.ns",
      count: { $sum: 1 },
      avgAlertMs: { $avg: "$_source.alertMs" },
      maxTotalMs: { $max: "$_source.totalMs" }
    }
  }
])
