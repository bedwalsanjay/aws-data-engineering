"""
Generates sample airlines CSV and uploads to S3.
Run this locally before the pipeline starts.
"""

import boto3
import csv
import io
import random
from datetime import date, timedelta

BUCKET = "sanjay-de-bucket-2026"
S3_KEY = "raw/airlines/flights.csv"
REGION = "ap-south-1"

airlines = ["IndiGo", "Air India", "SpiceJet", "Vistara", "GoAir"]
airports = ["DEL", "BOM", "BLR", "HYD", "MAA", "CCU", "AMD", "PNQ"]
statuses = ["On Time", "Delayed", "Cancelled"]
status_weights = [0.6, 0.3, 0.1]

rows = []
start = date(2024, 1, 1)
for i in range(1, 5001):
    origin, destination = random.sample(airports, 2)
    flight_date = start + timedelta(days=random.randint(0, 364))
    status = random.choices(statuses, weights=status_weights)[0]
    dep_delay = random.randint(0, 180) if status == "Delayed" else 0
    arr_delay = dep_delay + random.randint(-5, 20) if status == "Delayed" else 0
    rows.append({
        "flight_id":             f"FL{i:05d}",
        "flight_date":           flight_date.isoformat(),
        "airline":               random.choice(airlines),
        "origin":                origin,
        "destination":           destination,
        "departure_delay_mins":  dep_delay,
        "arrival_delay_mins":    max(arr_delay, 0),
        "distance_km":           random.randint(300, 3000),
        "status":                status,
    })

buf = io.StringIO()
writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
writer.writeheader()
writer.writerows(rows)

s3 = boto3.client("s3", region_name=REGION)
s3.put_object(Bucket=BUCKET, Key=S3_KEY, Body=buf.getvalue())
print(f"Uploaded {len(rows)} rows to s3://{BUCKET}/{S3_KEY}")
