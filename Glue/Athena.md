# AWS Athena

Amazon Athena is a **serverless, interactive query service** that lets you analyze data directly in S3 using standard SQL — no infrastructure to manage, no data loading required.

## How Athena Works

```
S3 (data files)  →  Glue Catalog (metadata/schema)  →  Athena (SQL queries)
```

- Data stays in S3 — Athena never moves or copies it
- Glue Catalog stores the schema (column names, types, S3 location)
- Athena uses the schema to query the data in S3
- You pay only for the data scanned per query

---

## First Time Setup — Query Result Location

Before running your first query, Athena requires an S3 location to store query results. Without this you will see:

> *"Before you run your first query, you need to set up a query result location in Amazon S3."*

### Steps to set it up

1. Open **AWS Console → Athena**
2. Click **Settings** (top right)
3. Click **Manage**
4. Under **Query result location**, enter an S3 path:
   ```
   s3://sanjay-de-bucket-2026/athena-results/
   ```
5. Click **Save**

> The `athena-results/` folder doesn't need to exist — Athena will create it automatically on first query run.

**What gets stored there?**
- Every query result is saved as a `.csv` file in this location
- A `.csv.metadata` file is also saved alongside it
- These are just Athena's working files — not your actual data
- You can set a lifecycle policy on this folder to auto-delete files older than 30 days to save cost

---

## Key Concepts

| Term | Meaning |
|---|---|
| External Table | Table whose data lives in S3, not inside a database |
| SerDe | Serializer/Deserializer — tells Athena how to read the file format (CSV, JSON, Parquet etc) |
| Hive Style Partition | Folder structure like `s3://bucket/data/year=2024/month=01/` |
| Partition | A subset of data stored in a separate S3 prefix for faster queries |
| MSCK REPAIR TABLE | Command to auto-discover new Hive-style partitions and register them in Glue Catalog |

---

## 1. External Table on S3 — No Partitions

### When to use
Use this when:
- Schema of incoming files **always remains the same**
- No need for a Crawler — new files dropped in the S3 path are **automatically reflected**
- Simple flat folder structure (no partitions)

### Example — CSV file

S3 path: `s3://sanjay-de-bucket-2026/raw/orders/`

Files in path:
```
s3://sanjay-de-bucket-2026/raw/orders/orders_jan.csv
s3://sanjay-de-bucket-2026/raw/orders/orders_feb.csv
s3://sanjay-de-bucket-2026/raw/orders/orders_mar.csv
```

```sql
CREATE EXTERNAL TABLE ecommerce_db1.orders (
    order_id      STRING,
    order_date    DATE,
    customer_id   STRING,
    product_id    STRING,
    product_name  STRING,
    category      STRING,
    quantity      INT,
    unit_price    INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://sanjay-de-bucket-2026/raw/orders/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

### What happens when new data arrives?

```
Month 1: orders_jan.csv uploaded → Athena query returns Jan data
Month 2: orders_feb.csv uploaded → Athena query automatically returns Jan + Feb data
Month 3: orders_mar.csv uploaded → Athena query automatically returns Jan + Feb + Mar data
```

**No Crawler needed. No ALTER TABLE needed. Just upload the file and query.**

> Key point: This works because the table points to an **S3 path (prefix)**, not a specific file. Athena scans all files under that prefix.

### Example — Parquet file

```sql
CREATE EXTERNAL TABLE ecommerce_db1.subscriber_plans_parquet (
    gender      STRING,
    birth_date  STRING,
    is_vip      BOOLEAN,
    plan_desc   STRING,
    plan_price  INT
)
STORED AS PARQUET
LOCATION 's3://sanjay-de-bucket-2026/parquet_data_sample/';
```

> Note: No `skip.header.line.count` needed for Parquet — it stores schema in the file itself.

---

## 1b. External Table on S3 — CSV with Quoted Fields (OpenCSVSerde)

### When to use
Use this when your CSV has fields that **contain commas inside quoted strings** — `LazySimpleSerDe` (used by `ROW FORMAT DELIMITED`) will misparse these.

### Sample data — save as `customers.csv` and upload to S3

```
customer_id,customer_name,address,amount
CUST-001,"Smith, John","123 Main St, New York",1500.00
CUST-002,"Johnson, Mary","456 Oak Ave, Los Angeles",2300.50
CUST-003,"Brown, James","789 Pine Rd, Chicago",980.75
CUST-004,"Davis, Sarah","321 Elm St, Houston",3200.00
CUST-005,"Wilson, Mike","654 Maple Dr, Phoenix",750.25
```

> Notice `"Smith, John"` and `"123 Main St, New York"` — commas inside quoted fields. `ROW FORMAT DELIMITED` would split these incorrectly into extra columns.

### Create table using OpenCSVSerde

S3 path: `s3://sanjay-de-bucket-2026/raw/customers/`

```sql
CREATE EXTERNAL TABLE ecommerce_db.customers (
    customer_id   STRING,
    customer_name STRING,
    address       STRING,
    amount        DOUBLE
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    'separatorChar' = ',',
    'quoteChar'     = '"'
)
STORED AS TEXTFILE
LOCATION 's3://sanjay-de-bucket-2026/raw/customers/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

### SerDe comparison

| | `ROW FORMAT DELIMITED` | `OpenCSVSerde` |
|---|---|---|
| Simple CSV | ✅ Works | ✅ Works |
| CSV with quoted commas | ❌ Misparsed | ✅ Works |
| Explicit SerDe needed | ❌ No | ✅ Yes |
| Default SerDe used | LazySimpleSerDe | OpenCSVSerde |

---

## 2. External Table on S3 — With Hive Style Partitions

### What are Hive Style Partitions?

A folder structure where the **partition key and value are part of the folder name**:

```
s3://aws-glue-temporary-361116840744-ap-south-1/example/subscriber_plans/plan_id=1005969896014/
s3://aws-glue-temporary-361116840744-ap-south-1/example/subscriber_plans/plan_id=1069854325801/
s3://aws-glue-temporary-361116840744-ap-south-1/example/subscriber_plans/plan_id=1099999999999/
```

Athena can use these partitions to **skip scanning irrelevant data** — making queries faster and cheaper.

### Create the partitioned table

```sql
CREATE EXTERNAL TABLE ecommerce_db.subscriber_plans (
    gender      STRING,
    birth_date  STRING,
    is_vip      BOOLEAN,
    plan_desc   STRING,
    plan_price  INT
)
PARTITIONED BY (plan_id BIGINT)
STORED AS PARQUET
LOCATION 's3://aws-glue-temporary-361116840744-ap-south-1/example/subscriber_plans/';
```

> Note: The partition column `plan_id` is **NOT** in the main column list — it's defined separately in `PARTITIONED BY`.

### The Problem — New partitions are NOT auto-discovered

Unlike non-partitioned tables, **Athena does not automatically see new partitions**. When a new `plan_id=XXXX/` folder is added to S3, Glue Catalog doesn't know about it until you tell it.

```sql
-- This will return 0 rows even if data exists in S3
SELECT * FROM ecommerce_db.subscriber_plans WHERE plan_id = 1005969896014;
```

### Fix Option 1 — MSCK REPAIR TABLE (manual, one-time scan)

Scans the entire S3 path and registers all discovered Hive-style partitions into Glue Catalog:

```sql
MSCK REPAIR TABLE ecommerce_db.subscriber_plans;
```

Run this every time new partitions are added. After running:
```sql
-- Now this works
SELECT * FROM ecommerce_db.subscriber_plans WHERE plan_id = 1005969896014;

-- Check all registered partitions
SHOW PARTITIONS ecommerce_db.subscriber_plans;
```

> Limitation: `MSCK REPAIR TABLE` can be slow if there are thousands of partitions since it scans the entire S3 path.

### Fix Option 2 — ALTER TABLE ADD PARTITION (manual, targeted)

Add specific partitions manually without scanning the entire path:

```sql
ALTER TABLE ecommerce_db.subscriber_plans ADD IF NOT EXISTS
    PARTITION (plan_id = 1005969896014)
    LOCATION 's3://aws-glue-temporary-361116840744-ap-south-1/example/subscriber_plans/plan_id=1005969896014/'

    PARTITION (plan_id = 1069854325801)
    LOCATION 's3://aws-glue-temporary-361116840744-ap-south-1/example/subscriber_plans/plan_id=1069854325801/';
```

> Use this when you know exactly which partitions were added — faster than `MSCK REPAIR TABLE`.

### Fix Option 3 — AWS Glue Crawler (automated)

Set up a Crawler to run on a schedule (e.g. daily) that scans the S3 path and automatically registers new partitions in Glue Catalog.

**When to use each option:**

| Option | When to use |
|---|---|
| `MSCK REPAIR TABLE` | One-time setup or infrequent partition additions |
| `ALTER TABLE ADD PARTITION` | You know exactly which partitions were added (e.g. from a Glue job) |
| Glue Crawler | Fully automated, large number of partitions, frequent additions |

---

## 3. Query Optimization Tips

### Partition Pruning — Always filter on partition column

```sql
-- BAD — scans ALL partitions (expensive)
SELECT * FROM ecommerce_db.subscriber_plans;

-- GOOD — scans only plan_id=1005969896014 partition (cheap)
SELECT * FROM ecommerce_db.subscriber_plans
WHERE plan_id = 1005969896014;
```

### Use columnar formats (Parquet/ORC) over CSV

```
CSV  → Athena scans entire file even for 1 column query
Parquet → Athena scans only the columns you SELECT (columnar storage)
```

### Use compression

```sql
-- Snappy compressed Parquet — less data scanned = cheaper + faster
STORED AS PARQUET
TBLPROPERTIES ('parquet.compression'='SNAPPY');
```

---

## 4. Useful DDL Commands

```sql
-- List all databases
SHOW DATABASES;

-- List all tables in a database
SHOW TABLES IN order_analytics_dev;

-- View table schema
DESCRIBE order_analytics_dev.order_revenue_by_category; 

-- View full table definition including location and properties
SHOW CREATE TABLE ecommerce_db.orders;

-- View registered partitions
SHOW PARTITIONS ecommerce_db.subscriber_plans;

-- Drop a table (does NOT delete S3 data — external table)
DROP TABLE IF EXISTS ecommerce_db.orders;

-- Drop a specific partition from catalog (does NOT delete S3 data)
ALTER TABLE ecommerce_db.subscriber_plans
DROP PARTITION (plan_id = 1005969896014);
```

---

---

## 5. Multiple External Tables on the Same S3 Location

Yes, you can create multiple external tables pointing to the **same S3 path**. Since external tables are just metadata (schema + pointer to S3), creating or dropping them has no effect on the actual data.

### Example

```sql
-- Table 1 — full schema for data engineers
CREATE EXTERNAL TABLE ecommerce_db.orders_full (
    order_id      STRING,
    order_date    DATE,
    customer_id   STRING,
    product_id    STRING,
    product_name  STRING,
    category      STRING,
    quantity      INT,
    unit_price    DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://sanjay-de-bucket-2026/raw/orders/'
TBLPROPERTIES ('skip.header.line.count'='1');

-- Table 2 — only financial columns for finance team
CREATE EXTERNAL TABLE ecommerce_db.orders_finance (
    order_id      STRING,
    order_date    DATE,
    quantity      INT,
    unit_price    DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://sanjay-de-bucket-2026/raw/orders/'
TBLPROPERTIES ('skip.header.line.count'='1');

-- Table 3 — only product columns for product team
CREATE EXTERNAL TABLE ecommerce_db.orders_products (
    order_id      STRING,
    product_id    STRING,
    product_name  STRING,
    category      STRING,
    quantity      INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://sanjay-de-bucket-2026/raw/orders/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

All 3 tables point to the same S3 path — same data, different views of it.


> Dropping any of these tables **never deletes the S3 data** — it only removes the metadata from Glue Catalog.

---

## 6. Is Athena Table Always an External Table?

**Yes — in Athena, every table is always an external table.**

### Why?

Athena is a **serverless query engine** — it has no storage of its own. It can only query data that lives somewhere else (S3). So by design:

- Athena **never owns the data**
- Athena **never stores the data**
- Athena only stores the **metadata** (schema, location) in Glue Catalog
- The actual data always lives in **S3**

This is fundamentally different from traditional databases like MySQL or Redshift where the database owns and manages the data storage.

### What happens when you DROP a table in Athena?

```sql
DROP TABLE ecommerce_db.orders;
```

- ✅ Removes the table metadata from Glue Catalog
- ❌ Does NOT delete the data from S3
- ❌ Does NOT affect any other table pointing to the same S3 location

This is the key characteristic of an external table — **metadata and data are decoupled**.

### Comparison with traditional databases

| | Traditional DB (MySQL/Redshift) | Athena |
|---|---|---|
| Data stored in | Database storage | S3 |
| DROP TABLE deletes data | ✅ Yes | ❌ No |
| Table type | Internal (managed) | Always External |
| Storage cost | Pay for DB storage | Pay for S3 storage |
| Query cost | Pay for compute | Pay per data scanned |

> This is why Athena is ideal for a **data lake architecture** — your data lives in S3 (cheap, durable, scalable) and Athena just provides a SQL interface on top of it.

| Scenario | Need Crawler? |
|---|---|
| Non-partitioned table, schema never changes | ❌ No — just create external table once |
| Non-partitioned table, schema changes (new columns) | ✅ Yes — Crawler detects schema evolution |
| Partitioned table, partitions added manually | ❌ No — use `MSCK REPAIR TABLE` or `ALTER TABLE ADD PARTITION` |
| Partitioned table, partitions added frequently/automatically | ✅ Yes — Crawler automates partition discovery |
| Brand new S3 path, unknown schema | ✅ Yes — Crawler infers schema automatically |
