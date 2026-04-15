"""
Generates sample orders CSV and uploads to S3.
Run this locally (Windows) or on EC2 before starting the Spark job.
"""

import boto3
import csv
import io
import random
from datetime import date, timedelta

BUCKET = "sanjay-de-bucket-2026"
S3_KEY = "raw/orders/orders.csv"
REGION = "ap-south-1"

categories = ["Electronics", "Clothing", "Books", "Home", "Sports"]
products = {
    "Electronics": [("P001", "Laptop"), ("P002", "Phone"), ("P003", "Tablet")],
    "Clothing":    [("P004", "T-Shirt"), ("P005", "Jeans"), ("P006", "Jacket")],
    "Books":       [("P007", "Python Book"), ("P008", "SQL Book"), ("P009", "ML Book")],
    "Home":        [("P010", "Lamp"), ("P011", "Chair"), ("P012", "Table")],
    "Sports":      [("P013", "Shoes"), ("P014", "Bag"), ("P015", "Bottle")],
}
prices = {"P001":800,"P002":500,"P003":350,"P004":20,"P005":40,"P006":80,
          "P007":30,"P008":25,"P009":45,"P010":15,"P011":120,"P012":200,
          "P013":60,"P014":35,"P015":10}

rows = []
start = date(2024, 1, 1)
for i in range(1, 5001):
    cat = random.choice(categories)
    pid, pname = random.choice(products[cat])
    order_date = start + timedelta(days=random.randint(0, 364))
    rows.append({
        "order_id": f"ORD{i:05d}",
        "order_date": order_date.isoformat(),
        "customer_id": f"CUST{random.randint(1,500):04d}",
        "product_id": pid,
        "product_name": pname,
        "category": cat,
        "quantity": random.randint(1, 5),
        "unit_price": prices[pid],
    })

buf = io.StringIO()
writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
writer.writeheader()
writer.writerows(rows)

s3 = boto3.client("s3", region_name=REGION)
s3.put_object(Bucket=BUCKET, Key=S3_KEY, Body=buf.getvalue())
print(f"Uploaded {len(rows)} rows to s3://{BUCKET}/{S3_KEY}")
