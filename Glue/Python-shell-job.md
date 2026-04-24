# AWS Glue - Python Shell Job

---

## Table of Contents

1. [What is a Python Shell Job](#1-what-is-a-python-shell-job)
2. [Creating a Python Shell Job](#2-creating-a-python-shell-job)
3. [Important Job Parameters](#3-important-job-parameters)
4. [IAM Role and Permissions](#4-iam-role-and-permissions)
5. [Runtime Parameters - Job Run ID](#5-runtime-parameters---job-run-id)
6. [Checking Output Logs](#6-checking-output-logs)
7. [Simulating and Debugging Errors](#7-simulating-and-debugging-errors)

---

## 1. What is a Python Shell Job

A Python Shell Job in AWS Glue runs a plain Python script without any Spark cluster. It is lightweight, starts quickly, and is cost effective compared to a Spark ETL job.

**Best suited for:**
- Small data transformations (MBs not GBs)
- Calling external APIs
- Triggering other AWS services like Lambda, SNS, or another Glue job
- Running SQL queries on Athena or Redshift
- Lightweight file operations on S3

---

## 2. Creating a Python Shell Job

**Steps:**
1. Glue Console → **ETL Jobs** → **Create job**
2. Select **Python Shell** as the job type
3. Choose Python version (Python 3.9 recommended)
4. Set the script location - S3 path where your Python script is stored
5. Configure IAM role, DPU, timeout and other parameters
6. Click **Save**

---

## 3. Important Job Parameters

When creating a Python Shell Job, these are the key parameters to understand:

| Parameter | Description |
|---|---|
| **Job Name** | Unique name to identify the job |
| **IAM Role** | Role that grants the job permissions to access AWS services |
| **Python Version** | Python 3.9 is the recommended version for Python Shell. Only Python 3.6 and 3.9 are supported |
| **DPU** | Data Processing Units - Python Shell uses 0.0625 DPU (1/16th) by default, max 1 DPU |
| **Max Capacity** | Controls how much compute is allocated - set to 0.0625 for Python Shell |
| **Timeout** | Maximum time the job is allowed to run before it is forcefully stopped (in minutes) |
| **Script Path** | S3 location of your Python script |
| **Temp Directory** | S3 path used by Glue for temporary files during job execution |
| **Job Parameters** | Custom key-value pairs passed to the script at runtime (e.g. `--input_path`, `--output_path`) |
| **Max Retries** | Number of times Glue automatically retries the job on failure |
| **Number of Workers** | Not applicable for Python Shell - only relevant for Spark jobs |

**Passing custom parameters to the script:**

```python
import sys
from awsglue.utils import getResolvedOptions

# Fetch custom parameters passed at job creation or runtime
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'input_path', 'output_path'])

input_path = args['input_path']
output_path = args['output_path']

print(f"Input: {input_path}")
print(f"Output: {output_path}")
```

---

## 4. IAM Role and Permissions

The IAM role attached to the Glue job defines what AWS resources the job can access. Without the right permissions the job will fail with an Access Denied error.

**Minimum required permissions:**

| Permission | Why it is needed |
|---|---|
| `AWSGlueServiceRole` (AWS Managed) | Allows Glue to manage job execution, write logs to CloudWatch |
| `s3:GetObject` | Read input files from S3 |
| `s3:PutObject` | Write output files to S3 |
| `s3:ListBucket` | List objects in S3 bucket |
| `logs:CreateLogGroup` | Create CloudWatch log group for job logs |
| `logs:CreateLogStream` | Create log stream inside the log group |
| `logs:PutLogEvents` | Write log events to CloudWatch |

**Recommended approach:**
- Attach the AWS managed policy `AWSGlueServiceRole` as a base
- Add a custom policy scoped to the specific S3 buckets the job needs to access

**AWS Glue System Bucket - Auto Created on First Run:**

When you run a Glue job for the first time in a region, Glue automatically creates a system bucket on your behalf if it does not already exist:

```
Bucket name: aws-glue-assets-<account-id>-<region>
Example:     aws-glue-assets-526844078262-ap-south-1
```

This bucket is used by Glue internally to store:
- Your ETL scripts
- Temporary files during job execution
- Spark shuffle data during Spark job runs
- Job output before moving to final destination

This is why `AWSGlueServiceRole` includes `s3:CreateBucket` permission scoped to `arn:aws:s3:::aws-glue-*` - so Glue can create this bucket automatically without any manual setup from you.

**Trust policy on the role must allow Glue to assume it:**

```json
{
    "Effect": "Allow",
    "Principal": {
        "Service": "glue.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
}
```

---

## 5. Runtime Parameters - Job Run ID

Every time a Glue job is triggered, AWS assigns it a unique **Job Run ID**. This ID is used to track, monitor, and debug a specific execution of the job.

**Format:**
```
jr_918ec84940e0442565927328dbfee31e54a35c0081723829f22693a1e3c85cc8
```

**How to get the Job Run ID:**

**From Console:**
- Glue Console → your job → **Runs** tab
- Each run shows its Job Run ID, status, start time, duration

**From CLI:**
```bash
# Start job and capture run ID
aws glue start-job-run --job-name my-python-shell-job

# Check status using run ID
aws glue get-job-run \
  --job-name my-python-shell-job \
  --run-id jr_918ec84940e044...
```

**From boto3:**
```python
import boto3

glue = boto3.client('glue', region_name='ap-south-1')

# Start job
response = glue.start_job_run(JobName='my-python-shell-job')
job_run_id = response['JobRunId']
print(f"Job Run ID: {job_run_id}")

# Check status
status = glue.get_job_run(JobName='my-python-shell-job', RunId=job_run_id)
print(status['JobRun']['JobRunState'])
```

**Possible Job Run States:**

| State | Meaning |
|---|---|
| `STARTING` | Job is initializing |
| `RUNNING` | Job is actively executing |
| `SUCCEEDED` | Job completed successfully |
| `FAILED` | Job failed due to an error |
| `STOPPED` | Job was manually stopped |
| `ERROR` | System level error occurred |

---

## 6. Checking Output Logs

Every Python Shell Job automatically writes logs to **Amazon CloudWatch**.

**Log Groups created by Glue:**

| Log Group | Contains |
|---|---|
| `/aws-glue/python-jobs/output` | All `print()` statements from your script |
| `/aws-glue/python-jobs/error` | Error messages and stack traces |

**How to access logs:**

**From Glue Console:**
- Glue Console → your job → **Runs** tab
- Click on a specific run
- Click **Output logs** or **Error logs** link
- This opens CloudWatch directly filtered to that job run

**From CloudWatch Console:**
- CloudWatch → **Log groups** → `/aws-glue/python-jobs/output`
- Find the log stream matching your Job Run ID

**From CLI:**
```bash
aws logs filter-log-events \
  --log-group-name /aws-glue/python-jobs/output \
  --log-stream-name jr_918ec84940e044...
```

**Every `print()` statement appears in the output log in CloudWatch.**
```python
import boto3

def main():
    print("Job started")

    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket='my-bucket', Prefix='raw/')

    print(f"Found {response['KeyCount']} files")
    print("Job completed successfully")

main()
```

---

## 7. Simulating and Debugging Errors

Understanding how to read error logs is a critical skill for any data engineer.

### How Errors are Displayed

AWS Glue shows errors at two levels:

**Level 1 - Glue UI (Summary):**
- Glue Console → your job → Runs tab → click a failed run
- Shows a **single line error summary** - just enough to identify the type of error
- Example: `An error occurred (AccessDeniedException) when calling the ListObjectsV2 operation`

**Level 2 - CloudWatch Error Logs (Full Detail):**
- Click **Error logs** link on the failed run
- Shows the complete Python **stack trace** with file name, line number, and full error message
- This is where you get the full picture of what went wrong

```
Summary in Glue UI:
"AttributeError: 'NoneType' object has no attribute 'split'"

Full stack trace in CloudWatch:
Traceback (most recent call last):
  File "/tmp/script.py", line 15, in main
    prefix = source_key.split('/')[-1]
AttributeError: 'NoneType' object has no attribute 'split'
```

### Simulating a Common Error - Missing S3 Permission

```python
import boto3

def main():
    print("Job started")

    s3 = boto3.client('s3')

    # This will fail if the IAM role does not have s3:ListBucket permission
    response = s3.list_objects_v2(Bucket='my-bucket', Prefix='raw/')
    print(response)

main()
```

**What you will see:**

In Glue UI (single line):
```
An error occurred (AccessDeniedException) when calling the ListObjectsV2 operation: Access Denied
```

In CloudWatch error logs (full detail):
```
Traceback (most recent call last):
  File "script.py", line 8, in main
    response = s3.list_objects_v2(Bucket='my-bucket', Prefix='raw/')
  File ".../botocore/client.py", line 940, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.exceptions.ClientError: An error occurred (AccessDeniedException)
when calling the ListObjectsV2 operation: Access Denied
```

### Debugging Checklist

When a Glue job fails:

1. Go to Glue Console → job → **Runs** tab
2. Click the failed run → read the **single line error** in the UI
3. Click **Error logs** → read the full **stack trace** in CloudWatch
4. Identify the line number and error type from the stack trace
5. Common fixes:
   - `AccessDeniedException` → fix IAM role permissions
   - `NoSuchBucket` → check S3 bucket name spelling
   - `AttributeError` / `KeyError` → fix the Python code logic
   - `ModuleNotFoundError` → library not available, add it via Glue job libraries or use a different approach
