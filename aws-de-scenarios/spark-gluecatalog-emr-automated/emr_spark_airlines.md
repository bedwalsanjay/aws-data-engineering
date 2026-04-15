# Spark on EMR + Glue Data Catalog + S3 — Airlines Analytics

## Usecase

Raw flights CSV lands in S3.
We register it as a **Glue external table** (manual DDL via Athena).
An **S3 event triggers Lambda**, which launches a **transient EMR cluster**.
The Spark job reads the Glue Catalog table, computes analytics, and writes CSV results back to S3.
The EMR cluster auto-terminates after the job completes.

```
Local machine
  └── generate_airlines_data.py
          └── S3: raw/airlines/flights.csv
                  └── S3 Event → Lambda
                          └── Transient EMR Cluster (Spark)
                                  └── Reads Glue Catalog → Aggregations → S3: curated/airlines/
```

**Outputs written:**
- `curated/airlines/delay_by_airline/`
- `curated/airlines/top_routes/`
- `curated/airlines/daily_trends/`

---

## Prerequisites

- S3 bucket: `sanjay-de-bucket-2026`
- Region: `ap-south-1`
- IAM roles:
  - `EMR_DefaultRole` — EMR service role
  - `EMR_EC2_DefaultRole` — EC2 instance profile for EMR nodes
  - `LambdaEMRRole` — Lambda execution role
- AWS CLI configured locally (for uploading script to S3)

---

## Step 1 — Upload Sample Data to S3

```bash
pip3 install boto3
python3 scripts/generate_airlines_data.py
```

Verify in S3 console:
```
s3://sanjay-de-bucket-2026/raw/airlines/flights.csv   ← should exist
```

---

## Step 2 — Create Glue Database + External Table (Athena Console)

### 2a. Open Athena Console
```
AWS Console → Athena → Query Editor
Set query result location: s3://sanjay-de-bucket-2026/athena-results/
```

### 2b. Create Glue Database
```sql
CREATE DATABASE IF NOT EXISTS airlines_db;
```

### 2c. Create External Table
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS airlines_db.flights (
  flight_id            STRING,
  flight_date          STRING,
  airline              STRING,
  origin               STRING,
  destination          STRING,
  departure_delay_mins INT,
  arrival_delay_mins   INT,
  distance_km          INT,
  status               STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://sanjay-de-bucket-2026/raw/airlines/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

### 2d. Verify
```sql
SELECT * FROM airlines_db.flights LIMIT 5;
```

---

## Step 3 — Upload Spark Script to S3

EMR needs the script in S3 to run it as a step.

```bash
aws s3 cp scripts/airlines_analytics.py s3://sanjay-de-bucket-2026/emr-scripts/airlines_analytics.py
```

---

## Step 4 — Create IAM Roles

### 4a. EMR Roles (if not already created)

The quickest way — AWS CLI creates both default EMR roles in one command:
```bash
aws emr create-default-roles
```
This creates `EMR_DefaultRole` and `EMR_EC2_DefaultRole`.

### 4b. Lambda Execution Role

1. Go to **IAM → Roles → Create Role**
2. Trusted entity: **AWS Service → Lambda**
3. Attach policies:
   - `AmazonEMRFullAccessPolicy_v2`
   - `AmazonS3ReadOnlyAccess`
   - `AWSLambdaBasicExecutionRole`
4. Name it: `LambdaEMRRole`

---

## Step 5 — Create Lambda Function

1. Go to **AWS Lambda → Create Function**
2. Configure:

| Setting | Value |
|---|---|
| Function name | `airlines-emr-trigger` |
| Runtime | `Python 3.12` |
| Execution role | `LambdaEMRRole` |

3. Paste contents of `scripts/lambda_trigger.py` into the code editor
4. Set **Environment Variables**:

| Key | Value |
|---|---|
| `BUCKET` | `sanjay-de-bucket-2026` |
| `SPARK_SCRIPT` | `s3://sanjay-de-bucket-2026/emr-scripts/airlines_analytics.py` |
| `EMR_ROLE` | `EMR_DefaultRole` |
| `EMR_EC2_ROLE` | `EMR_EC2_DefaultRole` |
| `SUBNET_ID` | your subnet ID (from VPC console) |

5. Set **Timeout** to `1 min` (Lambda just launches EMR, doesn't wait for it)

---

## Step 6 — Add S3 Trigger to Lambda

1. In Lambda → **Add Trigger** → **S3**
2. Configure:

| Setting | Value |
|---|---|
| Bucket | `sanjay-de-bucket-2026` |
| Event type | `PUT` |
| Prefix | `raw/airlines/` |
| Suffix | `.csv` |

3. Click **Add**

---

## Step 7 — Test the Pipeline End to End

Re-upload the flights CSV to trigger the Lambda:
```bash
python3 scripts/generate_airlines_data.py
```

**Monitor Lambda:**
```
AWS Lambda → airlines-emr-trigger → Monitor → CloudWatch Logs
```
You should see: `EMR cluster launched: j-XXXXXXXXXXXX`

**Monitor EMR:**
```
AWS EMR → Clusters → airlines-analytics-transient
```
Status: `STARTING → BOOTSTRAPPING → RUNNING → TERMINATING → TERMINATED`

Click the cluster → **Steps** tab → **airlines-analytics** → **View logs** to see Spark output including printed summaries.

---

## Step 8 — Verify Output in S3

```
s3://sanjay-de-bucket-2026/curated/airlines/
    ├── delay_by_airline/   ← CSV files
    ├── top_routes/         ← CSV files
    └── daily_trends/       ← CSV files
```

---

## Step 9 — Query Results via Athena (optional)

```sql
CREATE EXTERNAL TABLE airlines_db.delay_by_airline (
  airline            STRING,
  avg_dep_delay_mins DOUBLE,
  avg_arr_delay_mins DOUBLE,
  total_flights      BIGINT,
  delay_pct          DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://sanjay-de-bucket-2026/curated/airlines/delay_by_airline/'
TBLPROPERTIES ('skip.header.line.count'='1');

SELECT * FROM airlines_db.delay_by_airline ORDER BY avg_dep_delay_mins DESC;
```

---

## Architecture Summary

```
Local machine
  └── generate_airlines_data.py → S3: raw/airlines/flights.csv

Athena Console (DDL only)
  └── CREATE EXTERNAL TABLE airlines_db.flights → Glue Data Catalog

S3 PUT event (raw/airlines/*.csv)
  └── Lambda: airlines-emr-trigger
          └── boto3 EMR run_job_flow()
                  └── Transient EMR cluster (emr-6.15.0, Spark + Hadoop)
                          └── spark-submit airlines_analytics.py
                                  ├── Reads Glue Catalog via Hive Metastore
                                  ├── Computes 3 aggregations
                                  └── Writes CSV → S3: curated/airlines/
                  └── Cluster auto-terminates
```

---

## Key Concepts

| Concept | Explanation |
|---|---|
| Transient EMR cluster | `KeepJobFlowAliveWhenNoSteps=False` — cluster terminates as soon as steps finish, minimising cost |
| Glue as Hive Metastore | EMR has `AWSGlueDataCatalogHiveClientFactory` built-in — no extra JARs needed unlike plain EC2 |
| Lambda as trigger | Decouples ingestion from processing — any new file in S3 automatically kicks off the pipeline |
| S3 event notification | Native S3 feature — zero polling, event-driven |
| `spark-hive-site` config | EMR classification that sets Glue as the Hive metastore at cluster level |
| `ActionOnFailure` | `TERMINATE_CLUSTER` — avoids idle cluster costs if the Spark job fails |

---

## Common Issues

| Issue | Fix |
|---|---|
| Lambda not triggering | Check S3 event notification is saved and prefix/suffix match exactly |
| `EMR_DefaultRole not found` | Run `aws emr create-default-roles` |
| `Access Denied on S3` | Verify `EMR_EC2_DefaultRole` instance profile has S3 access |
| `Table not found: airlines_db.flights` | Check Glue console → Databases → airlines_db → tables |
| Cluster terminates immediately | Check EMR Steps tab → logs for Spark errors |
| Lambda timeout | Lambda timeout only needs to cover the `run_job_flow()` API call (~5s), not the EMR job itself |

---

## Files in This Project

```
spark-gluecatalog-emr/
├── emr_spark_airlines.md               ← this guide
└── scripts/
    ├── generate_airlines_data.py       ← generates + uploads flights CSV to S3
    ├── airlines_analytics.py           ← PySpark job (runs on EMR)
    └── lambda_trigger.py               ← Lambda function (S3 trigger → EMR)
```

---

*Region: ap-south-1 | EMR: 6.15.0 (Spark 3.4) | Glue Catalog: external table via Athena DDL | Trigger: S3 → Lambda → EMR*
