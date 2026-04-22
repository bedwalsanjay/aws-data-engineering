# AWS Data Engineering - Course Index

> This document serves as a course roadmap. Follow the sections in order for a structured learning path.

---

## Prerequisites

Before starting this course, learners are expected to have a basic understanding of the following:

### Python
- Variables, data types, loops, conditionals
- Functions and modules
- File handling - reading and writing CSV, JSON
- Working with libraries like `pandas` and `boto3`
- Basic understanding of OOP (classes and objects)
- Running Python scripts from the terminal

### SQL
- SELECT, WHERE, GROUP BY, ORDER BY, HAVING
- JOINs - INNER, LEFT, RIGHT
- Aggregation functions - COUNT, SUM, AVG, MIN, MAX
- Subqueries and CTEs (Common Table Expressions)
- Basic DDL - CREATE TABLE, INSERT, UPDATE, DELETE
- Understanding of primary keys, foreign keys, and indexes

### General
- Comfortable using a terminal or command prompt
- Basic understanding of what a database is
- Familiarity with any code editor (VS Code recommended)

> No prior AWS or cloud experience is required. Everything AWS-related is covered from scratch in this course.

---

## Module 1: AWS Account Setup

### 1.1 Creating a Free Tier Account
### 1.2 Setting Up AWS Budget and Billing Alerts
### 1.3 Checking Bills and Cost Explorer
### 1.4 Enabling MFA (Multi-Factor Authentication)

---

## Module 2: IAM - Identity and Access Management

### 2.1 IAM Users - Why Not Use Root Account
### 2.2 IAM Groups - Managing Permissions at Scale
### 2.3 IAM Roles - Permissions for AWS Services
### 2.4 IAM Policies - JSON Permission Documents
### 2.5 IAM Best Practices Summary

---

## Module 3: AWS CLI

### 3.1 Installation (Windows / Linux / Mac)
### 3.2 Configuration and Profiles
### 3.3 Common CLI Commands for Data Engineering

---

## Module 4: Boto3 Python SDK

### 4.1 What is Boto3 and Why it is Needed
### 4.2 Python and Pip Setup in CloudShell
### 4.3 Installation and Authentication
### 4.4 Boto3 Client - How to Connect to AWS Services
### 4.5 S3 Operations with Boto3
### 4.6 Run and Monitor a Glue Job with Boto3
### 4.7 Other Useful Boto3 Examples - Lambda, SNS, DynamoDB, Secrets Manager

---

## Module 5: S3 - Simple Storage Service

### 5.1 Core Concepts - Buckets, Objects, Keys
### 5.2 Storage Classes and When to Use Each
### 5.3 Bucket Policies and Access Control
### 5.4 Data Lake Folder Structure *(covered in depth in Module 24)*
### 5.5 S3 Event Notifications
### 5.6 Versioning and Lifecycle Rules
### 5.7 Partitioning Strategy *(covered in depth in Module 24)*

---

## Module 6: Lambda

### 6.1 Key Concepts - Triggers, Handlers, Runtimes
### 6.2 Lambda Use Cases in Data Pipelines
### 6.3 Writing a Basic Lambda Function
### 6.4 Lambda Layers - Packaging External Libraries
### 6.5 Environment Variables
### 6.6 Concurrency, Timeouts and Limits

---

## Module 7: AWS Glue

### 7.1 Glue Components Overview
### 7.2 Glue Data Catalog - Central Metadata Store
### 7.3 Glue Crawlers - Auto Schema Discovery
### 7.4 Glue ETL Jobs - PySpark Transformations
### 7.5 Glue Job Types - Spark, Python Shell, Streaming
### 7.6 Glue Workflows - Chaining Jobs and Crawlers
### 7.7 Glue vs EMR - When to Use Which

---

## Module 8: Athena

### 8.1 What is Athena - Serverless SQL on S3
### 8.2 Setup and Output Location
### 8.3 Creating External Tables
### 8.4 Optimizing Query Cost - Parquet, Partitions, Compression
### 8.5 Athena Workgroups
### 8.6 Querying Athena Programmatically

---

## Module 9: RDS - Relational Database Service

### 9.1 Supported Database Engines
### 9.2 RDS Free Tier Details
### 9.3 Creating an RDS Instance
### 9.4 Connecting to RDS
### 9.5 RDS as Source and Target in Data Pipelines
### 9.6 Snapshots and Automated Backups

---

## Module 10: Redshift

### 10.1 Redshift Architecture - Leader and Compute Nodes
### 10.2 Redshift vs RDS - OLAP vs OLTP
### 10.3 Loading Data - COPY Command and Glue
### 10.4 Redshift Spectrum - Query S3 from Redshift
### 10.5 Distribution Styles
### 10.6 Sort Keys
### 10.7 Redshift Serverless

---

## Module 11: Kinesis

### 11.1 Kinesis Services Overview
### 11.2 Kinesis Data Streams - Shards, Records, Partitions
### 11.3 Kinesis Data Firehose - Delivery to S3 / Redshift
### 11.4 Kinesis vs SQS vs SNS - Choosing the Right Service

---

## Module 12: EC2 - Elastic Compute Cloud

### 12.1 Instance Types for Data Engineering
### 12.2 Launching an EC2 Instance
### 12.3 Connecting via SSH
### 12.4 User Data - Bootstrap Scripts on Launch
### 12.5 EC2 Instance Profile - Attaching IAM Role
### 12.6 EBS - Elastic Block Store
### 12.7 Security Groups - Inbound and Outbound Rules

---

## Module 13: EMR - Elastic MapReduce

### 13.1 EMR Components - Master, Core, Task Nodes
### 13.2 Launching an EMR Cluster
### 13.3 Submitting Spark Jobs as EMR Steps
### 13.4 EMR with Airflow - Industry Pattern
### 13.5 EMR Serverless
### 13.6 Storage Options - S3, HDFS, EBS

---

## Module 14: SNS and SQS

### 14.1 SNS - Pub/Sub Notifications
### 14.2 SQS - Message Queues and Decoupling
### 14.3 Dead Letter Queues (DLQ)

---

## Module 15: Secrets Manager

### 15.1 Storing Credentials Securely
### 15.2 Retrieving Secrets in Code
### 15.3 Secrets Manager vs SSM Parameter Store

---

## Module 16: CloudFormation and CDK

### 16.1 CloudFormation - YAML/JSON Templates
### 16.2 AWS CDK - Infrastructure as Python Code
### 16.3 CDK Project Structure and Commands
### 16.4 CDK vs CloudFormation - When to Use Which

---

## Module 17: CloudWatch

### 17.1 Logs - Lambda, Glue, EMR
### 17.2 Metrics and Dashboards
### 17.3 Alarms - Alert on Pipeline Failures

---

## Module 18: Step Functions

### 18.1 State Machines for Workflow Orchestration
### 18.2 Orchestrating Data Pipelines with Step Functions
### 18.3 Step Functions vs Airflow

---

## Module 19: EventBridge

### 19.1 Scheduling Jobs with Cron Rules
### 19.2 Reacting to AWS Service Events

---

## Module 20: DynamoDB

### 20.1 Use Cases in Data Engineering
### 20.2 Core Concepts - Tables, Items, Partition Key, Sort Key
### 20.3 Storing Pipeline Metadata and Run History

---

## Module 21: Git, GitHub and CI/CD

### 21.1 Git Basics for Data Engineers
### 21.2 Branching Strategy
### 21.3 .gitignore Best Practices
### 21.4 GitHub Actions - Automated Deploy to AWS
### 21.5 Storing AWS Credentials as GitHub Secrets

---

## Module 22: Docker

### 22.1 Why Docker for Data Engineering
### 22.2 Core Docker Commands
### 22.3 Writing a Dockerfile
### 22.4 Docker Compose - Local Dev Stack

---

## Module 23: Apache Airflow

### 23.1 Core Concepts - DAG, Task, Operator, Sensor, Hook
### 23.2 Running Airflow Locally with Docker
### 23.3 Writing a DAG
### 23.4 AWS Operators - Glue, EMR, S3, Redshift
### 23.5 Amazon MWAA - Managed Airflow on AWS

---

## Module 24: Data Engineering Concepts and Best Practices

### 24.1 Data Lake Architecture - Raw / Bronze / Silver / Gold Layers
### 24.2 Partitioning Strategy for Performance and Cost
### 24.3 Batch vs Streaming - When to Use Which
### 24.4 Data Pipeline Design Patterns
### 24.5 Idempotency - Designing Pipelines That Can Safely Re-run
### 24.6 Data Quality and Validation
### 24.7 Schema Evolution and Handling Breaking Changes
### 24.8 File Formats - CSV vs JSON vs Parquet vs ORC
### 24.9 Slowly Changing Dimensions (SCD) - Type 1, 2, 3
### 24.10 Pipeline Monitoring, Alerting and Observability

---

## Module 25: Projects

### Project 1: Batch Processing Pipeline - AWS Glue and Redshift
- Ingest raw data from S3
- Transform with Glue PySpark
- Load into Redshift for analytics
- Schedule with EventBridge, monitor with CloudWatch

### Project 2: Event-Driven Pipeline - Lambda and Glue
- S3 file arrival triggers SQS → Lambda → Glue
- Track pipeline runs in DynamoDB
- Notify via SNS on success/failure

### Project 3: Real-Time Streaming Pipeline - Spark and Kinesis
- Ingest events via Kinesis Data Streams
- Process with Spark Structured Streaming on EMR
- Write micro-batch output to S3
- Query with Athena and Redshift Spectrum

### Project 4: Databricks on AWS
> *(Details to be decided)*

### Project 5: Snowflake Data Pipeline
> *(Details to be decided)*

---
