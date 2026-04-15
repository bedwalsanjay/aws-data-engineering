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

## Module 4: S3 - Simple Storage Service

### 4.1 Core Concepts - Buckets, Objects, Keys
### 4.2 Storage Classes and When to Use Each
### 4.3 Bucket Policies and Access Control
### 4.4 Data Lake Folder Structure *(covered in depth in Module 23)*
### 4.5 S3 Event Notifications
### 4.6 Versioning and Lifecycle Rules
### 4.7 Partitioning Strategy *(covered in depth in Module 23)*

---

## Module 5: EC2 - Elastic Compute Cloud

### 5.1 Instance Types for Data Engineering
### 5.2 Launching an EC2 Instance
### 5.3 Connecting via SSH
### 5.4 User Data - Bootstrap Scripts on Launch
### 5.5 EC2 Instance Profile - Attaching IAM Role
### 5.6 EBS - Elastic Block Store
### 5.7 Security Groups - Inbound and Outbound Rules

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

## Module 12: EMR - Elastic MapReduce

### 12.1 EMR Components - Master, Core, Task Nodes
### 12.2 Launching an EMR Cluster
### 12.3 Submitting Spark Jobs as EMR Steps
### 12.4 EMR with Airflow - Industry Pattern
### 12.5 EMR Serverless
### 12.6 Storage Options - S3, HDFS, EBS

---

## Module 13: SNS and SQS

### 13.1 SNS - Pub/Sub Notifications
### 13.2 SQS - Message Queues and Decoupling
### 13.3 Dead Letter Queues (DLQ)
---

## Module 14: Secrets Manager

### 14.1 Storing Credentials Securely
### 14.2 Retrieving Secrets in Code
### 14.3 Secrets Manager vs SSM Parameter Store

---

## Module 15: CloudFormation and CDK

### 15.1 CloudFormation - YAML/JSON Templates
### 15.2 AWS CDK - Infrastructure as Python Code
### 15.3 CDK Project Structure and Commands
### 15.4 CDK vs CloudFormation - When to Use Which

---

## Module 16: CloudWatch

### 16.1 Logs - Lambda, Glue, EMR
### 16.2 Metrics and Dashboards
### 16.3 Alarms - Alert on Pipeline Failures

---

## Module 17: Step Functions

### 17.1 State Machines for Workflow Orchestration
### 17.2 Orchestrating Data Pipelines with Step Functions
### 17.3 Step Functions vs Airflow

---

## Module 18: EventBridge

### 18.1 Scheduling Jobs with Cron Rules
### 18.2 Reacting to AWS Service Events
---

## Module 19: DynamoDB

### 19.1 Use Cases in Data Engineering
### 19.2 Core Concepts - Tables, Items, Partition Key, Sort Key
### 19.3 Storing Pipeline Metadata and Run History
---

## Module 20: Git, GitHub and CI/CD

### 20.1 Git Basics for Data Engineers
### 20.2 Branching Strategy
### 20.3 .gitignore Best Practices
### 20.4 GitHub Actions - Automated Deploy to AWS
### 20.5 Storing AWS Credentials as GitHub Secrets

---

## Module 21: Docker

### 21.1 Why Docker for Data Engineering
### 21.2 Core Docker Commands
### 21.3 Writing a Dockerfile
### 21.4 Docker Compose - Local Dev Stack
---

## Module 22: Apache Airflow

### 22.1 Core Concepts - DAG, Task, Operator, Sensor, Hook
### 22.2 Running Airflow Locally with Docker
### 22.3 Writing a DAG
### 22.4 AWS Operators - Glue, EMR, S3, Redshift
### 22.5 Amazon MWAA - Managed Airflow on AWS

---

## Module 23: Data Engineering Concepts and Best Practices

### 23.1 Data Lake Architecture - Raw / Bronze / Silver / Gold Layers
### 23.2 Partitioning Strategy for Performance and Cost
### 23.3 Batch vs Streaming - When to Use Which
### 23.4 Data Pipeline Design Patterns
### 23.5 Idempotency - Designing Pipelines That Can Safely Re-run
### 23.6 Data Quality and Validation
### 23.7 Schema Evolution and Handling Breaking Changes
### 23.8 File Formats - CSV vs JSON vs Parquet vs ORC
### 23.9 Slowly Changing Dimensions (SCD) - Type 1, 2, 3
### 23.10 Pipeline Monitoring, Alerting and Observability

---

## Module 24: Projects

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
