#Generate your  API Key and ENDPOINT these will no longer work - 

ENDPOINT
--------

https://data.mongodb-api.com/app/data-amzuu/endpoint/data/beta

API KEY
--------
0vaT8d5Vh9cgvm3KdIQJWkl5M8alZgnoOczmApFlWVTMqisg24QWrUfMS0wkQ5Sj



curl https://data.mongodb-api.com/app/data-gvbow/endpoint/data/beta/action/insertOne \
-H 'Content-Type: application/json'  \
-H 'api-key: iH9yTg74wiRor93BzQlU1TADJ0RLhaZWWTp3RnUrUMPGpoaY4mWe8953UxkUadHw' \
--data-raw \
'{ 
  "dataSource": "Google-Terraform", 
  "database" : "Household", 
  "collection" : "pets", 
  "document" : { "name": "Harvest",
                 "breed": "Labrador",
                 "age": 5 }
}' 


curl https://data.mongodb-api.com/app/data-gvbo/endpoint/data/beta/action/findOne \
-H 'Content-Type: application/json'  \
-H 'api-key: BbhcEUTGyXZI6w6IuuLoHifHhdTlzOfmJfzcgFtcwas4zEImky55H47tlDlVfQHa' \
--data-raw \
'{ 
  "dataSource": "Cluster0", 
  "database" : "household", 
  "collection" : "pets", 
  "filter" : {"name" : "Harvest" }
}' 


Postman
---------

https://tinyurl.com/atlasdapi


curl  https://data.mongodb-api.com/app/data-amzuu/endpoint/data/beta/action/insertMany \
-H 'Content-Type: application/json'  \
-H 'api-key: BbhcEUTGyXZI6w6IuuLoHifHhdTlzOfmJfzcgFtcwas4zEImky55H47tlDlVfQHa' \
--data-raw \
'{
    "dataSource": "Cluster0",
    "database": "household",
    "collection": "pets",
    "documents": [{
            "name": "Brea",
            "breed": "Labrador",
            "age": 9,
            "colour": "black"
        },
        {
            "name": "Bramble",
            "breed": "Labrador",
            "age": 1,
            "colour": "black"
        }
    ]
}'

curl  https://data.mongodb-api.com/app/data-amzuu/endpoint/data/beta/action/find \
-H 'Content-Type: application/json'  \
-H 'api-key: BbhcEUTGyXZI6w6IuuLoHifHhdTlzOfmJfzcgFtcwas4zEImky55H47tlDlVfQHa' \
--data-raw \
'{
    "dataSource": "Cluster0", 
    "database": "household", 
    "collection": "pets", 
    "filter": { "breed": "Labrador",
                 "age": { "$gt" : 2} },
    "sort": { "age": 1 } }
'

curl  https://data.mongodb-api.com/app/data-amzuu/endpoint/data/beta/action/updateOne \
-H 'Content-Type: application/json'  \
-H 'api-key: BbhcEUTGyXZI6w6IuuLoHifHhdTlzOfmJfzcgFtcwas4zEImky55H47tlDlVfQHa' \
--data-raw \
'{  
    "dataSource": "Cluster0",
    "database": "household", 
    "collection": "pets",
    "filter" : { "name" : "Harvest"},
    "update" : { "$set" : { "colour": "yellow" }}
}'



curl  https://data.mongodb-api.com/app/data-amzuu/endpoint/data/beta/action/aggregate \
-H 'Content-Type: application/json'  \
-H 'api-key: 0vaT8d5Vh9cgvm3KdIQJWkl5M8alZgnoOczmApFlWVTMqisg24QWrUfMS0wkQ5Sj' \
--data-raw \
'{  
    "dataSource": "Cluster0",
    "database": "household", 
    "collection": "pets",
    "pipeline" : [ { "$match": {"breed": "Labrador"}}, 
                   { "$group": { "_id" : "$colour",
                          "count" : { "$sum" : 1},
                          "average_age": {"$avg": "$age" }}}]}'
