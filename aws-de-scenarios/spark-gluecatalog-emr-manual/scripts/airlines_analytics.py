# -*- coding: utf-8 -*-
"""
Usecase: Airlines Analytics (AWS EMR Spark Job)
- Reads flights table from Glue Data Catalog (external table on S3 CSV)
- Computes: delay stats by airline, top 10 busiest routes, daily flight trends
- Writes results back to S3 as CSV (curated layer)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, round as _round, sum as _sum, to_date, concat_ws

S3_OUTPUT = "s3://sanjay-de-bucket-2026/curated/airlines/"

spark = (
    SparkSession.builder
    .appName("AirlinesAnalytics")
    .config("hive.metastore.client.factory.class",
            "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# --- Read from Glue Data Catalog ---
flights = spark.sql("SELECT * FROM airlines_db.flights")
flights = flights.withColumn("flight_date", to_date(col("flight_date"), "yyyy-MM-dd"))

# --- 1. Delay stats by airline ---
delay_by_airline = (
    flights.filter(col("status") != "Cancelled")
    .groupBy("airline")
    .agg(
        _round(avg("departure_delay_mins"), 2).alias("avg_dep_delay_mins"),
        _round(avg("arrival_delay_mins"), 2).alias("avg_arr_delay_mins"),
        count("flight_id").alias("total_flights"),
        _round(
            count(col("status") == "Delayed") / count("flight_id") * 100, 2
        ).alias("delay_pct")
    )
    .orderBy(col("avg_dep_delay_mins").desc())
)

# --- 2. Top 10 busiest routes ---
top_routes = (
    flights.withColumn("route", concat_ws(" -> ", col("origin"), col("destination")))
    .groupBy("route")
    .agg(
        count("flight_id").alias("total_flights"),
        _round(avg("departure_delay_mins"), 2).alias("avg_dep_delay_mins")
    )
    .orderBy(col("total_flights").desc())
    .limit(10)
)

# --- 3. Daily flight trends ---
daily_trends = (
    flights.groupBy("flight_date")
    .agg(
        count("flight_id").alias("total_flights"),
        _round(avg("departure_delay_mins"), 2).alias("avg_dep_delay_mins"),
        count(col("status") == "Cancelled").alias("cancellations")
    )
    .orderBy("flight_date")
)

# --- Print summaries to logs ---
print("\n=== Delay Stats by Airline ===")
delay_by_airline.show(truncate=False)

print("=== Top 10 Busiest Routes ===")
top_routes.show(truncate=False)

print("=== Daily Flight Trends (first 10 days) ===")
daily_trends.show(10, truncate=False)

# --- Write results to S3 as CSV ---
delay_by_airline.write.mode("overwrite").option("header", "true").csv(S3_OUTPUT + "delay_by_airline/")
top_routes.write.mode("overwrite").option("header", "true").csv(S3_OUTPUT + "top_routes/")
daily_trends.write.mode("overwrite").option("header", "true").csv(S3_OUTPUT + "daily_trends/")

print("\nDone. Results written to:", S3_OUTPUT)
spark.stop()
