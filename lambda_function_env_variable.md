# Lambda Function - Environment Variables

---

## Table of Contents

1. [What are Environment Variables](#1-what-are-environment-variables)
2. [Why Use Environment Variables in Lambda](#2-why-use-environment-variables-in-lambda)
3. [How to Set Environment Variables in Lambda](#3-how-to-set-environment-variables-in-lambda)
4. [How to Read Environment Variables in Python](#4-how-to-read-environment-variables-in-python)
5. [What We Are Building](#5-what-we-are-building)
6. [Architecture](#6-architecture)
7. [Step 1 - Create Two S3 Buckets](#7-step-1---create-two-s3-buckets)
8. [Step 2 - Create Lambda Function](#8-step-2---create-lambda-function)
9. [Step 3 - Attach S3 Permission to Lambda Role](#9-step-3---attach-s3-permission-to-lambda-role)
10. [Step 4 - Set Environment Variable](#10-step-4---set-environment-variable)
11. [Step 5 - Lambda Code with Environment Variable](#11-step-5---lambda-code-with-environment-variable)
12. [Step 6 - Add S3 Event Trigger](#12-step-6---add-s3-event-trigger)
13. [Step 7 - Test End to End](#13-step-7---test-end-to-end)
14. [Step 8 - Verify in CloudWatch Logs](#14-step-8---verify-in-cloudwatch-logs)
15. [How the Target Key is Built](#15-how-the-target-key-is-built)
16. [What Happens for Different Source Files](#16-what-happens-for-different-source-files)

---

## 1. What are Environment Variables

Environment variables are **key-value pairs** stored outside your code that your application can read at runtime.

```
Key:   TARGET_BUCKET
Value: lambda-function-demo-s3eventnotification-target
```

They are set in the Lambda configuration, not inside the Python code. Your code reads them using `os.environ`.

---

## 2. Why Use Environment Variables in Lambda

**The problem with hardcoding:**

```python
# BAD - hardcoded
target_bucket = 'lambda-function-demo-s3eventnotification-target'
```

| Problem | Description |
|---|---|
| Not reusable | Same code cannot be used for dev, staging, prod without editing |
| Security risk | Sensitive values like passwords visible in source code |
| Hard to maintain | Changing a value requires redeploying the entire function |
| Not scalable | Every environment needs a separate code change |

**With environment variables:**

```python
# GOOD - from environment variable
target_bucket = os.environ['TARGET_BUCKET']
```

| Benefit | Description |
|---|---|
| Reusable | Same code works across dev, staging, prod - just change the variable |
| Secure | Sensitive values kept out of source code |
| Easy to maintain | Change value in console without touching or redeploying code |
| Scalable | Deploy same code to multiple environments with different configs |

---

## 3. How to Set Environment Variables in Lambda

- Lambda Console → your function → **Configuration** tab
- Click **Environment variables** → **Edit**
- Click **Add environment variable**
- Enter Key and Value:

```
Key:   TARGET_BUCKET
Value: lambda-function-demo-s3eventnotification-target
```

- Click **Save**

You can add as many environment variables as needed. Common ones in data engineering:

| Key | Example Value |
|---|---|
| `TARGET_BUCKET` | `my-target-bucket` |
| `DATABASE_NAME` | `my_glue_database` |
| `GLUE_JOB_NAME` | `my-etl-job` |
| `SNS_TOPIC_ARN` | `arn:aws:sns:ap-south-1:123456789012:alerts` |
| `ENVIRONMENT` | `dev` / `staging` / `prod` |

---

## 4. How to Read Environment Variables in Python

```python
import os

# Read a required variable - raises KeyError if not set
target_bucket = os.environ['TARGET_BUCKET']

# Read with a default fallback - does not raise error if not set
target_bucket = os.environ.get('TARGET_BUCKET', 'default-bucket-name')
```

**Difference between the two:**

| | `os.environ['KEY']` | `os.environ.get('KEY', 'default')` |
|---|---|---|
| Key not set | Raises `KeyError` - function fails | Returns default value |
| Key is set | Returns the value | Returns the value |
| Best for | Required config - should fail if missing | Optional config with a sensible default |

> For critical config like bucket names, use `os.environ['KEY']` so the function fails loudly if the variable is missing rather than silently using a wrong default.

---

## 5. What We Are Building

A Lambda function that:
- Triggers automatically when any file lands in source S3 bucket
- Reads the source bucket and file key from the S3 event
- Reads the target bucket name from an **environment variable**
- Copies the file to the target bucket
- Maintains a date based folder hierarchy `year=YYYY/month=MM/day=DD/` in the target bucket

---

## 6. Architecture

```
File uploaded/copied to:
s3://lambda-function-demo-s3eventnotification-source/raw/orders/orders.csv
        ↓
S3 Event Notification (s3:ObjectCreated:*)
        ↓
Lambda Triggered
        ↓
Reads source bucket and key from S3 event
Reads target bucket from environment variable TARGET_BUCKET
        ↓
Copies file to target bucket with date hierarchy:
s3://lambda-function-demo-s3eventnotification-target/raw/orders/year=2026/month=04/day=22/orders.csv
```

---

## 7. Step 1 - Create Two S3 Buckets

- Source bucket: `lambda-function-demo-s3eventnotification-source`
- Target bucket: `lambda-function-demo-s3eventnotification-target`

---

## 8. Step 2 - Create Lambda Function

- Lambda Console → **Create function**
- Name: `s3-copy-with-env-variable`
- Runtime: **Python 3.14**
- Execution role: Create a new role with basic Lambda permissions
- Click **Create function**

---

## 9. Step 3 - Attach S3 Permission to Lambda Role

- Lambda Console → Configuration → **Permissions** → click the role name
- IAM → Add permissions → Attach policies
- Attach `AmazonS3FullAccess`

---

## 10. Step 4 - Set Environment Variable

- Lambda Console → your function → **Configuration** tab
- Click **Environment variables** → **Edit**
- Click **Add environment variable**
- Enter:

```
Key:   TARGET_BUCKET
Value: lambda-function-demo-s3eventnotification-target
```

- Click **Save**

---

## 11. Step 5 - Lambda Code with Environment Variable

```python
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    print(event)

    # Read target bucket from environment variable
    target_bucket = os.environ['TARGET_BUCKET']

    # Extract source bucket and key from S3 event
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    source_key = event['Records'][0]['s3']['object']['key']

    print(f"Source: s3://{source_bucket}/{source_key}")
    print(f"Target bucket from env variable: {target_bucket}")

    # Build date hierarchy from current date
    now = datetime.utcnow()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')

    # Extract just the file name from the source key
    file_name = source_key.split('/')[-1]

    # Extract the prefix (folder path) from the source key excluding file name
    # Example: raw/orders/orders.csv → prefix = raw/orders
    prefix = '/'.join(source_key.split('/')[:-1])

    # Build target key with date hierarchy
    # Example: raw/orders/year=2026/month=04/day=22/orders.csv
    target_key = f"{prefix}/year={year}/month={month}/day={day}/{file_name}"

    print(f"Target: s3://{target_bucket}/{target_key}")

    # Copy object from source to target
    s3.copy_object(
        CopySource={
            'Bucket': source_bucket,
            'Key': source_key
        },
        Bucket=target_bucket,
        Key=target_key
    )

    print(f"File copied successfully")

    return {
        'statusCode': 200,
        'body': f"Copied to s3://{target_bucket}/{target_key}"
    }
```

Click **Deploy**.

---

## 12. Step 6 - Add S3 Event Trigger

- Lambda Console → your function → **+ Add trigger**
- Select **S3**
- Bucket: `lambda-function-demo-s3eventnotification-source`
- Event types: **s3:ObjectCreated:***
- Prefix filter: `raw/` *(optional - only trigger for files under raw/)*
- Suffix filter: `.csv` *(optional - only trigger for CSV files)*
- Click **Add**

---

## 13. Step 7 - Test End to End

**Upload a new file:**
```bash
aws s3 cp orders.csv s3://lambda-function-demo-s3eventnotification-source/raw/orders/orders.csv
```

**Or copy an existing S3 file:**
```bash
aws s3 cp s3://lambda-function-demo-s3eventnotification-source/raw/orders/orders.csv \
          s3://lambda-function-demo-s3eventnotification-source/raw/orders/orders.csv \
          --metadata-directive REPLACE
```

**Check target bucket:**
```bash
aws s3 ls s3://lambda-function-demo-s3eventnotification-target/raw/orders/ --recursive
```

**Expected output:**
```
2026-04-22  raw/orders/year=2026/month=04/day=22/orders.csv
```

---

## 14. Step 8 - Verify in CloudWatch Logs

- Lambda Console → **Monitor** tab → **View CloudWatch logs**
- You should see:

```
Source: s3://lambda-function-demo-s3eventnotification-source/raw/orders/orders.csv
Target bucket from env variable: lambda-function-demo-s3eventnotification-target
Target: s3://lambda-function-demo-s3eventnotification-target/raw/orders/year=2026/month=04/day=22/orders.csv
File copied successfully
```

---

## 15. How the Target Key is Built

```
Source key:   raw/orders/orders.csv

Split by /:   ['raw', 'orders', 'orders.csv']

file_name:    orders.csv         ← last element
prefix:       raw/orders         ← everything except last element

date:         year=2026/month=04/day=22

target_key:   raw/orders/year=2026/month=04/day=22/orders.csv
```

---

## 16. What Happens for Different Source Files

| Source Key | Target Key |
|---|---|
| `raw/orders/orders.csv` | `raw/orders/year=2026/month=04/day=22/orders.csv` |
| `raw/sales/sales_data.csv` | `raw/sales/year=2026/month=04/day=22/sales_data.csv` |
| `raw/customers/customers.csv` | `raw/customers/year=2026/month=04/day=22/customers.csv` |

The date hierarchy is automatically inserted just before the file name, preserving the original folder structure.

---

## Hardcoded vs Environment Variable - Side by Side

| | Hardcoded | Environment Variable |
|---|---|---|
| Target bucket in code | `'lambda-function-demo-...-target'` | `os.environ['TARGET_BUCKET']` |
| Change target bucket | Edit code + redeploy | Change value in console, no redeploy |
| Use same code for dev/prod | No, need separate code | Yes, just change the variable |
| Visible in source code | Yes | No |
| Best practice | No | Yes |
