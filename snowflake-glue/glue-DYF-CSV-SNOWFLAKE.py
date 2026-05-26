import sys
from pyspark.context import SparkContext
from pyspark.sql.functions import col, to_timestamp
from pyspark.sql.types import (
    StructType,
    StructField,
    IntegerType,
    StringType
)
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(sys.argv, ["JOB_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# -----------------------------
# Source and Target paths
# -----------------------------
source_path = "s3://snowflake-orders/source_data/part-00000_orders_1.csv"

target_path = "s3://snowflake-orders/target_data/orders_parquet/"

# -----------------------------
# Define schema
# -----------------------------
orders_schema = StructType([
    StructField("ORDER_ID", IntegerType(), True),
    StructField("ORDER_DATE", StringType(), True),
    StructField("ORDER_CUSTOMER_ID", IntegerType(), True),
    StructField("ORDER_STATUS", StringType(), True)
])

# -----------------------------
# Read CSV from S3
# -----------------------------
df = spark.read \
    .option("header", "true") \
    .schema(orders_schema) \
    .csv(source_path)

# -----------------------------
# Transform timestamp column
# -----------------------------
df_transformed = df.withColumn(
    "ORDER_DATE",
    to_timestamp(
        col("ORDER_DATE"),
        "yyyy-MM-dd HH:mm:ss.S"
    )
)

print("Preview of transformed data")
df_transformed.show()

# -----------------------------
# Save transformed data as Parquet
# -----------------------------
df_transformed.write \
    .mode("overwrite") \
    .parquet(target_path)

print("Parquet data written successfully.")

# -----------------------------
# Convert DataFrame to DynamicFrame
# -----------------------------
dyf = DynamicFrame.fromDF(
    df_transformed,
    glueContext,
    "orders_dyf"
)

# -----------------------------
# Load into Snowflake
# -----------------------------
glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="snowflake",
    connection_options={
        "connectionName": "youtube-Snowflake-connection",
        "dbtable": "ORDERS",
        "sfDatabase": "GLUE_DATA",
        "sfSchema": "ORDERS",
        "sfWarehouse": "COMPUTE_WH"
    }
)

print("Data loaded successfully into Snowflake.")

job.commit()