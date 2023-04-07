db.POCCOLL.aggregate([
  {
    $group: {
      _id: null,
      total: { $sum: "$fld1" }
    }
  }
])
pr
