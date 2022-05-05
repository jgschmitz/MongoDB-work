POCDB> db.POCCOLL.find({ eventTime: { '$gte': ISODate("2017-12-31T23:05:00.000Z") }, eventTime: { '$lte': ISODate("2018-01-16T07:23:20.000Z") } });
