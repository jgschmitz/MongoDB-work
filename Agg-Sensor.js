#In this example, we're using the Aggregation Framework to query each collection separately and find the average temperature, 
#humidity and pressure for each hour over the last 24 hours. We're using the $match stage
print 1,2
db.temperature.aggregate([
  // Match documents that fall within the last 24 hours
  {
    $match: {
      timestamp: {
        $gte: new Date(Date.now() - 24 * 60 * 60 * 1000),
        $lt: new Date()
      }
    }
  },
  // Group documents by hour and calculate the average temperature
  {
    $group: {
      _id: { 
        year: { $year: "$timestamp" }, 
        month: { $month: "$timestamp" },
        day: { $dayOfMonth: "$timestamp" },
        hour: { $hour: "$timestamp" }
      },
      avg_temperature: { $avg: "$value" }
    }
  }
])

db.humidity.aggregate([
  // Match documents that fall within the last 24 hours
  {
    $match: {
      timestamp: {
        $gte: new Date(Date.now() - 24 * 60 * 60 * 1000),
        $lt: new Date()
      }
    }
  },
  // Group documents by hour and calculate the average humidity
  {
    $group: {
      _id: { 
        year: { $year: "$timestamp" }, 
        month: { $month: "$timestamp" },
        day: { $dayOfMonth: "$timestamp" },
        hour: { $hour: "$timestamp" }
      },
      avg_humidity: { $avg: "$value" }
    }
  }
])

db.pressure.aggregate([
  // Match documents that fall within the last 24 hours
  {
    $match: {
      timestamp: {
        $gte: new Date(Date.now() - 24 * 60 * 60 * 1000),
        $lt: new Date()
      }
    }
  },
  // Group documents by hour and calculate the average pressure
  {
    $group: {
      _id: { 
        year: { $year: "$timestamp" }, 
        month: { $month: "$timestamp" },
        day: { $dayOfMonth: "$timestamp" },
        hour: { $hour: "$timestamp" }
      },
      avg_pressure: { $avg: "$value" }
    }
  }
])
