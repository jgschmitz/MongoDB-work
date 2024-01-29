[
    {
      $group:
        /**
         * _id: The id of the group.
         * fieldN: The first field name.
         */
        {
          _id: {
            TSF: "$tsf_id",
            LOG: "$log_file",
            LINE: {
              $floor: {
                $divide: ["$line_number", 10],
              },
            },
          },
          messages: {
            $addToSet: "$message",
          },
          min_datetime: {
            $min: "$datetime",
          },
          max_datetime: {
            $max: "$datetime",
          },
          message: {
            $accumulator: {
              accumulateArgs: ["$message"],
              init: function () {
                return [];
              },
              accumulate: function (names, name) {
                return names.concat(name);
              },
              merge: function (names1, names2) {
                return names1.concat(names2);
              },
              finalize: function (names) {
                return names.join("|");
              },
              lang: "js",
            },
          },
          level: {
            $accumulator: {
              accumulateArgs: ["$level"],
              init: function () {
                return [];
              },
              accumulate: function (names, name) {
                return names.concat(name);
              },
              merge: function (names1, names2) {
                return names1.concat(names2);
              },
              finalize: function (names) {
                return names.join("|");
              },
              lang: "js",
            },
          },
        },
    },
    {
      $project:
        /**
         * specifications: The fields to
         *   include or exclude.
         */
        {
          tsf_id: "$_id.TSF",
          line_number: "$_id.LINE",
          log_file: "$_id.LOG",
          message: "$message",
          level: "$level",
          min_datetime: "$min_datetime",
          max_datetime: "$max_datetime",
          message_number: {
            $cond: {
              if: {
                $isArray: "$messages",
              },
              then: {
                $size: "$messages",
              },
              else: 0,
            },
          },
          _id: "$$REMOVE"
        },
    },
    {
      $out:
        /**
         * Provide the name of the output collection.
         */
        "logs_combined",
    },
  ]
