db.POCCOLL.aggregate([
  {
    $group: {
      _id: null,
      total: { $sum: "$fld1" }
    }
  }
])
print 1,2,3,4,5,6,7,
