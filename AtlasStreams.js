#some advanced processing with streams - 

            p = [
    {
        $source: {
            name: 'kafkaProd',
            topic: 'Nettraffic',
        } 
    },
    // 1. Filtering Specific Traffic
    {
        $match: { 
            ip_source: { $nin: ["192.168.1.1", "10.0.0.1"] } 
        }
    },
    // 2. Enriching Data with GeoIP Information
    {
        $lookup: {
            from: "GeoIP",
            localField: "ip_source",
            foreignField: "ip",
            as: "geo_info"
        }
    },
    // 3. Grouping by IP Source and Calculating Metrics
    {
        $tumblingWindow: {
            interval: {size: NumberInt(60), unit: "second"},
            pipeline: [
                {
                    $group: { 
                        _id: "$ip_source",
                        count_reset: { $sum: 1 },
                        avg_packet_size: { $avg: "$packet_size" },
                        max_packet_size: { $max: "$packet_size" },
                        min_packet_size: { $min: "$packet_size" }
                    }
                }
            ]
        }
    },
    // 4. Identifying Anomalies
    {
        $match: {
            count_reset: { $gt: 1000 }  // Example threshold for anomaly detection
        }
    },
    // 5. Adding Alert Field Based on Anomaly Detection
    {
        $project: {
            _id: 0,
            ip_source: 1,
            count_reset: 1,
            avg_packet_size: 1,
            max_packet_size: 1,
            min_packet_size: 1,
            alert: { $cond: { if: { $gt: ["$count_reset", 1000] }, then: "ALERT", else: null } },
            geo_info: 1
        }
    },
    // 6. Merging the Results into the MongoDB Collection
    {
        $merge: {
            name: 'myAtlasCluster', 
            db: "ID", 
            coll: "DDOSattacks"
        }
    }
]

// Creating and starting the stream processor
streams.createStreamProcessor('netattacks', p);
streams.netattacks.start();
