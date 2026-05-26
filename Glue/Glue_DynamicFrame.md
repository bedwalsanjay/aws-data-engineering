# AWS Glue - DynamicFrame

---

## Table of Contents

1. [What is a DynamicFrame](#1-what-is-a-dynamicframe)
2. [DynamicFrame vs Spark DataFrame](#2-dynamicframe-vs-spark-dataframe)
3. [When to Use DynamicFrame](#3-when-to-use-dynamicframe)
4. [Scenario 1 - Messy Data with Inconsistent Schema](#4-scenario-1---messy-data-with-inconsistent-schema)
5. [Scenario 2 - Reading from Glue Catalog](#5-scenario-2---reading-from-glue-catalog)
6. [Scenario 3 - Job Bookmark](#6-scenario-3---job-bookmark)
7. [Scenario 4 - Writing with Glue Specific Options](#7-scenario-4---writing-with-glue-specific-options)
8. [Converting Between DynamicFrame and DataFrame](#8-converting-between-dynamicframe-and-dataframe)
9. [Native DynamicFrame Transformations](#9-native-dynamicframe-transformations)
10. [Common DynamicFrame Operations](#10-common-dynamicframe-operations)

---

## 1. What is a DynamicFrame

DynamicFrame is a separate data structure introduced by AWS Glue, built on top of Apache Spark's RDD layer. It is **not an extension of Spark DataFrame** — it is a parallel implementation with its own limited API designed specifically for ETL workloads.

```
Apache Spark RDD (base layer)
    ├── Spark DataFrame  (standard Spark — rich API, SQL support, full transformations)
    └── DynamicFrame     (Glue's own structure — limited API, ETL focused)
```

### The Most Important Thing to Understand

DynamicFrame does **NOT** give you Spark DataFrame APIs. The two are separate.

```python
dyf = glueContext.create_dynamic_frame.from_options(...)

# These DO NOT work on a DynamicFrame
dyf.filter(col("amount") > 100)             # AttributeError
dyf.groupBy("status").count()               # AttributeError
dyf.join(other_dyf, "order_id")             # AttributeError
dyf.withColumn("tax", col("amount") * 0.1)  # AttributeError
dyf.select("order_id", "amount")            # AttributeError

# DynamicFrame has only a small set of its own methods
dyf.count()           # works
dyf.printSchema()     # works
dyf.show()            # works
dyf.resolveChoice()   # works - Glue specific
dyf.toDF()            # works - converts to Spark DataFrame
```

So in practice, the real workflow in every Glue job is:

```
DynamicFrame → toDF() → Spark DataFrame → all transformations → fromDF() → DynamicFrame → write
```

You use DynamicFrame only at the **entry and exit points** of your job. Everything in between is plain Spark.

### What DynamicFrame Actually Adds Over Spark DataFrame

| Capability | DynamicFrame | Spark DataFrame |
|---|---|---|
| Mixed type columns (`choice` type) | ✅ handles natively | ❌ must be clean before reading |
| Job Bookmark (incremental loads) | ✅ built in | ❌ not supported |
| Glue Catalog read/write (`from_catalog`) | ✅ native | needs extra config |
| `Relationalize` (flatten nested JSON) | ✅ | ❌ no direct equivalent |
| `groupBy`, `join`, `window`, `filter` | ❌ not available | ✅ full support |
| Spark SQL | ❌ not available | ✅ full support |
| Performance | slower | faster |
| Portability (EMR, Databricks) | ❌ Glue only | ✅ runs anywhere |

### The Correct Mental Model

```
DynamicFrame is NOT Spark DataFrame + extra features.
DynamicFrame is a lightweight wrapper used at the edges of a Glue job
for reading messy data and writing with Glue-specific options.
All real transformation work happens in Spark DataFrame.
```

Every DynamicFrame can be converted to a Spark DataFrame and vice versa using `toDF()` and `DynamicFrame.fromDF()`.

---

## 2. DynamicFrame vs Spark DataFrame

| | DynamicFrame | Spark DataFrame |
|---|---|---|
| Created by | AWS Glue | Apache Spark |
| Schema | Flexible - each row can have different types | Strict - all rows must match schema |
| Inconsistent data | Handles gracefully | Throws error or requires preprocessing |
| Glue Catalog integration | Native - `from_catalog` | Needs extra configuration |
| Job Bookmark support | Yes | No |
| Spark SQL functions | Not directly available | Full support |
| Performance | Slightly slower | Faster |
| Portability | Glue only | Works on any Spark cluster (EMR, Databricks) |
| Best for | Reading messy raw data, catalog integration | Complex transformations |

---

## 3. When to Use DynamicFrame

There are 4 specific scenarios where DynamicFrame adds real value over a plain Spark DataFrame:

| Scenario | Why DynamicFrame |
|---|---|
| Messy data with inconsistent schema | Handles type mismatches per row without failing |
| Reading from Glue Catalog | Native integration via `from_catalog` |
| Job Bookmark | Only works with DynamicFrame, not spark.read |
| Writing with Glue specific options | `write_dynamic_frame` supports partition keys and catalog writes |

**Use DynamicFrame when:**
- Data has inconsistent types across rows - messy raw data where same column has double in one row and string in another
- Schema evolves over time and you need flexibility to handle new or missing columns
- Reading from Glue Catalog using `from_catalog` - native integration
- Job Bookmark is needed for incremental loads - only works with DynamicFrame
- Data needs specialized transformations like `Relationalize` or `ApplyMapping`

**Use Spark DataFrame when:**
- Data is clean and well structured with consistent types
- You need full Spark SQL functions and APIs - `groupBy`, `join`, `window` functions etc.
- Performance is critical - DataFrame is faster than DynamicFrame
- Code needs to be portable - same code should run on EMR, Databricks, or any Spark cluster
- You are already comfortable with PySpark and do not need Glue specific features

**The core decision factors:**

```
Is your data messy with inconsistent types?  → DynamicFrame
Do you need Job Bookmark?                    → DynamicFrame
Are you reading from Glue Catalog?           → DynamicFrame

Is your data clean and structured?           → Spark DataFrame
Do you need complex Spark SQL operations?    → Spark DataFrame
Does code need to run outside Glue too?      → Spark DataFrame
```

> The file format (JSON, CSV, Parquet) is NOT the deciding factor. You can read any format with both DynamicFrame and Spark DataFrame. The real decision is about schema consistency and whether you need Glue specific features like Job Bookmark.

If none of the DynamicFrame scenarios apply → use `spark.read` directly. It is simpler and faster.

---

## 4. Scenario 1 - Messy Data with Inconsistent Schema

### The Problem

In real world data engineering, source data is often messy. The same column can have different data types across rows - a number in one row, a string in another, null in a third.

```
orders.csv:
order_id, customer_name, amount
ORD-001,  john smith,    99.99      ← amount is a number
ORD-002,  jane doe,      N/A        ← amount is a string
ORD-003,  bob brown,     null       ← amount is null
ORD-004,  alice green,   199.50     ← amount is a number again
```

---

### What Happens with Spark DataFrame

Spark DataFrame enforces a strict schema. Every row must match the same data type for each column.

```python
# Spark tries to infer schema from the data
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv("s3://my-bucket/raw/orders/orders.csv")
```

**What Spark does with `inferSchema=true`:**
- Scans the entire `amount` column
- Finds both numeric values (`99.99`) and non-numeric (`N/A`)
- Since it cannot infer a numeric type for the whole column it falls back to `STRING`
- `N/A` becomes a valid string value - no error thrown
- But now `amount` is a string and you cannot do math on it directly

**What Spark does with explicit schema (`amount as DoubleType`):**
- Tries to cast `N/A` to double
- Behaviour depends on the `mode` setting:

| Mode | Behaviour |
|---|---|
| `PERMISSIVE` (default) | `N/A` becomes `null`, no error thrown |
| `FAILFAST` | Throws error immediately on bad value |
| `DROPMALFORMED` | Silently drops the entire row with bad value |

**The real problem:**
```python
# amount was inferred as STRING
df.filter(col("amount") > 100)  # fails - cannot compare string with number

# You have to manually cast and handle nulls
df.filter(col("amount").cast("double") > 100)  # works but N/A rows are excluded
```

---

### What Happens with DynamicFrame

DynamicFrame does not enforce a strict schema. It uses a concept called **DynamicType** - when a column has inconsistent types across rows, it marks those rows with a special type instead of failing.

```python
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://my-bucket/raw/orders/"]},
    format="csv",
    format_options={"withHeader": True, "separator": ","}
)

datasource.printSchema()
```

**DynamicFrame schema output:**
```
root
|-- order_id: string
|-- customer_name: string
|-- amount: choice         ← DynamicFrame detected inconsistent types
|    |-- double
|    |-- string            ← N/A rows marked as string type
```

Notice `amount` is shown as `choice` type - meaning DynamicFrame found both `double` and `string` values in that column. It did not fail, it just flagged it.

---

### Resolving the Type Conflict

Once DynamicFrame has flagged the inconsistent column, you can resolve it using `ResolveChoice`:

```python
from awsglue.transforms import ResolveChoice

# Option 1 - cast all values to double, invalid values become null
resolved = ResolveChoice.apply(
    frame=datasource,
    choice="cast:double",
    specs=[("amount", "cast:double")]
)

# Option 2 - keep only the double values, drop string rows
resolved = ResolveChoice.apply(
    frame=datasource,
    choice="project:double",
    specs=[("amount", "project:double")]
)

# Option 3 - make it a struct with both types preserved
resolved = ResolveChoice.apply(
    frame=datasource,
    choice="make_struct",
    specs=[("amount", "make_struct")]
)
```

**Most common choice - `cast:double`:**
```
Before resolve:
ORD-001 → amount: 99.99  (double)
ORD-002 → amount: N/A    (string)
ORD-003 → amount: null   (null)
ORD-004 → amount: 199.50 (double)

After cast:double:
ORD-001 → amount: 99.99  ✅
ORD-002 → amount: null   ← N/A could not be cast, becomes null
ORD-003 → amount: null   ✅
ORD-004 → amount: 199.50 ✅
```

---

### Full Example

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'input_path', 'output_path'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Step 1 - Read messy CSV into DynamicFrame
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [args['input_path']]},
    format="csv",
    format_options={"withHeader": True, "separator": ","}
)

print("Schema before resolve:")
datasource.printSchema()

# Step 2 - Resolve inconsistent types in amount column
resolved = ResolveChoice.apply(
    frame=datasource,
    specs=[("amount", "cast:double")]
)

print("Schema after resolve:")
resolved.printSchema()

# Step 3 - Convert to DataFrame for transformations
df = resolved.toDF()

# Step 4 - Drop rows where amount is null (could not be cast)
df_clean = df.filter(df.amount.isNotNull())

print(f"Records after cleaning: {df_clean.count()}")

# Step 5 - Convert back to DynamicFrame and write
output = DynamicFrame.fromDF(df_clean, glueContext, "output")

glueContext.write_dynamic_frame.from_options(
    frame=output,
    connection_type="s3",
    connection_options={"path": args['output_path']},
    format="parquet"
)

job.commit()
```

---

### When Does This Happen in Real Projects

- Source system changes a column type without notifying the data team
- Multiple source systems writing to the same S3 path with slightly different schemas
- Manual data entry files where humans type `N/A`, `null`, `-`, `unknown` instead of leaving blank
- CSV exports from different versions of an application
- Third party vendor data with inconsistent formatting

---

### Summary

```
Spark DataFrame:
Inconsistent types → fails or silently loses data
You must clean data before reading

DynamicFrame:
Inconsistent types → marks as choice type, does not fail
You resolve types after reading using ResolveChoice
Much safer for raw/unknown data sources
```

---

## 5. Scenario 2 - Reading from Glue Catalog

### What is the Glue Catalog

Glue Catalog is a central metadata repository. It stores table definitions — column names, types, S3 location, file format — but NOT the actual data. The data stays in S3.

```
Glue Catalog
    └── database: ecommerce_db
            └── table: orders          ← metadata only (schema + S3 path)
                    └── data lives at: s3://my-bucket/raw/orders/
```

### Reading with spark.sql vs from_catalog

**Using spark.sql:**
```python
# Works but you need to set AWS env variables and handle header rows manually for CSV
import os
os.environ['AWS_PROFILE'] = 'default'
os.environ['AWS_REGION'] = 'ap-south-1'

df = spark.sql("SELECT * FROM ecommerce_db.orders WHERE order_status <> 'order_status'")
#                                                                         ↑
#                              CSV tables in catalog include the header row as a data row
#                              you have to filter it out manually
df.printSchema()
df.show(5)
```

**Using from_catalog:**
```python
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="ecommerce_db",
    table_name="orders"
)
# No header row problem - Glue handles it automatically
# No AWS env variables needed - GlueContext already has credentials
dyf.printSchema()
dyf.toDF().show(5)
```

**Expected schema output:**
```
root
|-- order_id: string
|-- order_date: string
|-- order_customer_id: string
|-- order_status: string
```

### Push Down Predicate — Filter at S3 Level Before Loading

This is the most important performance feature of `from_catalog`. It pushes the filter condition down to S3 so only matching data is loaded into memory — Spark never sees the rest.

```python
# Without push_down_predicate - loads ALL data into Spark, then filters
df = spark.sql("SELECT * FROM ecommerce_db.orders WHERE order_status = 'COMPLETE'")
# Spark loads every partition into memory first, then applies WHERE

# With push_down_predicate - filters at S3 level, only matching partitions loaded
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="ecommerce_db",
    table_name="orders",
    push_down_predicate="order_status = 'COMPLETE'"
)
# Only COMPLETE records are ever read from S3
```

> push_down_predicate works best on **partitioned tables**. If your table is partitioned by `order_date`, filtering on `order_date` will skip entire S3 prefixes.

### Summary

| | spark.sql | from_catalog |
|---|---|---|
| Header row issue with CSV | Yes, must filter manually | No, handled automatically |
| Push down predicate | No | Yes |
| Credentials setup | Needs env variables in local | Not needed, GlueContext handles it |
| Familiarity | Standard SQL | Glue specific |

---

## 6. Scenario 3 - Job Bookmark

### The Problem Without Job Bookmark

You have orders files landing in S3 every day. Your Glue job runs daily to process them.

```
Without Job Bookmark:
Run 1: reads orders_day1.csv                    → target has 6 records
Run 2: reads orders_day1.csv + orders_day2.csv  → target has 18 records  ← duplicates!
Run 3: reads all 3 files again                  → target has 36 records  ← more duplicates!

With Job Bookmark:
Run 1: reads orders_day1.csv              → bookmark saves: day1 done
Run 2: skips day1, reads orders_day2.csv  → bookmark saves: day1, day2 done
Run 3: skips day1+day2, reads day3 only   → no duplicates ever
```

### How It Works

Glue tracks processed files internally using their S3 ETag and size:
```
After Run 1, Glue stores:
{
  "orders_day1.csv": { "etag": "abc123", "size": 245 }
}

On Run 2, Glue compares S3 file list against bookmark:
- orders_day1.csv → already in bookmark → SKIP
- orders_day2.csv → NOT in bookmark    → PROCESS
```

### The Two Lines That Make It Work

```python
job.init(JOB_NAME, args)   # loads last saved bookmark state
# ... ETL logic ...
job.commit()               # saves new bookmark state — NEVER skip this
```

If `job.commit()` is not called → bookmark is never saved → next run reprocesses everything.

### Full Example

```python
import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)   # ← activates bookmark

datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": ["s3://my-bucket/raw/orders/"],
        "recurse": True
    },
    format="csv",
    format_options={"withHeader": True}
)

record_count = datasource.count()
print(f"New records found: {record_count}")

if record_count > 0:
    glueContext.write_dynamic_frame.from_options(
        frame=datasource,
        connection_type="s3",
        connection_options={"path": "s3://my-bucket/silver/orders/"},
        format="parquet"
    )

job.commit()   # ← saves bookmark state, always call this
```

### Important Rules

- Job Bookmark only works with `create_dynamic_frame` — **not with `spark.read`**
- Always use `mode("append")` or `write_dynamic_frame` on the target — never overwrite
- Reset bookmark + clear target together, never one without the other
- Enable bookmark from Glue Console → Job details → Job bookmark → Enable

---

## 7. Scenario 4 - Writing with Glue Specific Options

### Option 1 — Write to S3 as Parquet/CSV/JSON

```python
glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="s3",
    connection_options={"path": "s3://my-bucket/silver/orders/"},
    format="parquet"
)
```

### Option 2 — Write to S3 with Partitioning

Partitioning splits output files into folders by column value. This makes future reads much faster because Spark can skip entire folders.

```python
glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="s3",
    connection_options={
        "path": "s3://my-bucket/silver/orders/",
        "partitionKeys": ["order_status"]   # creates subfolders per status
    },
    format="parquet"
)
```

**Output folder structure:**
```
s3://my-bucket/silver/orders/
    order_status=COMPLETE/
        part-00000.parquet
    order_status=CLOSED/
        part-00000.parquet
    order_status=PENDING_PAYMENT/
        part-00000.parquet
```

Now when you query `WHERE order_status = 'COMPLETE'`, Spark only reads the `COMPLETE/` folder and skips everything else.

### Option 3 — Write back to Glue Catalog

```python
glueContext.write_dynamic_frame.from_catalog(
    frame=dyf,
    database="ecommerce_db",
    table_name="orders_silver"
)
# Glue writes data to the S3 path registered in the catalog for that table
# and updates the catalog metadata automatically
```

### Option 4 — Write to Redshift

```python
glueContext.write_dynamic_frame.from_jdbc_conf(
    frame=dyf,
    catalog_connection="redshift-connection",
    connection_options={
        "dbtable": "public.orders",
        "database": "analytics"
    },
    redshift_tmp_dir="s3://my-bucket/temp/redshift/"
)
```

### Why Not Just Use df.write?

```python
# Native Spark write — works fine for S3
df.write.mode("append").parquet("s3://my-bucket/silver/orders/")

# But native Spark write does NOT:
# - update the Glue Catalog metadata
# - support Job Bookmark tracking
# - handle Redshift COPY command automatically
```

For plain S3 writes, `df.write` is simpler and equally good. Use `write_dynamic_frame` when you need catalog updates, bookmarks, or Redshift.

---

## 8. Converting Between DynamicFrame and DataFrame

This is the most used operation in every Glue job. Since DynamicFrame has almost no transformation API, you convert to DataFrame, do all your work, then convert back only if you need Glue-specific write options.

```
DynamicFrame  →  toDF()  →  Spark DataFrame  →  all transformations  →  fromDF()  →  DynamicFrame  →  write
     ↑                                                                                                    ↑
  entry point                                                                                        exit point
  (read + resolve schema)                                                               (write with Glue options)
```

**DynamicFrame → Spark DataFrame:**
```python
df = dyf.toDF()
```

**Spark DataFrame → DynamicFrame:**
```python
from awsglue.dynamicframe import DynamicFrame

dyf = DynamicFrame.fromDF(df, glueContext, "output")
# third argument is just an internal label, any string works
```

**Full pattern used in production:**
```python
# Read with DynamicFrame — handles messy schema, bookmark
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="ecommerce_db",
    table_name="orders"
)

# Convert to DataFrame — do all real work here
df = dyf.toDF()
df = df.filter(col("order_status") == "COMPLETE")
df = df.groupBy("order_date").count()

# Convert back only if you need Glue write options
output_dyf = DynamicFrame.fromDF(df, glueContext, "output")
glueContext.write_dynamic_frame.from_options(
    frame=output_dyf,
    connection_type="s3",
    connection_options={"path": "s3://my-bucket/silver/orders/"},
    format="parquet"
)

# If you don't need Glue write options, just use df.write directly
# df.write.mode("append").parquet("s3://my-bucket/silver/orders/")
```

---

## 9. Native DynamicFrame Transformations

DynamicFrame has only 3 transformations worth knowing. Everything else should be done in Spark DataFrame.

---

### 9.1 ResolveChoice

Handles columns with mixed/inconsistent data types. Already covered in detail in Scenario 1.

```python
dyf.resolveChoice(specs=[('amount', 'cast:double')])
```

| Option | Behavior |
|---|---|
| `cast:double` | Cast all values to double, invalid values become null |
| `cast:string` | Cast everything to string |
| `project:double` | Keep only rows that were natively double, drop the rest |
| `make_struct` | Preserve all type variants as a struct for auditing |

---

### 9.2 ApplyMapping

Rename columns, cast types, and drop unwanted columns — all in one step. Equivalent to `select + withColumnRenamed + cast` in Spark.

```python
from awsglue.transforms import ApplyMapping

mapped = ApplyMapping.apply(
    frame=dyf,
    mappings=[
        # (source_column, source_type, target_column, target_type)
        ("order_id",          "string", "order_id",          "int"),
        ("order_date",        "string", "order_date",        "string"),
        ("order_customer_id", "string", "order_customer_id", "int"),
        ("order_status",      "string", "order_status",      "string"),
        # columns not listed here are automatically dropped
    ]
)
```

**Before and after:**
```
Before:
order_id (string), order_date (string), order_customer_id (string), order_status (string)

After:
order_id (int), order_date (string), order_customer_id (int), order_status (string)
```

---

### 9.3 Relationalize

Flattens nested JSON/arrays into multiple flat relational tables. No direct Spark equivalent.

**Source data:**
```json
{"order_id": "ORD-001", "customer": {"name": "John", "email": "john@x.com"},
 "items": [{"product": "Laptop", "price": 999.99}, {"product": "Mouse", "price": 29.99}]}
```

```python
from awsglue.transforms import Relationalize

dfc = Relationalize.apply(
    frame=dyf,
    staging_path="s3://my-bucket/temp/",
    name="orders"
)

print(dfc.keys())   # ['orders', 'orders_items']

orders_df = dfc.select('orders').toDF()
items_df  = dfc.select('orders_items').toDF()
```

**orders table output:**
```
order_id | customer.name | customer.email | items
ORD-001  | John          | john@x.com     | 1      ← 1 is a foreign key to items table
```

**orders_items table output:**
```
id | index | items.product | items.price
1  | 0     | Laptop        | 999.99
1  | 1     | Mouse         | 29.99
```

Join on `id` to reconstruct the full picture. Use this when loading nested API/NoSQL data into Redshift or any relational database.

---

### 9.4 Which Transformation to Use

| Transformation | Use When |
|---|---|
| `resolveChoice` | Column has mixed types detected as `choice` |
| `ApplyMapping` | Rename + cast + drop columns in one step |
| `Relationalize` | Flatten nested JSON/arrays into relational tables |

---

## 10. Common DynamicFrame Operations Quick Reference

```python
# Count
dyf.count()

# Schema
dyf.printSchema()

# Show records
dyf.show(5)

# Convert to DataFrame
df = dyf.toDF()

# Convert back to DynamicFrame
from awsglue.dynamicframe import DynamicFrame
dyf = DynamicFrame.fromDF(df, glueContext, "label")

# Read from S3
dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://my-bucket/raw/orders/"], "recurse": True},
    format="csv",
    format_options={"withHeader": True}
)

# Read from Glue Catalog
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="ecommerce_db",
    table_name="orders",
    push_down_predicate="order_status = 'COMPLETE'"  # optional
)

# Write to S3
glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="s3",
    connection_options={
        "path": "s3://my-bucket/silver/orders/",
        "partitionKeys": ["order_status"]   # optional
    },
    format="parquet"
)

# Write to Glue Catalog
glueContext.write_dynamic_frame.from_catalog(
    frame=dyf,
    database="ecommerce_db",
    table_name="orders_silver"
)
```
