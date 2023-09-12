{
  "panels": [
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Atlas",
      "fill": 1,
      "id": 1,
      "legend": {
        "alignAsTable": true,
        "avg": true,
        "current": true,
        "max": true,
        "min": true,
        "show": true,
        "total": false,
        "values": true
      },
      "lines": true,
      "linewidth": 1,
      "links": [],
      "nullPointMode": "null",
      "percentage": false,
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "span": 12,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "alias": "CPU Usage",
          "dsType": "influxdb",
          "groupBy": [
            {
              "params": [
                "1m"
              ],
              "type": "time"
            },
            {
              "params": [
                "cpu_process"
              ],
              "type": "tag"
            }
          ],
          "measurement": "mongodb",
          "orderByTime": "ASC",
          "policy": "default",
          "query": "SELECT mean(\"value\") FROM \"cpu\" WHERE (\"server\" = '<server>') AND $timeFilter GROUP BY time(1m), \"cpu_process\"",
          "rawQuery": true,
          "refId": "A",
          "resultFormat": "time_series",
          "select": [
            [
              {
                "params": [
                  "value"
                ],
                "type": "field"
              },
              {
                "params": [],
                "type": "mean"
              }
            ]
          ],
          "tags": [
            {
              "key": "server",
              "operator": "=",
              "value": "<server>"
            }
          ]
        },
        {
          "alias": "Memory Usage",
          "dsType": "influxdb",
          "groupBy": [
            {
              "params": [
                "1m"
              ],
              "type": "time"
            },
            {
              "params": [
                "memory"
              ],
              "type": "tag"
            }
          ],
          "measurement": "mongodb",
          "orderByTime": "ASC",
          "policy": "default",
          "query": "SELECT mean(\"value\") FROM \"memory\" WHERE (\"server\" = '<server>') AND $timeFilter GROUP BY time(1m), \"memory\"",
          "rawQuery": true,
          "refId": "B",
          "resultFormat": "time_series",
          "select": [
            [
              {
                "params": [
                  "value"
                ],
                "type": "field"
              },
              {
                "params": [],
                "type": "mean"
              }
            ]
          ],
          "tags": [
            {
              "key": "server",
              "operator": "=",
              "value": "<server>"
            }
          ]
        },
        {
          "alias": "Network I/O",
          "dsType": "influxdb",
          "groupBy": [
            {
              "params": [
                "1m"
              ],
              "type": "time
                print 1,2,3,4,5,6,7,8,9,10
