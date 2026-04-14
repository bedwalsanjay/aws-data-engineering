# Spark + Glue Data Catalog + S3 — E-Commerce Order Analytics

## Usecase

Raw orders CSV lives in S3.
We register it as a **Glue external table** (no crawler, manual DDL via Athena).
A **Glue ETL job** reads the table via Glue Data Catalog natively, computes analytics, and writes CSV results back to S3.

```
S3 (raw CSV)
    └── Glue External Table (DDL via Athena console)
            └── Glue ETL Job reads via Glue Data Catalog
                    └── Aggregations → S3 (curated CSV)
```

**Outputs written:**
- `curated/order_analytics/revenue_by_category/`
- `curated/order_analytics/top_products/`
- `curated/order_analytics/daily_trends/`

---

## Prerequisites

- IAM Role with:
  - `AmazonS3FullAccess`
  - `AmazonAthenaFullAccess`
  - `AWSGlueConsoleFullAccess`
- S3 bucket already created: `<your-s3-bucket>`
- Region: `ap-south-1`

---

## Step 1 — Upload Sample Data to S3

Run from your **local Windows machine**:

```bash
pip3 install boto3
python3 upload_sample_data.py
```

After running, verify in S3 console:
```
s3://<your-s3-bucket>/raw/orders/orders.csv   ← should exist
```

---

## Step 2 — Create Glue Database + External Table (Athena Console)

### 2a. Open Athena Console
```
AWS Console → Athena → Query Editor
Set query result location: s3://<your-s3-bucket>/athena-results/
```

### 2b. Create Glue Database
```sql
CREATE DATABASE IF NOT EXISTS ecommerce_db;
```

### 2c. Create External Table pointing to S3 CSV
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS ecommerce_db.orders (
  order_id     STRING,
  order_date   STRING,
  customer_id  STRING,
  product_id   STRING,
  product_name STRING,
  category     STRING,
  quantity     INT,
  unit_price   DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://<your-s3-bucket>/raw/orders/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

### 2d. Verify
```sql
SELECT * FROM ecommerce_db.orders LIMIT 5;
```

---

## Step 3 — Upload Glue Script to S3

Glue ETL jobs require the script to be in S3.

```bash
aws s3 cp order_analytics.py s3://<your-s3-bucket>/glue-scripts/order_analytics.py
```

---

## Step 4 — Create IAM Role for Glue

1. Go to **IAM → Roles → Create Role**
2. Trusted entity: **AWS Service → Glue**
3. Attach policies:
   - `AmazonS3FullAccess`
   - `AWSGlueConsoleFullAccess`
   - `AmazonAthenaFullAccess`
4. Name it: `GlueETLRole`

---

## Step 5 — Create and Run the Glue ETL Job

### 5a. Create the Job

1. Go to **AWS Glue → ETL Jobs → Create Job**
2. Select **Script editor** → **Upload script** → upload `order_analytics.py`
   - Or choose **Spark script** and paste the script contents
3. Configure:

| Setting | Value |
|---|---|
| Name | `order-analytics-etl` |
| IAM Role | `GlueETLRole` |
| Glue version | `Glue 5.0 (Spark 3.5, Python 3)` |
| Worker type | `G.1X` |
| Number of workers | `2` |
| Script path | `s3://<your-s3-bucket>/glue-scripts/order_analytics.py` |
| Temporary path | `s3://<your-s3-bucket>/glue-temp/` |

4. Click **Save** then **Run**

### 5b. Monitor the Job

```
AWS Glue → ETL Jobs → order-analytics-job → Runs tab
```

Status goes: `STARTING → RUNNING → SUCCEEDED` (~2-3 min)

Click **Logs** to see CloudWatch output including the printed summaries and `Done. Results written to:`.

---

## Step 6 — Verify Output in S3

After the job succeeds, check S3:

```
s3://<your-s3-bucket>/curated/order_analytics/
    ├── revenue_by_category/   ← CSV files
    ├── top_products/          ← CSV files
    └── daily_trends/          ← CSV files
```

Download any part file directly from S3 console to view the output.

---

## Step 7 — Query Results via Athena (optional)

```sql
CREATE EXTERNAL TABLE ecommerce_db.revenue_by_category (
  category      STRING,
  total_revenue DOUBLE,
  total_orders  BIGINT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://<your-s3-bucket>/curated/order_analytics/revenue_by_category/'
TBLPROPERTIES ('skip.header.line.count'='1');

SELECT * FROM ecommerce_db.revenue_by_category ORDER BY total_revenue DESC;
```

---

## Architecture Summary

```
Local/EC2
  └── upload_sample_data.py
          └── S3: raw/orders/orders.csv

Athena Console (DDL only, no crawler)
  └── CREATE EXTERNAL TABLE ecommerce_db.orders → Glue Data Catalog

AWS Glue ETL Job (order_analytics.py)
  └── Reads Glue table via GlueContext.create_dynamic_frame.from_catalog()
          ├── Computes 3 aggregations
          └── Writes CSV → S3: curated/order_analytics/

Athena (optional)
  └── Query curated Parquet via new external tables
```

---

## Key Concepts

| Concept | Explanation |
|---|---|
| Glue External Table | Table metadata in Glue Catalog, actual data stays in S3 — no data movement |
| No Crawler | We write DDL manually in Athena — saves cost, gives full control over schema |
| GlueContext | Glue's wrapper around SparkContext — has native Glue Catalog access, no extra JARs needed |
| DynamicFrame | Glue's DataFrame equivalent — `from_catalog()` reads directly from Glue metastore |
| S3A filesystem | Glue handles S3 access internally via its own runtime |
| IAM Role auth | Glue job uses the attached IAM role — no hardcoded keys |
| CSV output | Human-readable, easy to inspect directly from S3 — switch to Parquet for production |

---

## Common Issues

| Issue | Fix |
|---|---|
| `Table not found: ecommerce_db.orders` | Check Glue console → Databases → ecommerce_db → tables list |
| `Access Denied on S3` | Verify `GlueETLRole` has S3FullAccess and covers your bucket |
| `Access Denied on Glue` | Verify `GlueETLRole` has AWSGlueConsoleFullAccess |
| Job stuck in STARTING | Check IAM role trust policy — must trust `glue.amazonaws.com` |
| Script not found | Verify script S3 path matches what's set in the job config |
| No output in S3 | Check CloudWatch logs via Glue → Runs → Logs for Python errors |

---

## Files in This Project

```
spark+athena+s3/
├── spark_glue_s3.md              ← this guide
└── scripts/
    ├── upload_sample_data.py     ← generates + uploads CSV to S3
    └── order_analytics.py        ← Glue ETL job script (reads Glue catalog, writes CSV)
```

---

*Region: ap-south-1 | Glue 5.0 (Spark 3.5) | Job: order-analytics-etl | Glue Catalog: external table via Athena DDL*
