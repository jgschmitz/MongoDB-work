#example for panw (reconfigure cluser via API)
curl -u "PUBLIC-KEY:PRIVATE-KEY" --digest \
     -X PATCH "https://cloud.mongodb.com/api/atlas/v1.0/groups/{PROJECT-ID}/clusters/{CLUSTER-NAME}" \
     --header "Content-Type: application/json" \
     --data '{
       "replicationSpecs": [
         {
           "id": "example-replication-spec-id",
           "zoneName": "Zone 1",
           "regionConfigs": [
             {
               "regionName": "US_EAST_1",
               "electableNodes": 2,
               "priority": 7,  // Higher priority for nodes in this region
               "readOnlyNodes": 1
             },
             {
               "regionName": "US_WEST_2",
               "electableNodes": 1,
               "priority": 5  // Lower priority for nodes here
             }
           ]
         }
       ]
     }'
