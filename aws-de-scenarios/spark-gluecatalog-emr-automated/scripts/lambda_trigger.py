"""
Lambda function — triggered by S3 PUT event on raw/airlines/
Launches a transient EMR cluster to run the airlines_analytics.py Spark job.
Cluster auto-terminates after the job completes.
"""

import boto3
import os

EMR_CLIENT = boto3.client("emr", region_name="ap-south-1")

# --- Config (set these as Lambda environment variables) ---
BUCKET          = os.environ["BUCKET"]           # sanjay-de-bucket-2026
SPARK_SCRIPT    = os.environ["SPARK_SCRIPT"]     # s3://sanjay-de-bucket-2026/emr-scripts/airlines_analytics.py
EMR_ROLE        = os.environ["EMR_ROLE"]         # EMR_DefaultRole
EMR_EC2_ROLE    = os.environ["EMR_EC2_ROLE"]     # EMR_EC2_DefaultRole
SUBNET_ID       = os.environ["SUBNET_ID"]        # your subnet id
LOG_URI         = f"s3://{os.environ['BUCKET']}/emr-logs/"


def lambda_handler(event, context):
    # Only trigger on the expected S3 key prefix
    record = event["Records"][0]["s3"]
    key = record["object"]["key"]

    if not key.startswith("raw/airlines/"):
        print(f"Skipping — unexpected key: {key}")
        return

    print(f"New file detected: s3://{BUCKET}/{key} — launching EMR cluster")

    response = EMR_CLIENT.run_job_flow(
        Name="airlines-analytics-transient",
        ReleaseLabel="emr-6.15.0",
        Applications=[{"Name": "Spark"}, {"Name": "Hadoop"}],
        Instances={
            "InstanceGroups": [
                {
                    "Name": "Primary",
                    "Market": "ON_DEMAND",
                    "InstanceRole": "MASTER",
                    "InstanceType": "m5.xlarge",
                    "InstanceCount": 1,
                },
                {
                    "Name": "Core",
                    "Market": "ON_DEMAND",
                    "InstanceRole": "CORE",
                    "InstanceType": "m5.xlarge",
                    "InstanceCount": 2,
                },
            ],
            "KeepJobFlowAliveWhenNoSteps": False,   # auto-terminate after steps complete
            "TerminationProtected": False,
            "Ec2SubnetId": SUBNET_ID,
        },
        Steps=[
            {
                "Name": "airlines-analytics",
                "ActionOnFailure": "TERMINATE_CLUSTER",
                "HadoopJarStep": {
                    "Jar": "command-runner.jar",
                    "Args": [
                        "spark-submit",
                        "--master", "yarn",
                        "--deploy-mode", "cluster",
                        "--conf", "spark.sql.catalogImplementation=hive",
                        "--conf", "hive.metastore.client.factory.class=com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory",
                        SPARK_SCRIPT,
                    ],
                },
            }
        ],
        LogUri=LOG_URI,
        ServiceRole=EMR_ROLE,
        JobFlowRole=EMR_EC2_ROLE,
        AutoTerminationPolicy={"IdleTimeout": 3600},
        Configurations=[
            {
                "Classification": "spark-hive-site",
                "Properties": {
                    "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
                },
            }
        ],
        Tags=[{"Key": "Project", "Value": "airlines-analytics"}],
    )

    cluster_id = response["JobFlowId"]
    print(f"EMR cluster launched: {cluster_id}")
    return {"cluster_id": cluster_id}
