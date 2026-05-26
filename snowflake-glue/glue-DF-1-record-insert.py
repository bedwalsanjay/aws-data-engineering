import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, TimestampType
from datetime import datetime

args = getResolvedOptions(sys.argv, ["JOB_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Create sample Spark DataFrame
data = [
    (3, datetime.strptime("2013-07-25 00:00:00.0", "%Y-%m-%d %H:%M:%S.%f"), 256, "PENDING_PAYMENT")
]

schema = StructType([
    StructField("ORDER_ID", IntegerType(), True),
    StructField("ORDER_DATE", TimestampType(), True),
    StructField("ORDER_CUSTOMER_ID", IntegerType(), True),
    StructField("ORDER_STATUS", StringType(), True)
])

df = spark.createDataFrame(data, schema)

# Write Spark DataFrame directly to Snowflake
df.write \
    .format("snowflake") \
    .option("sfURL", "*****-*****.snowflakecomputing.com") \
    .option("sfUser", "GLUE_DEMO_USER") \
    .option("sfPassword", "*********") \
    .option("sfDatabase", "GLUE_DATA") \
    .option("sfSchema", "ORDERS") \
    .option("sfWarehouse", "COMPUTE_WH") \
    .option("dbtable", "ORDERS") \
    .mode("append") \
    .save()

job.commit()