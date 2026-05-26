import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, TimestampType
from datetime import datetime

args = getResolvedOptions(sys.argv, ["JOB_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args["JOB_NAME"], args)

data = [
    (1, datetime.strptime("2013-07-25 00:00:00.0", "%Y-%m-%d %H:%M:%S.%f"), 11599, "CLOSED")
]

schema = StructType([
    StructField("ORDER_ID", IntegerType(), True),
    StructField("ORDER_DATE", TimestampType(), True),
    StructField("ORDER_CUSTOMER_ID", IntegerType(), True),
    StructField("ORDER_STATUS", StringType(), True)
])

df = spark.createDataFrame(data, schema)

dyf = DynamicFrame.fromDF(df, glueContext, "orders_dyf")

glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="snowflake",
    connection_options={
        "connectionName": "Snowflake connection",
        "dbtable": "ORDERS",
        "sfDatabase": "GLUE_DATA",
        "sfSchema": "ORDERS",
        "sfWarehouse": "COMPUTE_WH"
    }
)

job.commit()