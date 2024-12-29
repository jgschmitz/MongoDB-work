#!/bin/sh

# Check if required arguments are supplied
if [ $# -lt 3 ]; then
  echo "Usage: $0 CONNECTION_STRING USERNAME PASSWORD"
  exit 1
fi

CONNECTION_STRING=$1
USERNAME=$2
PASSWORD=$3

mongo "$CONNECTION_STRING" --username "$USERNAME" --password "$PASSWORD" --eval '
function getRandomElement(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function runQuery(dbName, collectionName, query, sort, isAggregation = false, pipeline = []) {
  db = db.getSiblingDB(dbName);
  let result;
  if (isAggregation) {
    result = db[collectionName].aggregate(pipeline, { allowDiskUse: true });
  } else {
    result = db[collectionName].find(query).sort(sort);
  }
  print(`Performed query on ${collectionName}: found ${result.itcount()} docs`);
}

while (true) {
  const pickRandomQuery = Math.floor(Math.random() * 4);
  print("Running a slow query...");

  switch (pickRandomQuery) {
    case 0:
      // Airbnb query
      runQuery(
        "sample_airbnb",
        "listingsAndReviews",
        { description: { $regex: `.*${getRandomElement(["home", "new", "charming", "cosy"])}.*`, $options: "i" }},
        { description: 1 }
      );
      break;

    case 1:
      // Grades query
      runQuery(
        "sample_training",
        "grades",
        { "scores.type": getRandomElement(["exam", "quiz", "homework"]) },
        { student_id: 1, class_id: 1 }
      );
      break;

    case 2:
      // Mflix query
      runQuery(
        "sample_mflix",
        "movies",
        { [getRandomElement(["plot", "title", "fullplot"])]: { $regex: `.*${getRandomElement(["hero", "drama", "disaster", "horror"])}.*`, $options: "i" }},
        { title: 1 }
      );
      break;

    case 3:
      // Weather data query
      runQuery(
        "sample_weatherdata",
        "data",
        {},
        {},
        true,
        [
          { $match: getRandomElement([{ type: "FM-13" }, { callLetters: { $ne: "SHIP" }}]) },
          { $sort: getRandomElement([{ callLetters: 1 }, { callLetters: 1, qualityControlProcess: 1 }, { callLetters: 1, qualityControlProcess: 1, elevation: -1 }]) }
        ]
      );
      break;

    default:
      print("Invalid query selection.");
      break;
  }
}
'
