# -*- coding: utf-8 -*-
"""
Usecase: E-Commerce Order Analytics (AWS Glue ETL Job)
- Reads raw orders table from Glue Data Catalog (external table on S3 CSV)
- Computes: revenue by category, top 10 products, daily order trends
- Writes results back to S3 as Parquet (curated layer)
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import col, sum as _sum, count, round as _round, to_date

args = getResolvedOptions(sys.argv, ["JOB_NAME"])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

S3_OUTPUT = "s3://sanjay-de-bucket-2026/curated/order_analytics/"

# --- Read from Glue Data Catalog ---
orders_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="ecommerce_db",
    table_name="orders"
)
orders = orders_dyf.toDF()
orders = orders.withColumn("order_date", to_date(col("order_date"), "yyyy-MM-dd"))

# --- 1. Revenue by category ---
revenue_by_category = (
    orders.groupBy("category")
    .agg(
        _round(_sum(col("quantity") * col("unit_price")), 2).alias("total_revenue"),
        count("order_id").alias("total_orders")
    )
    .orderBy(col("total_revenue").desc())
)

# --- 2. Top 10 products by revenue ---
top_products = (
    orders.groupBy("product_id", "product_name")
    .agg(_round(_sum(col("quantity") * col("unit_price")), 2).alias("revenue"))
    .orderBy(col("revenue").desc())
    .limit(10)
)

# --- 3. Daily order trends ---
daily_trends = (
    orders.groupBy("order_date")
    .agg(
        count("order_id").alias("num_orders"),
        _round(_sum(col("quantity") * col("unit_price")), 2).alias("daily_revenue")
    )
    .orderBy("order_date")
)

# --- Print summaries to logs ---
print("\n=== Revenue by Category ===")
revenue_by_category.show(truncate=False)

print("=== Top 10 Products ===")
top_products.show(truncate=False)

print("=== Daily Trends (first 10 days) ===")
daily_trends.show(10, truncate=False)

# --- Write results to S3 as CSV ---
revenue_by_category.write.mode("overwrite").option("header", "true").csv(S3_OUTPUT + "revenue_by_category/")
top_products.write.mode("overwrite").option("header", "true").csv(S3_OUTPUT + "top_products/")
daily_trends.write.mode("overwrite").option("header", "true").csv(S3_OUTPUT + "daily_trends/")

print("\nDone. Results written to:", S3_OUTPUT)
job.commit()
