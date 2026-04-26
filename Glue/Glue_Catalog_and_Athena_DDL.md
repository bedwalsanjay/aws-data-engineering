# AWS Glue - Data Catalog

---

## Table of Contents

1. [What is Glue Data Catalog](#1-what-is-glue-data-catalog)
2. [Why Data Catalog Matters](#2-why-data-catalog-matters)
3. [Data Catalog Structure](#3-data-catalog-structure)
4. [Creating a Database Manually](#4-creating-a-database-manually)
5. [Creating a Table Manually](#5-creating-a-table-manually)
6. [Supported Data Formats](#6-supported-data-formats)
7. [Partitions in Glue Catalog](#7-partitions-in-glue-catalog)
8. [Querying Catalog Tables with Athena](#8-querying-catalog-tables-with-athena)
9. [Glue Catalog vs Hive Metastore](#9-glue-catalog-vs-hive-metastore)
10. [Who Uses the Glue Data Catalog](#10-who-uses-the-glue-data-catalog)

---

## 1. What is Glue Data Catalog

Glue Data Catalog is a **central metadata repository** for all your data assets on AWS. It stores information about your data - where it lives, what format it is in, what the schema looks like - but it does NOT store the actual data itself.

```
Without Glue Data Catalog:
Every tool needs to know separately:
  - Where is the data? (S3 path)
  - What format is it? (CSV, Parquet, JSON)
  - What are the columns? (schema)
  - What are the partitions?

With Glue Data Catalog:
Define it once in the catalog
Every tool reads from the catalog
One source of truth for all metadata
```

Think of it as a **library index**. The books (data) stay on the shelves (S3, RDS, Redshift). The index just tells you where each book is and what it contains.

---

## 2. Why Data Catalog Matters

**Problem without catalog:**

```
Data Engineer  → writes Glue ETL job
               → hardcodes S3 path: s3://my-bucket/raw/orders/
               → hardcodes schema: order_id string, amount double...

Data Analyst   → writes Athena query
               → hardcodes S3 path: s3://my-bucket/raw/orders/
               → hardcodes schema again in CREATE EXTERNAL TABLE

Data Scientist → writes PySpark job on EMR
               → hardcodes S3 path: s3://my-bucket/raw/orders/
               → hardcodes schema again in StructType definition

BI Developer   → connects Redshift Spectrum
               → hardcodes S3 path: s3://my-bucket/raw/orders/
               → hardcodes schema again in CREATE EXTERNAL TABLE

S3 path changes or a column is added to the schema:
→ Data Engineer updates Glue job
→ Data Analyst updates Athena table
→ Data Scientist updates EMR job
→ BI Developer updates Redshift Spectrum
→ 4 people, 4 places to update, high chance of inconsistency
```

**With catalog:**

```
S3 path and schema defined ONCE in Glue Catalog
        ↓
Glue ETL job      → reads from catalog → no hardcoded paths
Athena            → reads from catalog → no hardcoded paths
EMR Spark job     → reads from catalog → no hardcoded paths
Redshift Spectrum → reads from catalog → no hardcoded paths

S3 path changes or column added:
→ Update catalog ONCE
→ All tools automatically get the latest definition
```

---

## 3. Data Catalog Structure

The catalog is organized in a 3 level hierarchy:

```
Glue Data Catalog (one per AWS account per region)
└── Database (logical grouping of tables)
    ├── Table 1 (metadata for one dataset)
    │   ├── Schema (column names and data types)
    │   ├── S3 Location (where the data lives)
    │   ├── Format (CSV, Parquet, JSON, ORC)
    │   ├── SerDe (how to read/write the format)
    │   └── Partitions (year=2024/month=01 etc.)
    ├── Table 2
    └── Table 3
```

**Database:**
- Logical container for related tables
- Similar to a schema in a relational database
- Example: `raw_db`, `silver_db`, `gold_db`

**Table:**
- Metadata definition of one dataset
- Points to an S3 location
- Defines column names, data types, format
- Does NOT contain actual data - just describes it

---

## 4. Creating a Database Manually

**From Console:**
1. Glue Console → left sidebar → **Databases**
2. Click **Add database**
3. Fill in:
   - Name: `raw_db`
   - Description: Raw layer database
   - Location (optional): S3 path for the database
4. Click **Create database**

**From AWS CLI:**
```bash
aws glue create-database \
  --database-input '{
    "Name": "raw_db",
    "Description": "Raw layer database"
  }'
```

**From boto3:**
```python
import boto3

glue = boto3.client('glue', region_name='ap-south-1')

glue.create_database(
    DatabaseInput={
        'Name': 'raw_db',
        'Description': 'Raw layer database'
    }
)
print("Database created successfully")
```

---

## 5. Creating a Table Manually

A table in Glue Catalog is an **external table** - it points to data in S3 but does not own or store the data. The easiest way to create a table is using Athena DDL (SQL) which is much simpler than the console form or boto3.

---

### 5.1 From Athena - CSV Table

Open Athena Query Editor and run:

```sql
CREATE EXTERNAL TABLE raw_db.orders (
    order_id        STRING,
    customer_name   STRING,
    product         STRING,
    amount          DOUBLE,
    order_date      STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://my-bucket/raw/orders/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

**Key clauses explained:**

| Clause | Purpose |
|---|---|
| `EXTERNAL TABLE` | Table points to S3 data, does not own it. Dropping table does not delete S3 data |
| `ROW FORMAT DELIMITED` | Data is in delimited format |
| `FIELDS TERMINATED BY ','` | Comma separated values |
| `STORED AS TEXTFILE` | Plain text file format (CSV) |
| `LOCATION` | S3 path where the data files live |
| `skip.header.line.count` | Skip the first row (header row) |

---

### 5.2 From Athena - Parquet Table

```sql
CREATE EXTERNAL TABLE silver_db.orders_silver (
    order_id        STRING,
    customer_name   STRING,
    product         STRING,
    amount          DOUBLE,
    order_date      STRING,
    processed_date  DATE
)
STORED AS PARQUET
LOCATION 's3://my-bucket/silver/orders/';
```

Parquet is much simpler - no need to define delimiters since it is a binary columnar format.

---

### 5.3 From Athena - Partitioned Parquet Table

```sql
CREATE EXTERNAL TABLE silver_db.orders_partitioned (
    order_id        STRING,
    customer_name   STRING,
    product         STRING,
    amount          DOUBLE
)
PARTITIONED BY (
    year    STRING,
    month   STRING
)
STORED AS PARQUET
LOCATION 's3://my-bucket/silver/orders/';
```

After creating a partitioned table, run this to load existing partitions:

```sql
MSCK REPAIR TABLE silver_db.orders_partitioned;
```

`MSCK REPAIR TABLE` scans the S3 location, discovers all partition folders and registers them in the Glue Catalog automatically.

---

### 5.4 From Athena - JSON Table

```sql
CREATE EXTERNAL TABLE raw_db.orders_json (
    order_id        STRING,
    customer_name   STRING,
    product         STRING,
    amount          DOUBLE,
    order_date      STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://my-bucket/raw/orders-json/';
```

---

### 5.5 Verify Table Created in Glue Catalog

After running any of the above DDL in Athena:
- Glue Console → **Databases** → `raw_db` → **Tables**
- Your table will appear there immediately
- Click on the table to see schema, S3 location, format, SerDe details

This confirms that Athena DDL and Glue Catalog are the same thing - Athena just provides a SQL interface to create catalog entries.

---

### 5.6 SerDe - What is it

SerDe stands for **Serializer/Deserializer**. It tells Glue and Spark how to read and write a specific file format.

| Format | SerDe Library |
|---|---|
| CSV | `org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe` |
| JSON | `org.openx.data.jsonserde.JsonSerDe` |
| Parquet | `org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe` |
| ORC | `org.apache.hadoop.hive.ql.io.orc.OrcSerde` |
| Avro | `org.apache.hadoop.hive.serde2.avro.AvroSerDe` |

> You do not need to memorize these. When using Athena DDL with `STORED AS PARQUET` or `STORED AS ORC`, Athena fills in the correct SerDe automatically. You only need to specify SerDe manually for JSON as shown in section 5.4.

---

## 6. Supported Data Formats

| Format | Type | Best For |
|---|---|---|
| CSV | Row based | Simple flat files, easy to read |
| JSON | Row based | Semi-structured, nested data |
| Parquet | Columnar | Analytics, large datasets, cost efficient with Athena |
| ORC | Columnar | Hive workloads, similar to Parquet |
| Avro | Row based | Streaming, schema evolution |

> For data engineering workloads always prefer **Parquet** in silver and gold layers. It is columnar, compressed, and significantly reduces Athena query costs.

---

## 7. Partitions in Glue Catalog

Partitions allow Glue and Athena to skip irrelevant data when querying, dramatically improving performance and reducing cost.

**Partitioned table structure in S3:**
```
s3://my-bucket/silver/orders/
├── year=2024/month=01/orders_jan.parquet
├── year=2024/month=02/orders_feb.parquet
└── year=2024/month=03/orders_mar.parquet
```

**Creating a partitioned table in Athena:**

```sql
CREATE EXTERNAL TABLE silver_db.orders_partitioned (
    order_id        STRING,
    customer_name   STRING,
    amount          DOUBLE
)
PARTITIONED BY (
    year    STRING,
    month   STRING
)
STORED AS PARQUET
LOCATION 's3://my-bucket/silver/orders/';
```

**Load existing partitions:**

```sql
MSCK REPAIR TABLE silver_db.orders_partitioned;
```

**Add a specific partition manually:**

```sql
ALTER TABLE silver_db.orders_partitioned
ADD PARTITION (year='2024', month='01')
LOCATION 's3://my-bucket/silver/orders/year=2024/month=01/';
```

> In practice partitions are usually added automatically by Glue Crawlers or by running `MSCK REPAIR TABLE` in Athena rather than manually.

---

## 8. Querying Catalog Tables with Athena

Once a table is created in Glue Catalog, Athena can query it immediately without any additional setup.

```sql
-- Query the orders table
SELECT * FROM raw_db.orders LIMIT 10;

-- Query with partition filter (much faster and cheaper)
SELECT * FROM silver_db.orders_partitioned
WHERE year = '2024' AND month = '01';

-- Aggregation
SELECT product, SUM(amount) as total_sales
FROM raw_db.orders
GROUP BY product
ORDER BY total_sales DESC;
```

> Athena uses the S3 location and schema from Glue Catalog to know where and how to read the data.

---

## 9. Glue Catalog vs Hive Metastore

Glue Data Catalog is **compatible with Apache Hive Metastore**. This means:

| | Glue Data Catalog | Hive Metastore |
|---|---|---|
| Managed by | AWS (fully managed) | You manage (MySQL/Postgres backend) |
| Integration | Native with Athena, EMR, Glue | Hadoop ecosystem |
| API compatibility | Hive Metastore API | Hive Metastore API |
| Migration | On-premise Hive → Glue Catalog possible | - |
| Cost | First 1M objects free | Infrastructure cost |

EMR clusters can be configured to use Glue Catalog instead of a local Hive Metastore:
- All EMR jobs and Glue jobs share the same catalog
- No duplicate table definitions
- One source of truth across all compute engines

---

## 10. Who Uses the Glue Data Catalog

The catalog is shared across multiple AWS services:

```
Glue Data Catalog
        ↓
┌───────────────────────────────────────────┐
│                                           │
│  Athena    → SQL queries on S3 data       │
│  Glue Jobs → ETL using from_catalog       │
│  EMR       → Spark/Hive jobs              │
│  Redshift  → Redshift Spectrum queries    │
│  Lake      → AWS Lake Formation           │
│  Formation    access control              │
│                                           │
└───────────────────────────────────────────┘
```

This is the core value of Glue Data Catalog - define your data once, use it everywhere.
