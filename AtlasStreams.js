# updated - cleaner version 5.0

// Define the pipeline for stream processing
const pipeline = [
    // 1. Source: Kafka topic 'Nettraffic'
    {
        $source: {
            name: 'kafkaProd',
            topic: 'Networktraffic',
        }
    },
    // 2. Filter specific traffic
    {
        $match: {
            ip_source: { $nin: ["192.168.1.1", "10.0.0.1"] }
        }
    },
    // 3. Enrich data with GeoIP information
    {
        $lookup: {
            from: "GeoIP",
            localField: "ip_source",
            foreignField: "ip",
            as: "geo_info"
        }
    },
    // 4. Group by IP source and calculate metrics (tumbling window)
    {
        $tumblingWindow: {
            interval: { size: NumberInt(60), unit: "second" },
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
    // 5. Identify anomalies
    {
        $match: {
            count_reset: { $gt: 1000 } // Threshold for anomaly detection
        }
    },
    // 6. Add alert field based on anomaly detection
    {
        $project: {
            _id: 0,
            ip_source: 1,
            count_reset: 1,
            avg_packet_size: 1,
            max_packet_size: 1,
            min_packet_size: 1,
            alert: {
                $cond: {
                    if: { $gt: ["$count_reset", 1000] },
                    then: "ALERT",
                    else: null
                }
            },
            geo_info: 1
        }
    },
    // 7. Merge results into the MongoDB collection
    {
        $merge: {
            into: {
                db: "ID",
                coll: "DDOSattacks"
            },
            whenMatched: "merge", // Optional: Specify behavior for matching documents
            whenNotMatched: "insert"
        }
    }
];

// Create and start the stream processor
streams.createStreamProcessor('netattacks', pipeline);
streams.netattacks.start();
