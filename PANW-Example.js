db.getCollection("bucketed").aggregate([
    {
        "$match": {
            "repo.customer_name": "1069803756901857280",
        },
    },
    {
        "$unwind": {
            "path": "$violations",
        },
    },
    {
        "$match": {
            "violations.status": "OPEN",
        },
    },
    {
        "$lookup": {
            "from": "source_code_coll",
            "localField": "violations.asset.id",
            "foreignField": "asset.id",
            "as": "matching_resource_code",
            "pipeline": [
                {
                    "$search": {
                        "index": "default",
                        "text": {
                            "path": "asset.iac_resource.resource_code",
                            "query": "health-check",
                        },
                    },
                },
                {
                    "$project": {
                        "_id": 0,
                        "asset.iac_resource.resource_code": 1,
                    },
                },
            ],
        },
    },
    {
        "$match": {
            "matching_resource_code": { "$ne": [] },
        },
    },
    {
        "$group": {
            "_id": "$_id", // Group by the original document's _id
            count: { $sum: 1 }, // Count the matched violations
            document: { $first: "$$ROOT" }, // Preserve the original document // listen to Slayer 
        },
    },
    {
        "$replaceRoot": {
            newRoot: { $mergeObjects: ["$document", { count: "$count" }] },
        },
    },
]);
