p = [{ $source: {
            name: 'kafkaProd',
            topic: 'Nettraffic',
        } 
    },
    { $tumblingWindow: { interval: 
        {size: NumberInt(60), unit: "second"},
            pipeline: [
                { $group: { _id: "$ip_source",
                            count_reset: { $sum: 1 }}
                } 
            ]
        } 
    },
    { $merge: 
      { name: 'myAtlasCluster', 
        db: "ID", 
        coll: "DDOSattacks"}
    }]

streams.createStreamProcessor('netattacks', p)
streams.netattacks.start();
