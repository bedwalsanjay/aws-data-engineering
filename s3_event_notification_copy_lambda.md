# S3 Event Notification - Copy Lambda Demo

---

## Table of Contents

1. [What is S3 Event Notification](#1-what-is-s3-event-notification)
2. [What We Are Building](#2-what-we-are-building)
3. [Architecture](#3-architecture)
4. [Step 1 - Create Two S3 Buckets](#4-step-1---create-two-s3-buckets)
5. [Step 2 - Create Lambda Function](#5-step-2---create-lambda-function)
6. [Step 3 - Attach S3 Permission to Lambda Role](#6-step-3---attach-s3-permission-to-lambda-role)
7. [Step 4 - Lambda Code](#7-step-4---lambda-code)
8. [Step 5 - Add S3 Event Trigger](#8-step-5---add-s3-event-trigger)
9. [Step 6 - Test End to End](#9-step-6---test-end-to-end)
10. [Step 7 - Verify in CloudWatch Logs](#10-step-7---verify-in-cloudwatch-logs)
11. [How the Target Key is Built](#11-how-the-target-key-is-built)
12. [What Happens for Different Source Files](#12-what-happens-for-different-source-files)

---

## 1. What is S3 Event Notification

S3 Event Notification is a feature that allows S3 to **automatically notify other AWS services** when something happens inside a bucket - like a file being uploaded, copied, or deleted.

Instead of writing a script that keeps checking S3 every few minutes for new files, S3 Event Notification pushes the event to your target service the moment it happens.

```
Without S3 Event Notification:
Your script → polls S3 every 5 minutes → checks for new files → processes if found
Problem: wasteful, delayed, runs even when nothing is there

With S3 Event Notification:
File lands in S3 → S3 instantly pushes event → Lambda/SQS/SNS reacts immediately
Benefit: real time, no polling, cost efficient
```

### Supported Event Types

| Event Type | When it triggers |
|---|---|
| `s3:ObjectCreated:Put` | File uploaded from local machine via CLI, boto3, or console |
| `s3:ObjectCreated:Copy` | File copied from one S3 location to another |
| `s3:ObjectCreated:Post` | File uploaded via browser HTML form directly to S3 |
| `s3:ObjectCreated:CompleteMultipartUpload` | Large file multipart upload completes |
| `s3:ObjectCreated:*` | All of the above - catches every file creation event |
| `s3:ObjectRemoved:*` | File deleted |
| `s3:ObjectRestore:*` | Glacier object restore initiated or completed |

### Supported Destinations

S3 Event Notification can send events to:

| Destination | Use Case |
|---|---|
| **Lambda** | Run custom code immediately on file arrival |
| **SQS** | Queue events for reliable processing, buffer between S3 and Lambda |
| **SNS** | Fan out notifications to multiple subscribers |

### Prefix and Suffix Filters

You can filter which files trigger the notification:

- **Prefix filter** - only trigger for files under a specific folder e.g. `raw/orders/`
- **Suffix filter** - only trigger for specific file types e.g. `.csv`

```
Prefix: raw/orders/
Suffix: .csv

Only triggers for:
s3://bucket/raw/orders/orders.csv      ✅
s3://bucket/raw/orders/data.csv        ✅
s3://bucket/raw/sales/sales.csv        ❌ different prefix
s3://bucket/raw/orders/data.json       ❌ different suffix
```

### What the S3 Event Looks Like

When S3 triggers Lambda, it passes this JSON as the `event` parameter:

```json
{
    "Records": [
        {
            "s3": {
                "bucket": {
                    "name": "lambda-function-demo-s3eventnotification-source"
                },
                "object": {
                    "key": "raw/orders/orders.csv",
                    "size": 1024
                }
            }
        }
    ]
}
```

This is how Lambda knows which file was uploaded and from which bucket.

---

## 2. What We Are Building

A Lambda function that:
- Triggers automatically when any file lands in source S3 bucket
- Reads the source bucket and file key from the S3 event
- Copies the file to a target bucket
- Maintains a date based folder hierarchy `year=YYYY/month=MM/day=DD/` in the target bucket

---

## 3. Architecture

```
File uploaded/copied to:
s3://lambda-function-demo-s3eventnotification-source/raw/orders/orders.csv
        ↓
S3 Event Notification (s3:ObjectCreated:*)
        ↓
Lambda Triggered
        ↓
Reads source bucket and key from event
        ↓
Copies file to target bucket with date hierarchy:
s3://lambda-function-demo-s3eventnotification-target/raw/orders/year=2026/month=04/day=22/orders.csv
```

---

## 4. Step 1 - Create Two S3 Buckets

- Source bucket: `lambda-function-demo-s3eventnotification-source`
- Target bucket: `lambda-function-demo-s3eventnotification-target`

---

## 5. Step 2 - Create Lambda Function

- Lambda Console → **Create function**
- Name: `s3-copy-with-hierarchy`
- Runtime: **Python 3.14**
- Execution role: Create a new role with basic Lambda permissions
- Click **Create function**

---

## 6. Step 3 - Attach S3 Permission to Lambda Role

- Lambda Console → Configuration → **Permissions** → click the role name
- IAM → Add permissions → Attach policies
- Attach `AmazonS3FullAccess`

---

## 7. Step 4 - Lambda Code

```python
import boto3
from datetime import datetime

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    print(event)

    # Hardcoded target bucket
    target_bucket = 'lambda-function-demo-s3eventnotification-target'

    # Extract source bucket and key from S3 event
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    source_key = event['Records'][0]['s3']['object']['key']

    print(f"Source: s3://{source_bucket}/{source_key}")

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

## 8. Step 5 - Add S3 Event Trigger

- Lambda Console → your function → **+ Add trigger**
- Select **S3**
- Bucket: `lambda-function-demo-s3eventnotification-source`
- Event types: **s3:ObjectCreated:***
- Prefix filter: `raw/` *(optional - only trigger for files under raw/)*
- Suffix filter: `.csv` *(optional - only trigger for CSV files)*
- Click **Add**

---

## 9. Step 6 - Test End to End

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

## 10. Step 7 - Verify in CloudWatch Logs

- Lambda Console → **Monitor** tab → **View CloudWatch logs**
- You should see:

```
Source: s3://lambda-function-demo-s3eventnotification-source/raw/orders/orders.csv
Target: s3://lambda-function-demo-s3eventnotification-target/raw/orders/year=2026/month=04/day=22/orders.csv
File copied successfully
```

---

## 11. How the Target Key is Built

```
Source key:   raw/orders/orders.csv

Split by /:   ['raw', 'orders', 'orders.csv']

file_name:    orders.csv         ← last element
prefix:       raw/orders         ← everything except last element

date:         year=2026/month=04/day=22

target_key:   raw/orders/year=2026/month=04/day=22/orders.csv
```

---

## 12. What Happens for Different Source Files

| Source Key | Target Key |
|---|---|
| `raw/orders/orders.csv` | `raw/orders/year=2026/month=04/day=22/orders.csv` |
| `raw/sales/sales_data.csv` | `raw/sales/year=2026/month=04/day=22/sales_data.csv` |
| `raw/customers/customers.csv` | `raw/customers/year=2026/month=04/day=22/customers.csv` |

The date hierarchy is automatically inserted just before the file name, preserving the original folder structure.
