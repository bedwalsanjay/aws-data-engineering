# AWS Lambda - Complete Guide

---

## Table of Contents

1. [What is Lambda](#1-what-is-lambda)
2. [When to Use Lambda](#2-when-to-use-lambda)
3. [Memory and Ephemeral Storage Configuration](#3-memory-and-ephemeral-storage-configuration)
4. [Lambda Pricing](#4-lambda-pricing)
5. [Lambda Handler](#5-lambda-handler)
6. [Your First Lambda Function - Hello World](#6-your-first-lambda-function---hello-world)
7. [How to Test a Lambda Function](#7-how-to-test-a-lambda-function)
8. [S3 Event Trigger - Copy File Between Two Buckets](#8-s3-event-trigger---copy-file-between-two-buckets)
9. [Lambda Layers](#9-lambda-layers)
10. [Deploying Lambda via ZIP File](#10-deploying-lambda-via-zip-file)

---

## 1. What is Lambda

AWS Lambda is a **serverless compute service**. You write code, upload it, and AWS runs it. You never provision, manage, or think about servers.

- **Serverless** - no EC2 instances to launch, patch, or maintain
- **Event driven** - code runs only when triggered by an event
- **Auto scaling** - AWS automatically handles 1 request or 1 million requests
- **Multiple languages** - Python, Node.js, Java, Go, Ruby, C#, and more
- **Pay per use** - charged only when your code is actually running

```
Traditional Server:
You launch EC2 → pay 24/7 → code runs when called → pay even when idle

Lambda:
No server → code sleeps → event triggers it → runs → stops → you pay only for runtime
```

**Key Limits:**

| Property | Limit |
|---|---|
| Timeout | Maximum 15 minutes per invocation |
| Memory | 128 MB to 10,240 MB (10 GB) |
| Ephemeral storage (/tmp) | 512 MB to 10,240 MB (10 GB) |
| Deployment package | 50 MB zipped, 250 MB unzipped |
| Concurrency | 1000 per region (default) |

---

## 2. When to Use Lambda

Lambda is not for everything. Use it when your task is **short lived, event driven, and unpredictable in frequency**.

**Good use cases for Lambda:**

| Scenario | Example |
|---|---|
| File arrives in S3 | Validate, transform, move to another bucket |
| Scheduled jobs | Run a cleanup script every night at midnight |
| API backend | Handle HTTP requests via API Gateway |
| Database triggers | React to DynamoDB changes |
| Pipeline orchestration | Trigger Glue job when file lands in S3 |
| Notifications | Send SNS alert when EMR job fails |
| Data enrichment | Enrich streaming records from Kinesis |

**When NOT to use Lambda:**

| Scenario | Better Alternative |
|---|---|
| Job runs longer than 15 minutes | Glue, EMR, EC2 |
| Heavy data processing (GBs of data) | Glue, EMR, Spark |
| Always running web server | EC2, ECS, Fargate |
| Machine learning training | SageMaker |
| Long running batch jobs | AWS Batch, EMR |

---

## 3. Memory and Ephemeral Storage Configuration

### Memory

Memory in Lambda is unique - **CPU scales proportionally with memory**. There is no separate CPU setting.

```
128 MB memory  → least CPU  → slowest execution → cheapest
10,240 MB memory → most CPU → fastest execution → most expensive
```

You tune memory based on your workload:
- Simple API call or S3 copy → 128 MB is enough
- Pandas dataframe processing → 512 MB - 1 GB
- Large file processing → 2 GB - 4 GB
- Heavy computation → up to 10 GB

**Where to configure:**
- Lambda Console → your function → **Configuration** tab → **General configuration** → Edit → Memory

### Ephemeral Storage (/tmp)

Lambda provides a temporary disk space at `/tmp` during execution.

- Default: 512 MB
- Maximum: 10 GB
- Use it to download files, process them, then upload results to S3
- **Cleared after each invocation** - do not rely on it for persistent data

```python
import boto3
import os

def lambda_handler(event, context):
    s3 = boto3.client('s3')

    # Download file to /tmp
    s3.download_file('my-bucket', 'data.csv', '/tmp/data.csv')

    # Process the file
    with open('/tmp/data.csv', 'r') as f:
        data = f.read()

    # /tmp is cleared after this invocation ends
```

**Where to configure:**
- Lambda Console → Configuration → General configuration → Edit → Ephemeral storage

---

## 4. Lambda Pricing

Lambda pricing has two components:

### Requests
- First **1 million requests per month** → Free always (not just 12 months)
- After that → $0.20 per 1 million requests

### Duration
- Charged per **GB-second** (memory used × time running)
- First **400,000 GB-seconds per month** → Free always
- After that → $0.0000166667 per GB-second

**Practical example:**

```
Function memory: 512 MB (0.5 GB)
Execution time: 2 seconds
Invocations: 1 million per month

Duration cost:
0.5 GB × 2 sec × 1,000,000 = 1,000,000 GB-seconds
Free tier covers 400,000 GB-seconds
Billable: 600,000 GB-seconds × $0.0000166667 = $10.00/month

Request cost:
First 1M requests free
Total: ~$10/month
```

**Lambda is extremely cheap for low to medium workloads.** Most learning and small production workloads stay within free tier.

---

## 5. Lambda Handler

The handler is the **entry point** of your Lambda function. It is the function AWS calls when your Lambda is triggered.

**Handler format:**
```
filename.function_name
```

**Example:**
```python
# File name: handler.py

def lambda_handler(event, context):
    print("Lambda triggered")
    return {"statusCode": 200}
```

Handler setting in console: `handler.lambda_handler`
- `handler` → file name (handler.py)
- `lambda_handler` → function name inside the file

**The two parameters:**

| Parameter | What it contains |
|---|---|
| `event` | Input data passed to the function (S3 event, API request, scheduled event etc.) |
| `context` | Runtime information - function name, memory limit, remaining time, request ID |

```python
def lambda_handler(event, context):
    print(event)                              # input data
    print(context.function_name)             # name of this Lambda function
    print(context.memory_limit_in_mb)        # memory configured
    print(context.get_remaining_time_in_millis())  # time left before timeout
```

---

## 6. Your First Lambda Function - Hello World

**Step 1 - Create the function:**
- Lambda Console → **Create function**
- Select **Author from scratch**
- Function name: `hello-world`
- Runtime: **Python 3.12**
- Execution role: **Create a new role with basic Lambda permissions**
- Click **Create function**

**Step 2 - Write the code:**

In the inline code editor replace everything with:

```python
def lambda_handler(event, context):
    name = event.get('name', 'World')
    message = f"Hello, {name}!"
    print(message)
    return {
        'statusCode': 200,
        'body': message
    }
```

Click **Deploy** to save the code.

**Step 3 - Test it:**
- Click **Test** → **Create new test event**
- Event name: `test1`
- Event JSON:
```json
{
    "name": "Sanjay"
}
```
- Click **Save** → **Test**
- You should see:
```
Response:
{
  "statusCode": 200,
  "body": "Hello, Sanjay!"
}
```

---

## 7. How to Test a Lambda Function

There are 3 ways to test a Lambda function:

### Option 1 - Console Test (Quickest)
- Lambda Console → your function → **Test** tab
- Create a test event with sample JSON input
- Click **Test** → see response and logs inline
- Best for quick development and debugging

### Option 2 - AWS CLI
```bash
# Invoke and see response
aws lambda invoke \
  --function-name hello-world \
  --payload '{"name": "Sanjay"}' \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json
```

### Option 3 - boto3
```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-south-1')

response = lambda_client.invoke(
    FunctionName='hello-world',
    Payload=json.dumps({"name": "Sanjay"})
)

result = json.loads(response['Payload'].read())
print(result)
```

### Checking Logs After Test
- Lambda Console → **Monitor** tab → **View CloudWatch logs**
- Or directly: CloudWatch → Log groups → `/aws/lambda/hello-world`
- Every `print()` statement in your code appears here

---

## 8. S3 Event Trigger - Copy File Between Two Buckets

**Scenario:** A file lands in `source-bucket`. Lambda automatically copies it to `destination-bucket`.

---

**Step 1 - Create two S3 buckets:**
- `sanjay-source-bucket`
- `sanjay-destination-bucket`

---

**Step 2 - Create Lambda function:**
- Name: `s3-copy-trigger`
- Runtime: Python 3.12
- Create new role with basic Lambda permissions

---

**Step 3 - Add S3 permission to Lambda role:**

Lambda needs permission to read from source and write to destination.

- Lambda Console → Configuration → **Permissions** → click the role name
- IAM → Add permissions → Attach policies → `AmazonS3FullAccess`

Or create a specific policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::sanjay-source-bucket/*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::sanjay-destination-bucket/*"
        }
    ]
}
```

---

**Step 4 - Write the Lambda code:**

```python
import boto3

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Extract bucket name and file key from S3 event
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']

    destination_bucket = 'sanjay-destination-bucket'

    # Copy object from source to destination
    s3.copy_object(
        CopySource={'Bucket': source_bucket, 'Key': file_key},
        Bucket=destination_bucket,
        Key=file_key
    )

    print(f"Copied s3://{source_bucket}/{file_key} to s3://{destination_bucket}/{file_key}")

    return {'statusCode': 200, 'body': 'File copied successfully'}
```

Click **Deploy**.

---

**Step 5 - Add S3 Event Trigger:**
- Lambda Console → your function → **+ Add trigger**
- Select **S3**
- Bucket: `sanjay-source-bucket`
- Event type: **PUT** (triggers on file upload)
- Click **Add**

---

**Step 6 - Test end to end:**
```bash
# Upload a file to source bucket
aws s3 cp test.csv s3://sanjay-source-bucket/

# Check if it appeared in destination bucket
aws s3 ls s3://sanjay-destination-bucket/
```

---

**What happens under the hood:**
```
File uploaded to sanjay-source-bucket
        ↓
S3 generates an event
        ↓
Event triggers Lambda automatically
        ↓
Lambda reads source bucket and key from event
        ↓
Lambda copies file to sanjay-destination-bucket
        ↓
Logs written to CloudWatch
```

---

## 9. Lambda Layers

A Lambda Layer is a **reusable package of code or dependencies** that can be shared across multiple Lambda functions.

### Why Layers

Without layers:
```
Function A needs pandas → package pandas inside Function A zip
Function B needs pandas → package pandas inside Function B zip
Function C needs pandas → package pandas inside Function C zip
3 copies of pandas, 3 large deployment packages
```

With layers:
```
Create one pandas layer
Attach to Function A, B, C
Each function stays small
pandas maintained in one place
```

### When to use Layers
- External libraries not available in Lambda runtime (pandas, numpy, requests)
- Shared utility code used across multiple functions
- Large dependencies that would exceed deployment package size limit

### How to Create a Layer

**Step 1 - Package the library locally:**
```bash
mkdir python
pip install pandas -t python/
zip -r pandas-layer.zip python/
```

**Step 2 - Upload as a Layer:**
- Lambda Console → **Layers** (left sidebar) → **Create layer**
- Name: `pandas-layer`
- Upload the `pandas-layer.zip`
- Compatible runtime: Python 3.12
- Click **Create**

**Step 3 - Attach Layer to your function:**
- Lambda Console → your function → scroll down to **Layers**
- Click **Add a layer**
- Select **Custom layers** → select `pandas-layer`
- Click **Add**

**Step 4 - Use in your function:**
```python
import pandas as pd  # works now because layer is attached

def lambda_handler(event, context):
    df = pd.DataFrame({'col1': [1, 2, 3]})
    print(df)
    return {'statusCode': 200}
```

---

## 10. Deploying Lambda via ZIP File

### Why ZIP deployment

The inline console editor is fine for small scripts. But for real projects you need ZIP deployment when:
- Code is larger than what fits in the inline editor (max 3 MB inline)
- You have multiple Python files
- You need to include local dependencies
- You want to deploy via CLI or CI/CD pipeline

### Simple ZIP - code only

When your function has no external dependencies:

```bash
# Create zip with just your Python file
zip function.zip handler.py

# Deploy via CLI
aws lambda update-function-code \
  --function-name my-function \
  --zip-file fileb://function.zip
```

### ZIP with dependencies

When your function needs external libraries:

```bash
# Install dependencies into a local folder
pip install requests -t package/

# Copy your code into the same folder
cp handler.py package/

# Zip everything together
cd package
zip -r ../function.zip .
cd ..

# Deploy
aws lambda update-function-code \
  --function-name my-function \
  --zip-file fileb://function.zip
```

### ZIP structure

```
function.zip
├── handler.py          ← your Lambda code
├── utils.py            ← any other Python files
├── requests/           ← installed library
├── requests-2.31.0.dist-info/
└── ...
```

### Deploy via Console

- Lambda Console → your function → **Code** tab
- Click **Upload from** → **.zip file**
- Select your zip → **Save**

### When to use ZIP vs Layers

| | ZIP with dependencies | Layers |
|---|---|---|
| Dependencies shared across functions | No, duplicated | Yes, one layer for all |
| Quick single function deployment | Yes | Overhead of creating layer |
| Large shared libraries (pandas, numpy) | Package size grows | Better, kept separate |
| CI/CD pipeline deployment | Common approach | Used alongside ZIP |

---

*More topics will be added in upcoming modules.*
