# AWS Glue - Complete Guide

---

## Table of Contents

1. [What is AWS Glue](#1-what-is-aws-glue)
2. [Glue Components Overview](#2-glue-components-overview)
3. [Types of Glue Jobs](#3-types-of-glue-jobs)
4. [Glue vs Lambda - When to Use Which](#4-glue-vs-lambda---when-to-use-which)
5. [Glue vs EMR Serverless](#5-glue-vs-emr-serverless)
6. [Glue Data Catalog](#6-glue-data-catalog)
7. [Glue Crawlers](#7-glue-crawlers)
8. [Glue Connections](#8-glue-connections)
9. [Glue Workflows](#9-glue-workflows)
10. [Glue Job Monitoring and Logging](#10-glue-job-monitoring-and-logging)
11. [Glue Pricing](#11-glue-pricing)

---

## 1. What is AWS Glue

AWS Glue is a fully managed **serverless ETL (Extract, Transform, Load)** service. It allows you to discover, prepare, and combine data for analytics, machine learning, and application development.

- **Serverless** - no servers to provision, patch, or manage
- **Fully managed** - AWS handles the infrastructure
- **ETL focused** - designed specifically for data transformation workloads
- **Integrated** - works natively with S3, RDS, Redshift, Athena, EMR

```
Source Data (S3, RDS, Redshift, DynamoDB)
        ↓
AWS Glue (Extract → Transform → Load)
        ↓
Target (S3, Redshift, RDS, Athena)
```

**What problems Glue solves:**

| Problem | How Glue solves it |
|---|---|
| Data scattered across multiple sources | Glue Catalog centralizes metadata |
| Schema unknown for raw data | Glue Crawlers auto discover schema |
| Complex data transformations | Glue ETL jobs with PySpark |
| Scheduling ETL pipelines | Glue Triggers and Workflows |
| No infrastructure to manage | Fully serverless |

---

## 2. Glue Components Overview

```
┌─────────────────────────────────────────────────────────┐
│                      AWS Glue                           │
│                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐  │
│  │   Crawlers  │   │  Data       │   │   ETL Jobs   │  │
│  │             │──▶│  Catalog    │◀──│              │  │
│  │ Auto schema │   │             │   │ Spark/Python │  │
│  │ discovery   │   │ Databases   │   │ Shell        │  │
│  └─────────────┘   │ Tables      │   └──────────────┘  │
│                    │ Partitions  │                      │
│  ┌─────────────┐   └─────────────┘   ┌──────────────┐  │
│  │  Triggers   │                     │  Workflows   │  │
│  │             │                     │              │  │
│  │  Schedule   │                     │ Chain jobs   │  │
│  │  On demand  │                     │ and crawlers │  │
│  │  Event      │                     │              │  │
│  └─────────────┘                     └──────────────┘  │
│                                                         │
│  ┌─────────────┐                                        │
│  │ Connections │                                        │
│  │             │                                        │
│  │ JDBC/VPC    │                                        │
│  │ credentials │                                        │
│  └─────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

| Component | Purpose |
|---|---|
| **Crawlers** | Auto discover schema from S3, RDS, Redshift and populate Data Catalog |
| **Data Catalog** | Central metadata repository - databases, tables, schemas, partitions |
| **ETL Jobs** | Spark or Python scripts that transform data |
| **Triggers** | Schedule or event based job execution |
| **Workflows** | Chain multiple jobs and crawlers into a pipeline |
| **Connections** | Store JDBC connection details for RDS, Redshift etc. |

---

## 3. Types of Glue Jobs

Glue supports 3 types of jobs:

---

### 3.1 Spark ETL Job

- Runs on an **Apache Spark** cluster managed by AWS
- Best for large scale data transformations
- Uses PySpark or Scala
- Supports reading from and writing to S3, JDBC, Glue Catalog
- Auto scales based on DPU (Data Processing Units) configured

**When to use:**
- Processing GBs to TBs of data
- Complex transformations - joins, aggregations, deduplication
- Converting CSV/JSON to Parquet/ORC
- Reading from multiple sources and joining them

```python
# Sample Spark ETL Job
from awsglue.context import GlueContext
from pyspark.context import SparkContext

sc = SparkContext()
glueContext = GlueContext(sc)

# Read from Glue Catalog
datasource = glueContext.create_dynamic_frame.from_catalog(
    database="my_database",
    table_name="raw_sales"
)

# Write to S3 as Parquet
glueContext.write_dynamic_frame.from_options(
    frame=datasource,
    connection_type="s3",
    connection_options={"path": "s3://my-bucket/silver/sales/"},
    format="parquet"
)
```

---

### 3.2 Python Shell Job

- Runs a plain **Python script** without Spark
- Lightweight, fast startup, low cost
- Good for small data, API calls, orchestration tasks
- Uses standard Python libraries + boto3

**When to use:**
- Small data transformations (MBs not GBs)
- Calling external APIs
- Triggering other AWS services
- Running SQL queries on Athena or Redshift
- Lightweight file processing

```python
# Sample Python Shell Job
import boto3

s3 = boto3.client('s3')
response = s3.list_objects_v2(Bucket='my-bucket', Prefix='raw/')
print(f"Found {response['KeyCount']} files")
```

---

### 3.3 Streaming ETL Job

- Runs continuously on **streaming data**
- Reads from Kinesis Data Streams or Apache Kafka
- Processes data in micro-batches using Spark Structured Streaming
- Writes results to S3, Redshift, or other targets

**When to use:**
- Real time or near real time data processing
- Continuous ingestion from Kinesis or Kafka
- Streaming ETL without managing Spark clusters

---

### Job Types Summary

| Job Type | Framework | Best For | Startup Time | Cost |
|---|---|---|---|---|
| Spark ETL | Apache Spark | Large scale ETL, GBs-TBs | ~2 minutes | Medium |
| Python Shell | Plain Python | Small data, API calls, orchestration | ~30 seconds | Low |
| Streaming ETL | Spark Streaming | Real time data from Kinesis/Kafka | ~2 minutes | Medium |

---

## 4. Glue vs Lambda - When to Use Which

Both can run code but they are designed for very different purposes.

| | AWS Glue | AWS Lambda |
|---|---|---|
| Max runtime | Unlimited | 15 minutes |
| Data volume | GBs to TBs | MBs (small data) |
| Framework | Spark, Python | Any language |
| Trigger | Schedule, workflow, API | Event driven (S3, SQS, API GW) |
| Startup time | 1-2 minutes | Milliseconds |
| Cost model | Per DPU hour | Per invocation + duration |
| Best for | Heavy ETL, large data | Event reactions, lightweight tasks |
| Managed infra | Yes | Yes |

**Use Glue when:**
- Data is large - GBs or TBs
- You need Spark for distributed processing
- Complex multi step transformations
- Reading from multiple sources and joining
- Converting file formats at scale
- Long running jobs beyond 15 minutes

**Use Lambda when:**
- Reacting to events - file arrives in S3, message in SQS
- Small data processing - KBs to MBs
- Triggering other services - start a Glue job, send SNS
- Quick validations or metadata operations
- Job needs to start in milliseconds not minutes

**Common pattern in data engineering:**

```
File lands in S3
        ↓
Lambda triggered (milliseconds, lightweight)
        ↓
Lambda validates file, logs metadata to DynamoDB
        ↓
Lambda triggers Glue job (heavy lifting)
        ↓
Glue processes GBs of data with Spark
        ↓
Writes output to S3
```

Lambda and Glue complement each other - Lambda for event reaction, Glue for heavy processing.

---

## 5. Glue vs EMR Serverless

Both run Spark but with different trade-offs.

| | AWS Glue | EMR Serverless |
|---|---|---|
| Management | Fully managed | Serverless but more control |
| Spark version | AWS managed version | You choose Spark version |
| Custom libraries | Limited, via Glue layers | Full control |
| Glue Catalog integration | Native, built-in | Supported but needs config |
| Startup time | ~2 minutes | ~2-3 minutes |
| Cost | Higher per DPU | Lower for large workloads |
| Debugging | Glue console + CloudWatch | EMR console + CloudWatch |
| Custom Spark config | Limited | Full control |
| Best for | Standard ETL, quick setup | Complex Spark, cost optimization |

**Use Glue when:**
- You want the simplest setup with least configuration
- Standard ETL workloads
- Team is not deeply familiar with Spark internals
- You want native Glue Catalog integration
- Quick time to production

**Use EMR Serverless when:**
- You need specific Spark version or configuration
- Cost is a concern at large scale
- You need custom Spark libraries or JARs
- Complex Spark jobs that need fine tuning
- You are migrating from on-premise Hadoop/Spark

---

## 6. Glue Data Catalog

The Glue Data Catalog is a **central metadata repository** for all your data assets. It stores information about where your data is, what format it is in, and what the schema looks like.

```
S3 bucket with CSV files
        ↓
Glue Crawler scans the data
        ↓
Glue Data Catalog stores:
  - Database name
  - Table name
  - Column names and data types
  - S3 location
  - Partition information
  - File format (CSV, Parquet, JSON)
        ↓
Athena, EMR, Redshift Spectrum, Glue Jobs
all query the same catalog
```

### Why Data Catalog matters

Without Data Catalog:
- Every tool needs to know the schema separately
- Schema changes need to be updated in multiple places
- No central place to discover what data exists

With Data Catalog:
- One place to define schema
- All tools (Athena, Glue, EMR) share the same metadata
- Schema changes propagate automatically
- Data discovery becomes easy

### Data Catalog Structure

```
Glue Data Catalog
└── Database: my_data_lake
    ├── Table: raw_sales
    │   ├── Columns: sale_id, product, amount, date
    │   ├── Location: s3://my-bucket/raw/sales/
    │   ├── Format: CSV
    │   └── Partitions: year=2024/month=01/
    ├── Table: silver_sales
    │   ├── Columns: sale_id, product, amount, date
    │   ├── Location: s3://my-bucket/silver/sales/
    │   ├── Format: Parquet
    │   └── Partitions: year=2024/month=01/
    └── Table: customers
        ├── Columns: customer_id, name, email
        ├── Location: s3://my-bucket/raw/customers/
        └── Format: JSON
```

### Hive Metastore Compatibility

Glue Data Catalog is **compatible with Apache Hive Metastore**. This means:
- Spark jobs on EMR can use Glue Catalog instead of a separate Hive Metastore
- Existing Hive queries work without changes
- On-premise Hive Metastore can be migrated to Glue Catalog

---

## 7. Glue Crawlers

A Glue Crawler automatically scans a data source, detects the schema, and populates the Glue Data Catalog.

### How Crawlers Work

```
You point crawler at S3 path or JDBC source
        ↓
Crawler samples the data
        ↓
Detects file format (CSV, Parquet, JSON)
        ↓
Infers column names and data types
        ↓
Detects partitions (year=2024/month=01/)
        ↓
Creates or updates table in Glue Catalog
```

### Create a Crawler

1. Glue Console → **Crawlers** → **Create crawler**
2. Name: `raw-sales-crawler`
3. Data source: S3 → `s3://my-bucket/raw/sales/`
4. IAM role: attach role with S3 read + Glue permissions
5. Target database: select or create database in Glue Catalog
6. Schedule: on demand or cron schedule
7. Click **Create**

### When to Run Crawlers

- After new data lands in S3 with a new schema
- After adding new partitions
- After changing file format
- As part of a Glue Workflow before running ETL jobs

### Crawler vs Manual Table Creation

| | Crawler | Manual DDL |
|---|---|---|
| Effort | Low - auto detects schema | High - write CREATE TABLE |
| Accuracy | Good for simple schemas | Exact control |
| Schema changes | Auto detects | Manual update needed |
| Best for | Quick setup, unknown schema | Precise schema control |

---

## 8. Glue Connections

Glue Connections store **connection details** for external data sources so you do not hardcode them in your ETL scripts.

**Supported connection types:**
- JDBC (RDS MySQL, PostgreSQL, Redshift, Oracle)
- MongoDB
- Kafka
- Network (VPC based connections)

**Create a Connection:**
1. Glue Console → **Connections** → **Create connection**
2. Choose connection type: JDBC
3. Enter JDBC URL, username, password
4. Choose VPC, subnet, security group
5. Test connection
6. Save

**Use in Glue Job:**
```python
# Read from RDS using Glue Connection
datasource = glueContext.create_dynamic_frame.from_catalog(
    database="my_database",
    table_name="rds_orders",
    additional_options={"connectionName": "my-rds-connection"}
)
```

---

## 9. Glue Workflows

Glue Workflows let you chain multiple Glue jobs and crawlers into a single pipeline with dependencies.

```
Trigger (schedule or on demand)
        ↓
Crawler (scan new raw data)
        ↓
Glue Job 1 (raw → bronze)
        ↓
Glue Job 2 (bronze → silver)
        ↓
Crawler (update silver catalog)
        ↓
Glue Job 3 (silver → gold)
```

**Create a Workflow:**
1. Glue Console → **Workflows** → **Add workflow**
2. Name the workflow
3. Add trigger → add jobs and crawlers
4. Define dependencies between steps
5. Run on demand or schedule

---

## 10. Glue Job Monitoring and Logging

### CloudWatch Logs

Every Glue job automatically writes logs to CloudWatch:
- `/aws-glue/jobs/output` - standard output
- `/aws-glue/jobs/error` - error logs

### Glue Job Metrics

- Glue Console → your job → **Runs** tab
- Shows: status, duration, DPU hours used, records processed

### Job Bookmarks

Glue Job Bookmarks track which data has already been processed so re-runs only process new data:
- Enable in job properties → **Job bookmark** → Enable
- Prevents reprocessing the same files on every run
- Useful for incremental loads

---

## 11. Glue Pricing

Glue pricing is based on **DPU (Data Processing Unit)**:

- 1 DPU = 4 vCPUs + 16 GB memory
- Billed per second with a 1 minute minimum
- Different rates for different job types

| Job Type | Cost per DPU hour |
|---|---|
| Spark ETL Job | $0.44 |
| Python Shell Job | $0.44 (0.0625 DPU minimum) |
| Streaming ETL Job | $0.44 |
| Glue Crawler | $0.44 |
| Glue Data Catalog | First 1 million objects free |

**Python Shell is cheapest** because it uses only 0.0625 DPU (1/16th of a DPU) by default.

**Free tier:**
- 1 million Data Catalog objects free

> Always start with the minimum DPU and scale up only if needed. A Python Shell job at 0.0625 DPU costs a fraction of a Spark job at 2 DPU.
