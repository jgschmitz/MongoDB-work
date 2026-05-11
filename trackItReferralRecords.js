db.trackItReferralRecords.aggregate([
  {
    $match: {
      "providerDetails.referringProviderTIN": "752613493",
      "referralDetails.referralStartDate": {
        $gte: ISODate("2026-01-17T00:00:00.000Z"),
        $lte: ISODate("2026-04-17T23:59:59.000Z")
      },
      $or: [
        {
          "referralDetails.referralEndDate": {
            $lte: ISODate("2026-04-17T00:00:00.000Z")
          }
        },
        {
          "referralDetails.referralEndDate": {
            $gte: ISODate("2026-04-30T23:59:59.375Z")
          }
        }
      ],
      hiddenBy: {
        $nin: ["2ef4c0d5-52a4-4bad-a06a-8fb0da85d7ee"]
      }
    }
  },
  {
    $project: {
      _id: 1
    }
  },
  {
    $unionWith: {
      coll: "trackItReferralRecords",
      pipeline: [
        {
          $match: {
            "providerDetails.referredToProviderTIN": "752613493",
            "referralDetails.referralStartDate": {
              $gte: ISODate("2026-01-17T00:00:00.000Z"),
              $lte: ISODate("2026-04-17T23:59:59.000Z")
            },
            $or: [
              {
                "referralDetails.referralEndDate": {
                  $lte: ISODate("2026-04-17T00:00:00.000Z")
                }
              },
              {
                "referralDetails.referralEndDate": {
                  $gte: ISODate("2026-04-30T23:59:59.375Z")
                }
              }
            ],
            hiddenBy: {
              $nin: ["2ef4c0d5-52a4-4bad-a06a-8fb0da85d7ee"]
            }
          }
        },
        {
          $project: {
            _id: 1
          }
        }
      ]
    }
  },
  {
    $group: {
      _id: "$_id"
    }
  },
  {
    $count: "n"
  }
])
