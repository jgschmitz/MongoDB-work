db.createCollection( <name>,
{
capped: <boolean>,
timeseries: { // Added in MongoDB 5.0
timeField: <string>, // required for time series collections
metaField: <string>,
granularity: <string>
},
expireAfterSeconds: <number>,
clusteredIndex: <document>, // Added in MongoDB 5.3
changeStreamPreAndPostImages: <document>, // Added in MongoDB 6.0
size: <number>,
max: <number>,
storageEngine: <document>,
validator: <document>,
validationLevel: <string>,
validationAction: <string>,
indexOptionDefaults: <document>,
viewOn: <string>,
pipeline: <pipeline>,
collation: <document>,
writeConcern: <document>,
streaming: <document>
}
)
