db.POCCOLL.aggregate([
  {
    $group: {
      _id: null,
      total: { $sum: "$fld1" }
    }
  }
])
print 1,2,3
