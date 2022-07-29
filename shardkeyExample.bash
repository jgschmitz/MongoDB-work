#!/usr/bin/env bash

echo ">>> Clean up processes and files from previous runs"
echo ">>> killAll mongod mongos"
killall mongod mongos

echo ">>> Remove db files and logs"
rm -rf data
rm -rf log

# Create the common log directory
mkdir log

echo ">>> Start replica set for shard US-East"
mkdir -p data/shard-US-East/rsMemberEast data/shard-US-East/rsMemberWest
mongod --replSet shard-US-East --logpath "log/shard-US-East-rsMemberEast.log" --dbpath data/shard-US-East/rsMemberEast --port 37017 --fork --shardsvr --smallfiles
mongod --replSet shard-US-East --logpath "log/shard-US-East-rsMemberWest.log" --dbpath data/shard-US-East/rsMemberWest --port 37018 --fork --shardsvr --smallfiles

echo ">>> Sleep 15s to allow US-East replica set to start"
sleep 15

# The US-East replica set member is assigned priority 2 so that it becomes primary
echo ">>> Configure replica set for shard US-East"
mongo --port 37017 << 'EOF'
config = { _id: "shard-US-East", members:[
         { _id : 0, host : "localhost:37017", priority: 2 },
         { _id : 1, host : "localhost:37018" }]};
rs.initiate(config)
EOF

echo ">>> Start replica set for shard-US-West"
mkdir -p data/shard-US-West/rsMemberEast data/shard-US-West/rsMemberWest
mongod --replSet shard-US-West --logpath "log/shard-US-West-rsMemberEast.log" --dbpath data/shard-US-West/rsMemberEast --port 47017 --fork --shardsvr --smallfiles
mongod --replSet shard-US-West --logpath "log/shard-US-West-rsMemberWest.log" --dbpath data/shard-US-West/rsMemberWest --port 47018 --fork --shardsvr --smallfiles

echo ">>> Sleep 15s to allow US-West replica set to start"
sleep 15

# The US-West replica set member is assigned priority 2 so that it becomes primary
echo ">>> Configure replica set for shard-US-West"
mongo --port 47017 << 'EOF'
config = { _id: "shard-US-West", members:[
         { _id : 0, host : "localhost:47017" },
         { _id : 1, host : "localhost:47018", priority: 2 }]};
rs.initiate(config)
EOF

# Shard config servers: should be 3 and all must be up to deploy a shard cluster
# These are the mongos backing store for routing information
echo ">>> Start config servers"
mkdir -p data/config/config-us-east data/config/config-us-west data/config/config-redundant
mongod --logpath "log/cfg-us-east.log"   --dbpath data/config/config-us-east   --port 57040 --fork --configsvr --smallfiles
mongod --logpath "log/cfg-us-west.log"   --dbpath data/config/config-us-west   --port 57041 --fork --configsvr --smallfiles
mongod --logpath "log/cfg-redundant.log" --dbpath data/config/config-redundant --port 57042 --fork --configsvr --smallfiles

echo ">>> Sleep 5 to allow config servers to start and stabilize"
sleep 5

# All mongos's must point at the same config server, a coordinator dispatches writes to each
echo ">>> Start mongos"
mongos --logpath "log/mongos-us-east.log" --configdb localhost:57040,localhost:57041,localhost:57042 --port 27017 --fork
mongos --logpath "log/mongos-us-west.log" --configdb localhost:57040,localhost:57041,localhost:57042 --port 27018 --fork

echo ">>> Wait 60 seconds for the replica sets to stabilize"
sleep 60

# Enable sharding on the 'sales' database and 'sales.users' collection
# Every collection in 'sales' must be sharded or the writes will go to shard 0
# Add a shard tag so we can associate shard keys with the tag (region)
# Shard tag range main and max cannot be the same so we use a region id for US-East = 1
# and US-West = 2. sh.addTagRange() is inclusive of minKey and exclusive of maxKey.
# We only need to configure one mongos - config will be propogated to all mongos through
# the config server
echo ">>> Add shards to mongos"
mongo --port 27017 <<'EOF'
db.adminCommand( { addshard : "shard-US-East/"+"localhost:37017" } );
db.adminCommand( { addshard : "shard-US-West/"+"localhost:47017" } );

db.adminCommand({enableSharding: "sales"})
db.adminCommand({shardCollection: "sales.users", key: {region:1}});

sh.addShardTag("shard-US-East", "US-East")
sh.addShardTag("shard-US-West", "US-West")
sh.addTagRange("sales.users", { region: 1 }, { region: 2 }, "US-East")
sh.addTagRange("sales.users", { region: 2 }, { region: 3 }, "US-West")
EOF
