# Boto3 - Complete Guide

---

## Table of Contents

1. [What is Boto3](#1-what-is-boto3)
2. [Python and Pip Setup in CloudShell](#2-python-and-pip-setup-in-cloudshell)
3. [Why Boto3 is Needed](#3-why-boto3-is-needed)
4. [Installation and Setup](#4-installation-and-setup)
5. [Boto3 Client](#5-boto3-client)
6. [S3 Operations with Boto3](#6-s3-operations-with-boto3)
7. [Run and Monitor a Glue Job](#7-run-and-monitor-a-glue-job)
8. [Other Useful Boto3 Examples](#8-other-useful-boto3-examples)

---

## 1. What is Boto3

Boto3 is the official **AWS SDK (Software Development Kit) for Python**. It allows you to interact with AWS services programmatically using Python code.

- Maintained and released by AWS
- Covers virtually every AWS service
- Used in Lambda functions, Glue jobs, EC2 scripts, local Python scripts, Airflow DAGs - everywhere

```
Without Boto3:
You → AWS Console → click buttons → AWS does something

With Boto3:
You → Python script → Boto3 → AWS API → AWS does something
```

---

## 2. Python and Pip Setup in CloudShell

CloudShell comes with an older Python version by default. Follow these steps to upgrade to Python 3.12 and set up pip correctly.

### Upgrade Python to 3.12

```bash
sudo yum install python3.12 -y
```

### Set Python 3.12 as Default

Add aliases to `.bashrc` so `python3` and `pip3` always point to 3.12:

```bash
echo "alias python3='python3.12'" >> ~/.bashrc
echo "alias pip3='python3.12 -m pip'" >> ~/.bashrc

# Reload .bashrc to apply changes
source ~/.bashrc
```

### Install pip for Python 3.12

```bash
python3.12 -m ensurepip --upgrade
```

### Install Boto3

```bash
python3.12 -m pip install boto3
```

### Verify everything is working

```bash
python3 --version
# Python 3.12.x

pip3 --version
# pip xx.x from .../python3.12/...

python3 -c "import boto3; print(boto3.__version__)"
# 1.xx.x
```

> From now on use `python3` and `pip3` in CloudShell - they will automatically use Python 3.12 thanks to the aliases.



---

## 3. Why Boto3 is Needed

| Scenario | Without Boto3 | With Boto3 |
|---|---|---|
| Upload 1000 files to S3 | Click upload 1000 times | One loop in Python |
| Trigger Glue job daily | Login and click manually | Schedule a Python script |
| Check job status | Refresh console repeatedly | Poll in a while loop |
| Copy files between buckets | Manual download + upload | One `copy_object` call |
| Create infrastructure | Click through wizards | Python script, repeatable |
| React to events | Not possible manually | Lambda + Boto3 |

**Real world usage in data engineering:**
- Lambda functions use Boto3 to interact with S3, Glue, DynamoDB
- Glue jobs use Boto3 for custom AWS API calls
- Airflow DAGs use Boto3 operators under the hood
- CI/CD pipelines use Boto3 to deploy Lambda functions
- Data pipelines use Boto3 to orchestrate multiple AWS services

---

## 4. Installation and Setup

### Install Boto3

```bash
pip install boto3
```

> Boto3 comes pre-installed in AWS Lambda, AWS Glue, AWS CloudShell, and Amazon SageMaker. No installation needed in those environments.

### Authentication

Boto3 needs AWS credentials to make API calls. It looks for credentials in this order:

```
1. Explicitly passed in code (not recommended)
2. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
3. AWS credentials file (~/.aws/credentials)
4. IAM Role attached to EC2/Lambda/Glue (recommended for AWS environments)
```

**Local setup (after running `aws configure`):**
```bash
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: ap-south-1
# Default output format: json
```

After this, Boto3 automatically picks up credentials from `~/.aws/credentials`. No extra setup needed in your Python code.

**Inside Lambda/Glue/EC2:**
Boto3 automatically uses the IAM role attached to the service. No credentials needed in code at all.

---

## 5. Boto3 Client

Boto3 uses a **Client** to interact with AWS services.

- Direct mapping to AWS API calls
- Returns raw Python dictionaries
- Available for every AWS service
- Works for all services - S3, Glue, Lambda, Kinesis, DynamoDB and more

```python
import boto3

# Create a client for S3
s3 = boto3.client('s3', region_name='ap-south-1')

# Create a client for Glue
glue = boto3.client('glue', region_name='ap-south-1')

# Create a client for Lambda
lambda_client = boto3.client('lambda', region_name='ap-south-1')
```

The pattern is always the same - `boto3.client('service-name', region_name='your-region')`.

---

## 6. S3 Operations with Boto3

```python
import boto3

s3 = boto3.client('s3', region_name='ap-south-1')

# ── List all buckets ──────────────────────────────────────────
response = s3.list_buckets()
for bucket in response['Buckets']:
    print(bucket['Name'])


# ── List objects in a bucket ──────────────────────────────────
response = s3.list_objects_v2(
    Bucket='sanjay-de-bucket-2026',
    Prefix='raw/'
)
for obj in response.get('Contents', []):
    print(obj['Key'], obj['Size'])


# ── Upload a file ─────────────────────────────────────────────
s3.upload_file(
    Filename='/home/cloudshell-user/work/t.csv',
    Bucket='sanjay-de-bucket-2026',
    Key='raw/local_file.csv'
)


# ── Download a file ───────────────────────────────────────────
s3.download_file(
    Bucket='sanjay-de-bucket-2026',
    Key='raw/local_file.csv',
    Filename='/home/cloudshell-user/work/downloaded_file.csv'
)


# ── Copy object between buckets ───────────────────────────────
s3.copy_object(
    CopySource={
        'Bucket': 'sanjay-de-bucket-2026',
        'Key': 'raw/sales.csv'
    },
    Bucket='sanjay-destination-bucket',
    Key='silver/sales.csv'
)


# ── Delete an object ──────────────────────────────────────────
s3.delete_object(
    Bucket='sanjay-de-bucket-2026',
    Key='raw/old_file.csv'
)


# ── Read file content directly into memory (no download) ──────
response = s3.get_object(
    Bucket='sanjay-de-bucket-2026',
    Key='raw/sales.csv'
)
content = response['Body'].read().decode('utf-8')
print(content)


# ── Write string content directly to S3 (no local file) ───────
s3.put_object(
    Bucket='sanjay-de-bucket-2026',
    Key='raw/output.txt',
    Body='Hello from boto3'
)


# ── Generate a presigned URL ──────────────────────────────────
url = s3.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': 'sanjay-de-bucket-2026',
        'Key': 'raw/orders/orders.csv'
    },
    ExpiresIn=60  # 1 min
)
print(url)


# ── Check if an object exists ─────────────────────────────────
from botocore.exceptions import ClientError

def object_exists(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False

print(object_exists('sanjay-de-bucket-2026', 'raw/sales.csv'))
```

---

## 7. Run and Monitor a Glue Job

This is the most practical example for data engineers. Takes a Glue job name as input, runs it, and keeps polling until it finishes.

```python
import boto3
import time
import sys

def run_glue_job(job_name):
    glue = boto3.client('glue', region_name='ap-south-1')

    # ── Start the Glue job ────────────────────────────────────
    print(f"Starting Glue job: {job_name}")
    response = glue.start_job_run(JobName=job_name)
    job_run_id = response['JobRunId']
    print(f"Job Run ID: {job_run_id}")

    # ── Poll until job finishes ───────────────────────────────
    terminal_states = ['SUCCEEDED', 'FAILED', 'ERROR', 'STOPPED']

    while True:
        status_response = glue.get_job_run(
            JobName=job_name,
            RunId=job_run_id
        )
        status = status_response['JobRun']['JobRunState']
        print(f"Current status: {status}")

        if status in terminal_states:
            break

        print("Waiting 30 seconds...")
        time.sleep(30)

    # ── Print final result ────────────────────────────────────
    if status == 'SUCCEEDED':
        print(f"Job {job_name} completed successfully")
    else:
        error_message = status_response['JobRun'].get('ErrorMessage', 'No error message')
        print(f"Job {job_name} failed with status: {status}")
        print(f"Error: {error_message}")

    return status


# ── Run the script ────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python glue_runner.py <job-name>")
        sys.exit(1)

    job_name = sys.argv[1]
    run_glue_job(job_name)
```

**Run it:**
```bash
python glue_runner.py test_python_job_1
```

**Output:**
```
Starting Glue job: test_python_job_1
Job Run ID: jr_918ec84940e044...
Current status: STARTING
Waiting 30 seconds...
Current status: RUNNING
Waiting 30 seconds...
Current status: SUCCEEDED
Job test_python_job_1 completed successfully
```

---

## 8. Other Useful Boto3 Examples

### Trigger a Lambda Function

```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-south-1')

response = lambda_client.invoke(
    FunctionName='my-lambda-function',
    Payload=json.dumps({'bucket': 'sanjay-de-bucket-2026', 'key': 'raw/sales.csv'})
)

result = json.loads(response['Payload'].read())
print(result)
```

---

### Send SNS Notification

```python
import boto3

sns = boto3.client('sns', region_name='ap-south-1')

sns.publish(
    TopicArn='arn:aws:sns:ap-south-1:123456789012:pipeline-alerts',
    Subject='Glue Job Failed',
    Message='Glue job daily-etl failed at 2024-01-15 02:00 UTC'
)
```

---

### Write and Read from DynamoDB

```python
import boto3
from datetime import datetime

dynamodb = boto3.client('dynamodb', region_name='ap-south-1')

# Write a record
dynamodb.put_item(
    TableName='pipeline-runs',
    Item={
        'job_name': {'S': 'daily-etl'},
        'run_id': {'S': 'run-001'},
        'status': {'S': 'RUNNING'},
        'started_at': {'S': datetime.utcnow().isoformat()}
    }
)

# Read a record
response = dynamodb.get_item(
    TableName='pipeline-runs',
    Key={
        'job_name': {'S': 'daily-etl'},
        'run_id': {'S': 'run-001'}
    }
)
print(response['Item'])

# Update a record
dynamodb.update_item(
    TableName='pipeline-runs',
    Key={
        'job_name': {'S': 'daily-etl'},
        'run_id': {'S': 'run-001'}
    },
    UpdateExpression='SET #s = :status',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={':status': {'S': 'SUCCEEDED'}}
)
```

---

### Get a Secret from Secrets Manager

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='ap-south-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

creds = get_secret('prod/rds/postgres')
print(creds['username'])
print(creds['password'])
```

---

### Handle Boto3 Errors

Always wrap Boto3 calls in try/except to handle errors gracefully:

```python
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

s3 = boto3.client('s3', region_name='ap-south-1')

try:
    s3.download_file('my-bucket', 'missing-file.csv', 'local.csv')

except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        print("File does not exist in S3")
    elif error_code == '403':
        print("Access denied - check IAM permissions")
    else:
        print(f"Unexpected error: {e}")

except NoCredentialsError:
    print("AWS credentials not configured")
```

---

*More Boto3 examples will be added as we cover more AWS services.*
