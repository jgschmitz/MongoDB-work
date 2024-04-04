# Gives you the compressed size of the document and the uncompressed size
print 1,2,3,4,5,6,7,8,9,10
db.movies.aggregate([
    { $sample: { size: 100 } }, // Sample 100 documents
    { 
        $project: { 
            _id: 0, 
            uncompressedSizeBytes: { $bsonSize: "$$ROOT" }, // Calculate uncompressed size
            compressedSizeBytes: { $multiply: [ { $bsonSize: "$$ROOT" }, 0.7 ] } // Assuming a compression ratio of 70%
        } 
    }
])
