import argparse
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from pymongo import MongoClient, UpdateOne


def getvalue(old_value):
    # Equivalent distribution: a change between -0.1% and +0.1%.
    return round(old_value * (1 + random.uniform(-0.001, 0.001)), 2)


def worker(collection, gateway, sensor_count, samples_per_document,
           start_time, duration_seconds, batch_size):
    last_value = round(random.uniform(32, 75), 2)
    operations = []
    written = 0

    sensor_ids = range(
        gateway * 1000 + sensor_count,
        gateway * 1000,
        -1,
    )

    for offset in range(duration_seconds):
        timestamp = start_time + timedelta(seconds=offset)
        day = timestamp.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        for sensor_id in sensor_ids:
            last_value = getvalue(last_value)

            operations.append(
                UpdateOne(
                    {
                        "deviceid": gateway,
                        "sensorid": sensor_id,
                        "day": day,
                        "nsamples": {"$lt": samples_per_document},
                    },
                    {
                        "$push": {
                            "samples": {
                                "val": last_value,
                                "time": timestamp,
                            }
                        },
                        "$min": {"first": timestamp},
                        "$max": {"last": timestamp},
                        "$inc": {"nsamples": 1},
                    },
                    upsert=True,
                )
            )

            if len(operations) >= batch_size:
                collection.bulk_write(operations, ordered=True)
                written += len(operations)
                operations.clear()

    if operations:
        collection.bulk_write(operations, ordered=True)
        written += len(operations)

    return written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", type=int, required=True,
                        help="sensors per gateway")
    parser.add_argument("-g", type=int, required=True,
                        help="number of gateways")
    parser.add_argument("-n", type=int, default=200,
                        help="maximum samples per document")
    parser.add_argument("-m", type=int, required=True,
                        help="minutes of data")
    parser.add_argument("--uri", default="mongodb://localhost:27017")
    parser.add_argument("--database", default="IoTData")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--drop", action="store_true",
                        help="delete existing SensorData before generating")
    args = parser.parse_args()

    if not 1 <= args.s <= 999:
        parser.error("-s must be between 1 and 999")

    if min(args.g, args.n, args.m, args.workers, args.batch_size) < 1:
        parser.error("all numeric arguments must be positive")

    # Use one time interval for every gateway.
    end_time = datetime.now().replace(second=0, microsecond=0)
    start_time = end_time - timedelta(minutes=args.m)

    with MongoClient(args.uri) as client:
        collection = client[args.database]["SensorData"]

        if args.drop:
            collection.drop()

        # Deliberately non-unique: multiple buckets may exist for
        # the same gateway, sensor, and day.
        collection.create_index([
            ("deviceid", 1),
            ("sensorid", 1),
            ("day", 1),
            ("nsamples", 1),
        ])

        with ThreadPoolExecutor(
            max_workers=min(args.workers, args.g)
        ) as executor:
            futures = [
                executor.submit(
                    worker,
                    collection,
                    gateway,
                    args.s,
                    args.n,
                    start_time,
                    args.m * 60,
                    args.batch_size,
                )
                for gateway in range(1, args.g + 1)
            ]

            # Calling result() also propagates worker exceptions.
            total = sum(future.result() for future in futures)

    print(f"Wrote {total:,} samples")


if __name__ == "__main__":
    main()
