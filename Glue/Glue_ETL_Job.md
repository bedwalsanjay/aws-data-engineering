# AWS Glue - Spark ETL Job

---

## Table of Contents

1. [What is a Glue Spark ETL Job](#1-what-is-a-glue-spark-etl-job)
2. [ETL Job Parameters - What is Different from Python Shell](#2-etl-job-parameters---what-is-different-from-python-shell)
3. [What is a DPU](#3-what-is-a-dpu)
4. [Glue Version](#4-glue-version)
5. [Worker Type](#5-worker-type)
6. [Number of Workers](#6-number-of-workers)
7. [Spark UI](#7-spark-ui)
8. [Job Bookmark](#8-job-bookmark)
9. [Other Important Parameters](#9-other-important-parameters)
10. [Sample Glue ETL Job](#10-sample-glue-etl-job)
11. [DynamicFrame vs Spark DataFrame](#11-dynamicframe-vs-spark-dataframe)
12. [Running and Monitoring the ETL Job](#12-running-and-monitoring-the-etl-job)

---

## 1. What is a Glue Spark ETL Job

A Glue Spark ETL Job runs your Python or Scala code on a managed **Apache Spark** cluster. Unlike Python Shell which runs on a single machine, Spark ETL distributes the work across multiple nodes making it suitable for large scale data processing.

```
Python Shell Job:
Single machine → processes data sequentially → good for MBs

Spark ETL Job:
Driver node + multiple worker nodes
→ data split across workers
→ processed in parallel
→ good for GBs to TBs
```

**When to use Spark ETL over Python Shell:**
- Data size is GBs or TBs
- Complex transformations - joins across large datasets
- Aggregations on millions of rows
- Converting large files from CSV/JSON to Parquet
- Reading from and writing to multiple sources simultaneously

---

## 2. ETL Job Parameters - What is Different from Python Shell

These parameters exist in Spark ETL jobs but are **not available in Python Shell jobs:**

| Parameter | Python Shell | Spark ETL | Description |
|---|---|---|---|
| Glue Version | ❌ | ✅ | Spark and Python version bundled together |
| Worker Type | ❌ | ✅ | Size of each worker node |
| Number of Workers | ❌ | ✅ | How many worker nodes in the cluster |
| Spark UI | ❌ | ✅ | Visual Spark execution monitoring |
| Job Bookmark | ❌ | ✅ | Track processed data for incremental loads |
| Scala support | ❌ | ✅ | Can write jobs in Scala |
| Streaming mode | ❌ | ✅ | Continuous streaming ETL |

---

## 3. What is a DPU

DPU stands for **Data Processing Unit**. It is the unit of compute capacity that AWS Glue uses to measure and bill for job execution.

**1 DPU = 4 vCPUs + 16 GB of memory**

```
1 DPU
├── 4 vCPUs  (processing power)
└── 16 GB RAM (memory for data)
```

Think of DPU as a standardized measure of compute power. Instead of talking about individual CPUs and RAM separately, Glue bundles them together into one unit called DPU.

---

**In Spark terminology:**

When a Glue job runs, Spark has two types of processes:

```
Driver Process   → runs on 1 node → manages the job
Executor Process → runs on worker nodes → actually processes data
```

**How 1 DPU (4 vCPU + 16 GB) maps to Spark:**

Each worker node in Glue runs **one Spark executor**. The resources available to that executor depend on the worker type selected. For example with G.1X that executor gets:

```
1 Spark Executor
├── 4 vCPUs  → becomes Spark cores
│              each core runs one Spark task at a time
│              4 cores = 4 tasks running in parallel on this node
│
└── 16 GB RAM → executor memory available for data processing
```

**Practical example - Number of Workers = 5, G.1X:**

```
Total cluster:

Driver node (1 DPU):
└── manages job, does not process data

Worker node 1 (1 DPU) → 1 Executor → 4 cores → 4 parallel tasks
Worker node 2 (1 DPU) → 1 Executor → 4 cores → 4 parallel tasks
Worker node 3 (1 DPU) → 1 Executor → 4 cores → 4 parallel tasks
Worker node 4 (1 DPU) → 1 Executor → 4 cores → 4 parallel tasks

Total:
→ 4 executors
→ 16 Spark cores (tasks running in parallel)
→ 64 GB total executor memory
```

**What a Spark task is:**

When Spark reads your data it splits it into **partitions**. Each partition is processed by one task on one core.

```
orders.csv (1 GB file)
        ↓
Spark splits into partitions (e.g. 8 partitions)
        ↓
16 cores available across 4 executors
        ↓
8 tasks run in parallel (one per partition)
        ↓
All 8 partitions processed simultaneously
```

**Why more vCPUs = more parallelism:**

```
Number of Workers = 5 (1 driver + 4 executors)

G.1X (4 vCPU per worker) × 4 executor workers = 16 parallel tasks
G.2X (8 vCPU per worker) × 4 executor workers = 32 parallel tasks
                                                   ↑
                                        processes data 2x faster
                                        but costs 2x more
```

| DPU concept | Spark equivalent |
|---|---|
| 1 Worker | 1 Spark executor node |
| Worker Type (G.1X, G.2X etc.) | Size of each executor - CPU and memory |
| Number of Workers | Number of executors + 1 driver node |

---

## 4. Glue Version

Glue Version determines which version of **Apache Spark and Python** are bundled together in the job environment.

| Glue Version | Spark Version | Python Version | Java Version |
|---|---|---|---|
| Glue 3.0 | Spark 3.1 | Python 3.7 | Java 8 |
| Glue 4.0 | Spark 3.3 | Python 3.10 | Java 17 |
| Glue 5.0 | Spark 3.5 | Python 3.11 | Java 17 |

**Always use the latest Glue version (5.0) unless:**
- You have existing jobs written for an older Spark version
- A specific library only supports an older Spark version
- You are migrating from an on-premise Spark cluster with a specific version

**Why Glue version matters:**
- Newer Glue versions have better performance, bug fixes, and new Spark features
- Delta Lake, Iceberg support improved significantly in Glue 4.0+
- Python 3.10+ features only available from Glue 4.0 onwards

---

## 5. Worker Type

Worker Type defines the **size (CPU + memory)** of each individual worker node in the Spark cluster.

**DPU across different worker types:**

| Job Type | DPU per unit |
|---|---|
| Python Shell | 0.0625 DPU (default) or 1 DPU (max) |
| Spark ETL G.1X worker | 1 DPU per worker |
| Spark ETL G.2X worker | 2 DPU per worker |
| Spark ETL G.4X worker | 4 DPU per worker |
| Spark ETL G.8X worker | 8 DPU per worker |

**Why DPU matters for worker type:**
- Each worker type has a fixed DPU value
- More DPU per worker = more CPU and memory per node
- Total DPU = Worker Type DPU × Number of Workers
- Glue pricing is based on total DPU hours consumed

```
Example:
Worker Type       = G.2X  (2 DPU per worker)
Number of Workers = 5
Total DPU         = 2 × 5 = 10 DPU
Cost per hour     = 10 × $0.44 = $4.40/hour
```

| Worker Type | vCPU / Spark Cores | Memory | Disk | DPU | Available For |
|---|---|---|---|---|---|
| G.025X | 2 | 4 GB | 64 GB | 0.25 DPU | Streaming only |
| G.1X | 4 | 16 GB | 64 GB | 1 DPU | ETL, Streaming |
| G.2X | 8 | 32 GB | 128 GB | 2 DPU | ETL, Streaming |
| G.4X | 16 | 64 GB | 256 GB | 4 DPU | ETL only |
| G.8X | 32 | 128 GB | 512 GB | 8 DPU | ETL only |


> Start with **G.1X** for most workloads. Scale up only if you see memory errors or slow performance.

---

## 6. Number of Workers

Number of Workers defines **how many worker nodes** are in the Spark cluster. More workers = more parallelism = faster processing.

```
Number of Workers = 2 (minimum for ETL jobs)

1 node = Driver (manages the job, does not process data)
1 node = Worker (actually processes data)

Number of Workers = 10

1 node  = Driver
9 nodes = Workers (data split across 9 nodes in parallel)
```
---

## 7. Spark UI

Spark UI is a **visual monitoring interface** for your Spark job execution. It shows you exactly what is happening inside your Spark job - which stages ran, how long each took, how data was distributed across workers.

**Why Spark UI is important:**
- Identify slow stages and bottlenecks
- See data skew - when one worker has much more data than others
- Monitor memory usage per executor
- Debug failed tasks
- Understand shuffle operations

**How to enable Spark UI in Glue:**
- Glue Console → your job → **Job details** tab
- Scroll to **Spark UI**
- Enable **Spark UI**
- Set S3 path for Spark UI logs: `s3://your-bucket/spark-ui-logs/`

**Access Spark UI:**
- Glue Console → your job → **Runs** tab
- Click on a completed or running job run
- Click **Spark UI** button
- Opens the Spark UI dashboard in browser

**Key tabs in Spark UI:**

| Tab | What it shows |
|---|---|
| Jobs | All Spark jobs triggered, duration, status |
| Stages | Individual stages within each job, task counts |
| Executors | Memory and CPU usage per worker node |
| SQL | Query execution plans for DataFrame operations |
| Storage | Cached RDDs and DataFrames |

> Always enable Spark UI for production jobs. The S3 storage cost for logs is negligible compared to the debugging value it provides.

---

## 8. Job Bookmark

Job Bookmark tracks which data has already been processed so that on re-runs the job only processes **new data** and skips already processed data.

```
Without Job Bookmark:
Run 1: processes files A, B, C → writes to target
Run 2: processes files A, B, C, D → writes A, B, C again + D
Result: duplicate data in target

With Job Bookmark:
Run 1: processes files A, B, C → bookmark saves state
Run 2: sees bookmark → skips A, B, C → only processes D
Result: no duplicates
```

**Enable Job Bookmark:**
- Glue Console → your job → **Job details**
- Scroll to **Job bookmark**
- Set to **Enable**

**Job Bookmark states:**

| State | Behavior |
|---|---|
| Enable | Track processed data, skip on re-run |
| Disable | Process all data every run |
| Pause | Temporarily stop tracking without resetting |

**When to use:**
- Daily incremental loads where new files arrive in S3
- Avoid reprocessing historical data on every run
- Large datasets where reprocessing is expensive

**When NOT to use:**
- Full refresh jobs that should always reprocess everything
- Jobs where data changes in place (updates not appends)

---

## 9. Other Important Parameters

| Parameter | Description | Recommendation |
|---|---|---|
| **Max retries** | How many times Glue retries on failure | Set to 1 or 2 for production |
| **Job timeout** | Max minutes job can run before forced stop | Set based on expected duration + buffer |
| **Connections** | JDBC connections to RDS, Redshift | Add if reading from databases |
| **Security configuration** | Encryption settings for data at rest and in transit | Enable for production |
| **Tags** | Key-value tags for cost tracking | Always tag with team, environment, project |
| **Script path** | S3 location of your PySpark script | Store in `aws-glue-assets` bucket |
| **Temp directory** | S3 path for Spark shuffle and temp data | Use dedicated temp prefix |
| **Python library path** | S3 path to additional Python libraries (.zip or .egg) | Use for custom libraries |
| **Dependent JARs** | S3 path to additional Java JARs | Use for JDBC drivers or custom connectors |

---

## 10. Sample Glue ETL Job

---

### 10.1 Simple ETL Job - Native Spark APIs (No Glue Components)

This is the simplest way to write a Glue ETL job using pure Spark APIs without any Glue specific components like DynamicFrame or GlueContext. If you already know PySpark this will feel very familiar.

```python
import sys
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, upper, current_date

# Read job parameters
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'input_path',
    'output_path'
])

# Initialize Spark session
spark = SparkSession.builder \
    .appName(args['JOB_NAME']) \
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
    .getOrCreate()

print(f"Job Name   : {args['JOB_NAME']}")
print(f"Input Path : {args['input_path']}")
print(f"Output Path: {args['output_path']}")

# Read CSV from S3
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv(args['input_path'])

print(f"Records read: {df.count()}")
df.printSchema()

# Apply transformations
df_transformed = df \
    .withColumn("customer_name", upper(col("customer_name"))) \
    .withColumn("processed_date", current_date()) \
    .filter(col("amount").cast("double") > 0) \
    .dropDuplicates(["order_id"])

print(f"Records after transformation: {df_transformed.count()}")

# Write output as Parquet to S3
df_transformed.write \
    .mode("overwrite") \
    .partitionBy("processed_date") \
    .parquet(args['output_path'])

print("Job completed successfully")

spark.stop()
```

**Job parameters to pass when running:**
```
--input_path    s3://my-bucket/raw/orders/
--output_path   s3://my-bucket/silver/orders/
```

**Key difference from Glue specific job:**
- Uses `SparkSession` directly instead of `GlueContext`
- Uses native `spark.read` instead of `create_dynamic_frame`
- Uses native `df.write` instead of `write_dynamic_frame`
- No `job.init()` or `job.commit()` - so Job Bookmark does not work here
- Simpler and more portable - same code runs on EMR or any Spark cluster

---

### 10.2 ETL Job with Glue Components - DynamicFrame

This job uses Glue specific components. Use this when you need Job Bookmark, Glue Data Catalog integration, or are dealing with messy raw data with inconsistent schemas.

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, upper, current_date

# Initialize Glue context
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'input_path',
    'output_path'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

print(f"Job Name   : {args['JOB_NAME']}")
print(f"Input Path : {args['input_path']}")
print(f"Output Path: {args['output_path']}")

# ── Read CSV from S3 using Glue DynamicFrame ──────────────────
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [args['input_path']]},
    format="csv",
    format_options={"withHeader": True, "separator": ","}
)

print(f"Records read: {datasource.count()}")
datasource.printSchema()

# ── Convert DynamicFrame to Spark DataFrame for transformations
df = datasource.toDF()

# ── Apply transformations ─────────────────────────────────────
df_transformed = df \
    .withColumn("customer_name", upper(col("customer_name"))) \
    .withColumn("processed_date", current_date()) \
    .filter(col("amount").cast("double") > 0) \
    .dropDuplicates(["order_id"])

print(f"Records after transformation: {df_transformed.count()}")

# ── Convert back to DynamicFrame ──────────────────────────────
from awsglue.dynamicframe import DynamicFrame
output_frame = DynamicFrame.fromDF(df_transformed, glueContext, "output_frame")

# ── Write output as Parquet to S3 ─────────────────────────────
glueContext.write_dynamic_frame.from_options(
    frame=output_frame,
    connection_type="s3",
    connection_options={
        "path": args['output_path'],
        "partitionKeys": ["processed_date"]
    },
    format="parquet"
)

print("Job completed successfully")

# ── Commit job bookmark ───────────────────────────────────────
job.commit()
```

**Job parameters to pass when running:**
```
--input_path    s3://my-bucket/raw/orders/
--output_path   s3://my-bucket/silver/orders/
```

---

**Key lines explained:**

| Line | Purpose |
|---|---|
| `SparkContext()` | Initializes the Spark engine |
| `GlueContext(sc)` | Wraps SparkContext with Glue specific features |
| `glueContext.spark_session` | Gets the Spark session for DataFrame operations |
| `job.init()` | Initializes job bookmark tracking |
| `create_dynamic_frame` | Reads data into Glue DynamicFrame |
| `toDF()` | Converts DynamicFrame to Spark DataFrame |
| `DynamicFrame.fromDF()` | Converts Spark DataFrame back to DynamicFrame |
| `job.commit()` | Saves job bookmark state - always call at the end |

---

## 11. DynamicFrame vs Spark DataFrame

Glue introduces its own data structure called **DynamicFrame** on top of Spark DataFrame.

| | DynamicFrame | Spark DataFrame |
|---|---|---|
| Created by | AWS Glue | Apache Spark |
| Schema handling | Flexible - handles inconsistent schemas | Strict - schema must be defined |
| Null handling | More tolerant | Strict |
| Transformations | Limited Glue specific transforms | Full Spark SQL + functions |
| Performance | Slightly slower | Faster |
| Best for | Reading messy raw data | Complex transformations |

**Common pattern in ETL jobs:**
```
Read raw messy data → DynamicFrame (handles schema inconsistencies)
        ↓
Convert to DataFrame → toDF()
        ↓
Apply complex transformations using Spark SQL
        ↓
Convert back to DynamicFrame → DynamicFrame.fromDF()
        ↓
Write output → DynamicFrame
```

---

## 12. Running and Monitoring the ETL Job

**Run the job:**
- Glue Console → your job → **Run**
- Add job parameters → Click **Run job**

**Monitor from Runs tab:**
- Glue Console → your job → **Runs** tab
- Shows: status, start time, duration, DPU hours, records processed

**Check logs:**
- Click on a run → **Output logs** → CloudWatch (print statements)
- Click on a run → **Error logs** → CloudWatch (errors and stack traces)
- Click on a run → **Spark UI** → Visual Spark execution dashboard

**CLI monitoring:**
```bash
# Start job
aws glue start-job-run \
  --job-name order-analytics-etl \
  --arguments '{"--input_path":"s3://my-bucket/raw/orders/","--output_path":"s3://my-bucket/silver/orders/"}'

# Check status
aws glue get-job-run \
  --job-name order-analytics-etl \
  --run-id jr_xxxxx
```
