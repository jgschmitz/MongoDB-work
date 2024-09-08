function aggregateData(collection, field) {
  return db[collection].aggregate([
    // Match documents that fall within the last 24 hours
    {
      $match: {
        timestamp: {
          $gte: new Date(Date.now() - 24 * 60 * 60 * 1000),
          $lt: new Date()
        }
      }
    },
    // Group documents by hour and calculate the average of the specified field
    {
      $group: {
        _id: { 
          year: { $year: "$timestamp" }, 
          month: { $month: "$timestamp" },
          day: { $dayOfMonth: "$timestamp" },
          hour: { $hour: "$timestamp" }
        },
        [`avg_${field}`]: { $avg: `$value` }
      }
    }
  ]);
}

// Perform aggregation on each collection
const temperatureData = aggregateData('temperature', 'temperature');
const humidityData = aggregateData('humidity', 'humidity');
const pressureData = aggregateData('pressure', 'pressure');
