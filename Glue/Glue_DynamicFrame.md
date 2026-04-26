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

DynamicFrame is a data structure introduced by AWS Glue built on top of Apache Spark. It is similar to a Spark DataFrame but with additional capabilities designed specifically for ETL workloads.

```
Apache Spark
    └── Spark DataFrame  (standard Spark)
            └── DynamicFrame  (Glue adds extra ETL features on top)
```

Every DynamicFrame can be converted to a Spark DataFrame and vice versa. They represent the same data, just with different APIs and capabilities.

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

> *Details to be covered in the next session*

---

## 6. Scenario 3 - Job Bookmark

> *Details to be covered in the next session*

---

## 7. Scenario 4 - Writing with Glue Specific Options

> *Details to be covered in the next session*

---

## 8. Converting Between DynamicFrame and DataFrame

This is the most commonly used operation in Glue ETL jobs. The typical pattern is:

```
Read raw data → DynamicFrame
        ↓
toDF() → Spark DataFrame
        ↓
Apply complex transformations using Spark SQL
        ↓
fromDF() → DynamicFrame
        ↓
Write output using write_dynamic_frame
```

**DynamicFrame to Spark DataFrame:**

```python
# Convert DynamicFrame to DataFrame
df = dynamic_frame.toDF()
```

**Spark DataFrame to DynamicFrame:**

```python
from awsglue.dynamicframe import DynamicFrame

# Convert DataFrame back to DynamicFrame
dynamic_frame = DynamicFrame.fromDF(df, glueContext, "dynamic_frame_name")
```

The third argument `"dynamic_frame_name"` is just an internal label for the DynamicFrame. It can be any string.

---

## 9. Native DynamicFrame Transformations

DynamicFrame provides specialized ETL transformation methods that are not available in Spark DataFrame. These are designed specifically for common data engineering challenges.

---

### 9.1 ResolveChoice

Handles columns with mixed/inconsistent data types. Already covered in detail in Scenario 1.

```python
from awsglue.transforms import ResolveChoice

# Cast inconsistent column to a specific type
resolved = ResolveChoice.apply(
    frame=datasource,
    specs=[("amount", "cast:double")]
)
```

**Resolution options:**

| Option | Behavior |
|---|---|
| `cast:double` | Cast all values to double, invalid values become null |
| `cast:string` | Cast all values to string |
| `project:double` | Keep only double values, drop rows with other types |
| `make_struct` | Preserve both types as a struct `{double: 99.99, string: null}` |
| `make_array` | Combine both types into an array |

---

### 9.2 ApplyMapping

Renames columns, changes data types, and selects which columns to keep - all in one operation. Think of it as a combination of `withColumnRenamed`, `cast`, and `select` in Spark.

```python
from awsglue.transforms import ApplyMapping

mapped = ApplyMapping.apply(
    frame=datasource,
    mappings=[
        # (source_column, source_type, target_column, target_type)
        ("order_id",      "string", "order_id",      "string"),
        ("customer_name", "string", "customer_name", "string"),
        ("amount",        "string", "amount",         "double"),  # rename + cast
        ("order_date",    "string", "order_date",     "date"),    # cast to date
        # any column not listed here is dropped from output
    ]
)
```

**What ApplyMapping does in one step:**

```
Before:
order_id (string), customer_name (string), amount (string), order_date (string), product (string)

After ApplyMapping:
order_id (string), customer_name (string), amount (double), order_date (date)
                                                                ↑
                                              product column dropped (not in mappings)
                                              amount cast from string to double
                                              order_date cast from string to date
```

**When to use ApplyMapping:**
- Rename multiple columns at once
- Cast multiple columns to correct types in one step
- Drop unwanted columns by simply not including them in mappings
- Clean up schema before writing to target

---

### 9.3 Relationalize

Flattens **nested JSON/struct data** into multiple flat relational tables. This is the most unique DynamicFrame transformation with no direct Spark equivalent.

**The problem it solves:**

JSON data from APIs or NoSQL databases often has nested structures:

```json
{
    "order_id": "ORD-001",
    "customer": {
        "name": "John Smith",
        "email": "john@example.com"
    },
    "items": [
        {"product": "Laptop", "quantity": 1, "price": 999.99},
        {"product": "Mouse",  "quantity": 2, "price": 29.99}
    ]
}
```

This cannot be stored directly in a relational database or queried easily with SQL. `Relationalize` flattens it automatically.

```python
from awsglue.transforms import Relationalize
from awsglue.s3 import S3JsonClassifier

# Read nested JSON
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://my-bucket/raw/orders-nested/"]},
    format="json"
)

# Relationalize - flatten nested structure
dfc = Relationalize.apply(
    frame=datasource,
    staging_path="s3://my-bucket/temp/relationalize/",
    name="orders"
)

# Relationalize returns a DynamicFrameCollection (multiple tables)
# List all tables created
print(dfc.keys())
# Output: ['orders', 'orders_items']

# Get the root table
orders_df = dfc.select('orders').toDF()
orders_df.show()

# Get the items table (flattened array)
items_df = dfc.select('orders_items').toDF()
items_df.show()
```

**What Relationalize produces:**

**orders table:**
```
order_id | customer.name | customer.email | items
---------|---------------|----------------|-------
ORD-001  | John Smith    | john@example   | 1
```

**orders_items table:**
```
id | index | items.product | items.quantity | items.price
---|-------|---------------|----------------|------------
1  | 0     | Laptop        | 1              | 999.99
1  | 1     | Mouse         | 2              | 29.99
```

The two tables can be joined on the `id` column to reconstruct the original relationship.

**When to use Relationalize:**
- Loading nested JSON from APIs into Redshift or RDS
- Flattening DynamoDB exports for SQL analysis
- Processing nested data from MongoDB or DocumentDB
- Any scenario where nested data needs to go into a relational database

---

### 9.4 Summary - Which Transformation to Use

| Transformation | Use When |
|---|---|
| `ResolveChoice` | Column has mixed types (double + string in same column) |
| `ApplyMapping` | Rename columns, cast types, drop unwanted columns in one step |
| `Relationalize` | Flatten nested JSON/arrays into relational tables |

> These three transformations together cover the most common raw data cleaning challenges in ETL pipelines. We will create dedicated md files for each with detailed demos as we progress through the course.

---

## 10. Common DynamicFrame Operations

```python
# Count records
datasource.count()

# Print schema
datasource.printSchema()

# Show sample records
datasource.toDF().show(5)

# Convert to DataFrame
df = datasource.toDF()

# Convert back to DynamicFrame
from awsglue.dynamicframe import DynamicFrame
output = DynamicFrame.fromDF(df, glueContext, "output")

# Write to S3 as Parquet
glueContext.write_dynamic_frame.from_options(
    frame=output,
    connection_type="s3",
    connection_options={"path": "s3://my-bucket/silver/orders/"},
    format="parquet"
)

# Write to Glue Catalog
glueContext.write_dynamic_frame.from_catalog(
    frame=output,
    database="silver_db",
    table_name="orders_silver"
)
```
