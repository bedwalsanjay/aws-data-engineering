# Spark on EMR + Glue Data Catalog + S3 — Airlines Analytics (Manual)

## Usecase

Raw flights CSV lands in S3.
We register it as a **Glue external table** (manual DDL via Athena).
We **manually create a transient EMR cluster** via the AWS Console, add the Spark job as a step, and the cluster auto-terminates after the job completes.

> This is the manual version of the pipeline. For the automated version (S3 → Lambda → EMR), see `spark-gluecatalog-emr-automated`.

```
Local machine
  └── generate_airlines_data.py
          └── S3: raw/airlines/flights.csv

Athena Console
  └── CREATE EXTERNAL TABLE airlines_db.flights → Glue Data Catalog

AWS Console → EMR (manual)
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

## Step 4 — Create IAM Roles (if not already done)

```bash
aws emr create-default-roles
```

This creates `EMR_DefaultRole` and `EMR_EC2_DefaultRole` in one shot.

---

## Step 5 — Create Transient EMR Cluster (AWS Console)

1. Go to **AWS EMR → Clusters → Create Cluster**
2. Configure:

| Setting | Value |
|---|---|
| Cluster name | `airlines-analytics-manual` |
| EMR release | `emr-6.15.0` |
| Applications | `Spark`, `Hadoop` |
| Instance type (Primary) | `m5.xlarge` |
| Instance type (Core) | `m5.xlarge` |
| Core instance count | `2` |
| Cluster termination | **Terminate cluster after last step** ✅ |
| Service role | `EMR_DefaultRole` |
| EC2 instance profile | `EMR_EC2_DefaultRole` |
| EC2 subnet | pick any subnet in your VPC |
| Logging | `s3://sanjay-de-bucket-2026/emr-logs/` |

> **Terminate cluster after last step** is the key setting that makes it transient.

---

## Step 6 — Add Spark Step

Still on the Create Cluster page, scroll to **Steps** → **Add Step**:

| Setting | Value |
|---|---|
| Step type | `Spark application` |
| Name | `airlines-analytics` |
| Deploy mode | `Cluster` |
| Application location | `s3://sanjay-de-bucket-2026/emr-scripts/airlines_analytics.py` |
| Action on failure | `Terminate cluster` |

**Spark submit options** (paste into the Spark submit options field):
```
--conf spark.sql.catalogImplementation=hive --conf hive.metastore.client.factory.class=com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory
```

Click **Create Cluster** — the cluster will start, run the step, and terminate automatically.

---

## Step 7 — Monitor the Cluster

```
AWS EMR → Clusters → airlines-analytics-manual
```

Status progression:
```
STARTING → BOOTSTRAPPING → RUNNING → TERMINATING → TERMINATED
```

To see Spark logs:
```
EMR → Clusters → airlines-analytics-manual → Steps tab → airlines-analytics → View logs → stdout
```

You should see the printed summaries:
```
=== Delay Stats by Airline ===
=== Top 10 Busiest Routes ===
=== Daily Flight Trends (first 10 days) ===
```

---

## Step 8 — Verify Output in S3

```
s3://sanjay-de-bucket-2026/curated/airlines/
    ├── delay_by_airline/   ← CSV files
    ├── top_routes/         ← CSV files
    └── daily_trends/       ← CSV files
```

Download any `part-*.csv` file directly from S3 console to inspect the output.

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

AWS Console → EMR (manual)
  └── Transient EMR cluster (emr-6.15.0, Spark + Hadoop)
          └── spark-submit airlines_analytics.py
                  ├── Reads Glue Catalog via Hive Metastore (built-in on EMR)
                  ├── Computes 3 aggregations
                  └── Writes CSV → S3: curated/airlines/
          └── Cluster auto-terminates
```

---

## Key Concepts

| Concept | Explanation |
|---|---|
| Transient EMR cluster | Terminate after last step — pay only for job duration, no idle cost |
| Glue as Hive Metastore | EMR has `AWSGlueDataCatalogHiveClientFactory` built-in — no extra JARs needed |
| `spark-submit` on EMR | Uses `command-runner.jar` internally — `Spark application` step type handles this via console |
| Cluster vs Client deploy mode | `Cluster` mode — driver runs on EMR, not on the submitting machine |
| EMR logs in S3 | Set log URI at cluster creation — stdout/stderr of each step available in S3 after termination |

---

## Common Issues

| Issue | Fix |
|---|---|
| `EMR_DefaultRole not found` | Run `aws emr create-default-roles` |
| `Access Denied on S3` | Verify `EMR_EC2_DefaultRole` instance profile has S3 access to your bucket |
| `Table not found: airlines_db.flights` | Check Glue console → Databases → airlines_db → tables |
| Cluster terminates immediately | Check Steps tab → View logs → stderr for Spark errors |
| No output in S3 | Check stdout logs — look for Python exceptions after the `show()` prints |
| Step stays in PENDING | Cluster may still be bootstrapping — wait for RUNNING status |

---

## Files in This Project

```
spark-gluecatalog-emr-manual/
├── emr_spark_airlines_manual.md        ← this guide
└── scripts/
    ├── generate_airlines_data.py       ← generates + uploads flights CSV to S3
    └── airlines_analytics.py           ← PySpark job (runs on EMR)
```

---

## Next Step

Once comfortable with the manual flow, see `spark-gluecatalog-emr-automated` where Lambda automatically triggers the EMR cluster when a new file lands in S3.

---

*Region: ap-south-1 | EMR: 6.15.0 (Spark 3.4) | Glue Catalog: external table via Athena DDL | Cluster: transient, manually created*
