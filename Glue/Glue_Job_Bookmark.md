# AWS Glue - Job Bookmark

---

## Table of Contents

1. [What is Job Bookmark](#1-what-is-job-bookmark)
2. [How Job Bookmark Works](#2-how-job-bookmark-works)
3. [Enable Job Bookmark](#3-enable-job-bookmark)
4. [Practical Demo - Incremental Load](#4-practical-demo---incremental-load)
5. [Viewing the Bookmark Value](#5-viewing-the-bookmark-value)
6. [Resetting the Bookmark](#6-resetting-the-bookmark)
7. [Job Bookmark States](#7-job-bookmark-states)
8. [When to Use and When Not to Use](#8-when-to-use-and-when-not-to-use)

---

## 1. What is Job Bookmark

Job Bookmark is a Glue feature that **tracks which data has already been processed** by a job. On subsequent runs, Glue uses this bookmark to skip already processed data and only process new data.

```
Without Job Bookmark:
Every run → processes ALL data from the beginning
Result    → duplicate records in target on every run

With Job Bookmark:
Run 1 → processes files A, B, C → saves bookmark state
Run 2 → sees bookmark → skips A, B, C → only processes D
Result → no duplicates, only new data processed
```

---

## 2. How Job Bookmark Works

Glue Job Bookmark tracks data based on:

- **S3 sources** → tracks by file modification timestamp and ETag
- **JDBC sources** → tracks by primary key or timestamp column

```
Run 1 at 10:00 AM:
S3 has: file_001.csv, file_002.csv
Glue processes both → bookmark saves:
  "last processed file: file_002.csv, timestamp: 10:00 AM"

New file arrives at 11:00 AM:
S3 has: file_001.csv, file_002.csv, file_003.csv

Run 2 at 12:00 PM:
Glue checks bookmark → sees file_001 and file_002 already processed
→ only reads file_003.csv
→ updates bookmark: "last processed file: file_003.csv, timestamp: 12:00 PM"
```

**Important:** Job Bookmark only works when using `create_dynamic_frame.from_catalog` or `create_dynamic_frame.from_options` with S3 or JDBC sources. It does NOT work with native Spark `spark.read`.

---

## 3. Enable Job Bookmark

**From Console:**
- Glue Console → your job → **Job details** tab
- Scroll to **Job bookmark**
- Set to **Enable**
- Save

**From boto3 when creating job:**
```python
import boto3

glue = boto3.client('glue', region_name='ap-south-1')

glue.create_job(
    Name='incremental-etl-job',
    Role='arn:aws:iam::123456789012:role/GlueRole',
    Command={
        'Name': 'glueetl',
        'ScriptLocation': 's3://my-bucket/scripts/etl.py',
        'PythonVersion': '3'
    },
    DefaultArguments={
        '--job-bookmark-option': 'job-bookmark-enable'
    }
)
```

---

## 4. Practical Demo - Incremental Load

**Setup:**
- Source bucket: `s3://my-bucket/raw/orders/`
- Target bucket: `s3://my-bucket/silver/orders/`
- Glue job with Job Bookmark enabled

---

### Glue ETL Script with Job Bookmark

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'input_path',
    'output_path'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# job.init() activates the bookmark tracking
job.init(args['JOB_NAME'], args)

print(f"Job Name   : {args['JOB_NAME']}")
print(f"Input Path : {args['input_path']}")

# Read from S3 - Glue automatically skips already processed files
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": [args['input_path']],
        "recurse": True
    },
    format="csv",
    format_options={"withHeader": True, "separator": ","}
)

record_count = datasource.count()
print(f"New records found: {record_count}")

if record_count == 0:
    print("No new data to process. Exiting.")
    job.commit()
else:
    df = datasource.toDF()

    # Write to target
    df.write \
        .mode("append") \
        .parquet(args['output_path'])

    print(f"Written {record_count} records to {args['output_path']}")

# job.commit() saves the bookmark state
# Without this line bookmark will NOT be updated
job.commit()
```

---

### Demo Steps

**Step 1 - Upload first batch of files:**
```bash
aws s3 cp orders_jan.csv s3://my-bucket/raw/orders/orders_jan.csv
aws s3 cp orders_feb.csv s3://my-bucket/raw/orders/orders_feb.csv
```

**Step 2 - Run the Glue job (Run 1):**
- Glue Console → your job → Run
- Check CloudWatch logs:
```
New records found: 200
Written 200 records to s3://my-bucket/silver/orders/
```

**Step 3 - Upload second batch of files:**
```bash
aws s3 cp orders_mar.csv s3://my-bucket/raw/orders/orders_mar.csv
```

**Step 4 - Run the Glue job again (Run 2):**
- Glue Console → your job → Run
- Check CloudWatch logs:
```
New records found: 100
Written 100 records to s3://my-bucket/silver/orders/
```

Only `orders_mar.csv` was processed. `orders_jan.csv` and `orders_feb.csv` were skipped by the bookmark.

**Step 5 - Run the job again with no new files (Run 3):**
```
New records found: 0
No new data to process. Exiting.
```

---

### Why `mode("append")` is used here

With Job Bookmark we use `mode("append")` instead of `mode("overwrite")` because:
- Each run only processes new files
- We want to add new records to existing target data
- `mode("overwrite")` would delete previously written data

---

### Critical - `job.commit()` must always be called

```python
# job.init() → tells Glue to start tracking from last bookmark
job.init(args['JOB_NAME'], args)

# ... your ETL logic ...

# job.commit() → saves the new bookmark state after successful run
job.commit()
```

If `job.commit()` is NOT called:
- Bookmark state is NOT saved
- Next run will reprocess the same files again
- Defeats the entire purpose of Job Bookmark

---

## 5. Viewing the Bookmark Value

Yes, you can view the bookmark value.

**From Console:**
- Glue Console → **ETL Jobs** → select your job
- Click **Job details** tab
- Scroll down to **Bookmark** section
- You will see the current bookmark state

**From AWS CLI:**
```bash
aws glue get-job-bookmark --job-name incremental-etl-job
```

**Sample output:**
```json
{
    "JobBookmarkEntry": {
        "JobName": "incremental-etl-job",
        "Version": 3,
        "Run": 3,
        "Attempt": 0,
        "PreviousRunId": "jr_abc123",
        "RunId": "jr_xyz789",
        "JobBookmark": "{\"s3://my-bucket/raw/orders/orders_jan.csv\":{\"version\":1,\"etag\":\"abc123\"},\"s3://my-bucket/raw/orders/orders_feb.csv\":{\"version\":1,\"etag\":\"def456\"},\"s3://my-bucket/raw/orders/orders_mar.csv\":{\"version\":1,\"etag\":\"ghi789\"}}"
    }
}
```

The `JobBookmark` field contains a JSON string showing all files that have been processed along with their version and ETag. This is how Glue knows which files to skip on the next run.

---

## 6. Resetting the Bookmark

Resetting the bookmark means Glue forgets all previously processed data and will reprocess everything from scratch on the next run.

**When to reset:**
- You made a bug fix and need to reprocess all historical data
- Target data was accidentally deleted
- Schema changed and all data needs to be reprocessed
- Testing and development

**From Console:**
- Glue Console → your job → **Job details** tab
- Scroll to **Bookmark** section
- Click **Reset bookmark**
- Confirm

**From AWS CLI:**
```bash
aws glue reset-job-bookmark --job-name incremental-etl-job
```

**From boto3:**
```python
import boto3

glue = boto3.client('glue', region_name='ap-south-1')

glue.reset_job_bookmark(JobName='incremental-etl-job')
print("Bookmark reset successfully")
```

**What happens after reset:**
```
Before reset:
Bookmark tracks: orders_jan.csv, orders_feb.csv, orders_mar.csv

After reset:
Bookmark is empty

Next run:
Glue processes ALL files again:
orders_jan.csv + orders_feb.csv + orders_mar.csv
```

> Be careful when resetting in production. If target already has data and you reset the bookmark, the next run will reprocess everything causing duplicates unless you also clear the target first.

---

## 7. Job Bookmark States

| State | Behavior |
|---|---|
| **Enable** | Track processed data, skip already processed files on re-run |
| **Disable** | Process all data every run, no tracking |
| **Pause** | Stop tracking new progress but keep existing bookmark state. Next run processes all data but does not update the bookmark |

**Pause use case:**
- You want to reprocess recent data without losing the full bookmark history
- Temporarily disable incremental behavior for one run only

---

## 8. When to Use and When Not to Use

**Use Job Bookmark when:**
- New files arrive in S3 regularly (daily, hourly)
- You want incremental loads without reprocessing historical data
- Large datasets where reprocessing everything is expensive
- Append only data sources

**Do NOT use Job Bookmark when:**
- Full refresh jobs that should always reprocess everything
- Data in source files changes in place (updates not appends)
- You are using native Spark `spark.read` instead of Glue DynamicFrame
- Source data is not S3 or JDBC
- You need precise control over exactly which data to process
