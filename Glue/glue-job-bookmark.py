import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.types import IntegerType, TimestampType
from pyspark.sql.functions import lit, input_file_name, regexp_extract, col

# Initialize Glue context and job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Define source and target paths
source_path = "s3://<bucket_name>/source_files/orders/"
target_path = "s3://<bucket_name>/target_files/orders/"

# Read source data with bookmark support
source_GDF = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": [source_path],
        "recurse": True
    },
    format="csv",
    format_options={
        "withHeader": True
    },
    transformation_ctx="source_GDF"
)

# Convert DynamicFrame to DataFrame
df = source_GDF.toDF()

# Explicitly cast columns — Glue CSV reader ignores schema and reads everything as string
df = df.withColumn("order_id", col("order_id").cast(IntegerType())) \
       .withColumn("order_date", col("order_date").cast(TimestampType())) \
       .withColumn("order_customer_id", col("order_customer_id").cast(IntegerType()))

# Capture file path BEFORE dropDuplicates (input_file_name() loses lineage after shuffle)
df = (
    df.withColumn("source_file_path", input_file_name())
      .withColumn("source_file_name", regexp_extract(col("source_file_path"), r'([^/]+$)', 1))
)

# Remove duplicates
df = df.dropDuplicates()

# Store current timestamp in a variable
ingestion_ts = spark.sql(
    "SELECT current_timestamp() AS ingestion_date"
).collect()[0]["ingestion_date"]

# Add ingestion timestamp
df = df.withColumn("ingestion_date", lit(ingestion_ts))

# Convert DataFrame back to DynamicFrame
target_GDF = DynamicFrame.fromDF(
    df,
    glueContext,
    "target_GDF"
)

# Write data to target in Parquet format
glueContext.write_dynamic_frame.from_options(
    frame=target_GDF,
    connection_type="s3",
    connection_options={
        "path": target_path
    },
    format="parquet"
)

# Commit job
job.commit()
#   aws glue get-job-bookmark --job-name glue-job-bookmark