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
job.init(args['JOB_NAME'], args)

source_path = "s3://<bucket_name>/source_files/orders/order_big_for_scaleout_demo.csv"
target_path = "s3://<bucket_name>/target_files/big_file_demo/"

# Read source
df = spark.read.option("header", True).csv(source_path)

# Cross join to explode data size and force scale-out
# Select only left side columns to avoid duplicate column name error
df_result = df.alias("a").crossJoin(df.alias("b")).select("a.*")

# Write to parquet
df_result.write.mode("overwrite").parquet(target_path)

job.commit()
