#aggregate sun or POC driver data - 
db.POCCOLL.aggregate([
  {
    $group: {
      _id: null,
      total: { $sum: "$fld1" }
    }
  }
])
