# AWS Glue - getResolvedOptions Function 

---

## Table of Contents

1. [What is getResolvedOptions](#1-what-is-getresolvedoptions)
2. [Why Not Use sys.argv Directly](#2-why-not-use-sysargv-directly)
3. [How getResolvedOptions Works](#3-how-getresolvedoptions-works)
4. [System Parameters Available by Default](#4-system-parameters-available-by-default)
5. [Sample Script](#5-sample-script)
6. [How to Pass Parameters to a Glue Job](#6-how-to-pass-parameters-to-a-glue-job)

---

## 1. What is getResolvedOptions

`getResolvedOptions` is a utility function provided by the AWS Glue library (`awsglue.utils`) that helps you **read parameters passed to a Glue job** in a clean and reliable way.

When you run a Glue job, you can pass custom parameters like input S3 path, output S3 path, database name, date etc. `getResolvedOptions` reads these parameters from the command line arguments and returns them as a clean Python dictionary.

```python
from awsglue.utils import getResolvedOptions
import sys

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'input_path', 'output_path'])

print(args['input_path'])
print(args['output_path'])
```

---

## 2. Why Not Use sys.argv Directly

This is the most important question. Technically `sys.argv` contains all the arguments passed to the script. So why not just use it directly?

---

**Problem 1 - sys.argv returns a raw messy list**

When Glue runs your script it passes arguments in this format:

```
sys.argv = [
    'script.py',
    '--JOB_NAME', 'my-glue-job',
    '--JOB_RUN_ID', 'jr_abc123',
    '--JOB_QUEUE_ARN', 'arn:aws:...',
    '--input_path', 's3://my-bucket/raw/',
    '--output_path', 's3://my-bucket/silver/',
    '--TempDir', 's3://aws-glue-temp/...',
    ... many more internal Glue parameters
]
```

To get `input_path` using raw `sys.argv` you would have to:

```python
# Manually parse sys.argv - messy and error prone
for i, arg in enumerate(sys.argv):
    if arg == '--input_path':
        input_path = sys.argv[i + 1]
```

This is fragile, verbose, and breaks if argument order changes.

---

**Problem 2 - Glue injects many internal parameters automatically**

Glue adds its own system parameters to `sys.argv` like:
- `--JOB_RUN_ID`
- `--JOB_QUEUE_ARN`
- `--TempDir`
- `--encryption-type`
- `--enable-metrics`

If you try to parse `sys.argv` manually you have to deal with all of these even though you do not need them.

---

**Problem 3 - No validation**

`sys.argv` does not tell you if a required parameter is missing. Your script will silently fail or throw a confusing `IndexError` at runtime.

---

**How getResolvedOptions solves all of this:**

```python
# Clean, simple, validated
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'input_path', 'output_path'])
```

- Returns only the parameters you asked for as a clean dictionary
- Ignores all internal Glue system parameters automatically
- Raises a clear error if a required parameter is missing
- No manual parsing needed

---

**Side by side comparison:**

| | `sys.argv` directly | `getResolvedOptions` |
|---|---|---|
| Returns | Raw list with everything | Clean dictionary with only what you need |
| Internal Glue params | You have to filter them out | Automatically ignored |
| Missing param handling | Silent failure or IndexError | Clear descriptive error |
| Code complexity | High - manual parsing | Low - one line |
| Recommended | No | Yes |

---

## 3. How getResolvedOptions Works

```python
getResolvedOptions(sys.argv, ['PARAM1', 'PARAM2', 'PARAM3'])
```

- **First argument** - always pass `sys.argv`
- **Second argument** - list of parameter names you want to read
- **Returns** - a dictionary where keys are parameter names and values are the passed values

**Important naming rule:**

Parameters must be passed with `--` prefix when running the job but you reference them without `--` in your code:

```
Passed as:    --input_path
Read as:      args['input_path']
```

---

## 4. System Parameters Available by Default

Glue automatically injects system parameters into every job run. However the availability of these parameters **differs between Python Shell and Spark ETL jobs**.

| Parameter | Python Shell Job | Spark ETL Job | Description |
|---|---|---|---|
| `JOB_NAME` | ❌ Not auto injected | ✅ Auto injected | Name of the Glue job |
| `JOB_RUN_ID` | ❌ Not auto injected | ✅ Auto injected | Unique ID of the current job run |
| `JOB_ID` | ❌ Not present | ✅ Auto injected | Internal Glue job definition ID |
| `TempDir` | ✅ Auto injected | ✅ Auto injected | S3 path for Glue temporary files |

**For Python Shell jobs:**
- `JOB_NAME` and `JOB_RUN_ID` are NOT automatically available
- You must pass `--JOB_NAME` manually as a job parameter when running the job
- If you include `JOB_NAME` in `getResolvedOptions` without passing it manually you will get:
```
error: the following arguments are required: --JOB_NAME
```

**For Spark ETL jobs:**
- `JOB_NAME`, `JOB_RUN_ID` and `JOB_ID` are all automatically injected by Glue
- You can safely include them in `getResolvedOptions` without passing them manually

```python
# Safe to use in Spark ETL job - auto injected by Glue
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'JOB_RUN_ID'])
print(args['JOB_NAME'])    # order-analytics-etl
print(args['JOB_RUN_ID'])  # jr_2f5b0cb49e8429a0...
```

**Difference between `JOB_ID` and `JOB_RUN_ID`:**

| Parameter | Description | Use case |
|---|---|---|
| `JOB_ID` | Identifies the job definition itself - same across all runs | Rarely used |
| `JOB_RUN_ID` | Unique ID for each individual run of the job | Tracking, logging, debugging |

---

## 5. Sample Script

This script takes `input_path`, `output_path`, `environment` and `batch_date` as inputs and prints them to demonstrate `getResolvedOptions` usage.

```python
import sys
from awsglue.utils import getResolvedOptions

def main():

    # Pass JOB_NAME along with all custom parameters in the same list
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'input_path',
        'output_path',
        'environment',
        'batch_date'
    ])

    # Print system parameters
    print(f"Job Name    : {args['JOB_NAME']}")

    # Print custom parameters
    print(f"Input Path  : {args['input_path']}")
    print(f"Output Path : {args['output_path']}")
    print(f"Environment : {args['environment']}")
    print(f"Batch Date  : {args['batch_date']}")

    print("All parameters read successfully")

main()
```

**Expected output in CloudWatch logs:**

```
Job Name    : my-python-shell-job
Input Path  : s3://my-bucket/raw/sales/
Output Path : s3://my-bucket/silver/sales/
Environment : prod
Batch Date  : 2026-04-23
All parameters read successfully
```

---

**What happens if a required parameter is missing:**

If you forget to pass `--batch_date` when running the job, `getResolvedOptions` raises a clear error:

```
awsglue.utils.GlueArgumentError: argument --batch_date: expected one argument
```

This is much better than a silent failure or a confusing `IndexError` from raw `sys.argv`.

---

## 6. How to Pass Parameters to a Glue Job

**From Glue Console:**
- Glue Console → your job → **Run**
- Scroll to **Job parameters**
- Add key-value pairs:

```
Key              Value
--input_path     s3://my-bucket/raw/sales/
--output_path    s3://my-bucket/silver/sales/
--environment    prod
--batch_date     2026-04-23
```

> Note: Keys must start with `--` in the console but you read them without `--` in your code.

---

**From AWS CLI:**

```bash
aws glue start-job-run \
  --job-name my-python-shell-job \
  --arguments '{
    "--input_path": "s3://my-bucket/raw/sales/",
    "--output_path": "s3://my-bucket/silver/sales/",
    "--environment": "prod",
    "--batch_date": "2026-04-23"
  }'
```

---

**From boto3:**

```python
import boto3

glue = boto3.client('glue', region_name='ap-south-1')

glue.start_job_run(
    JobName='my-python-shell-job',
    Arguments={
        '--input_path': 's3://my-bucket/raw/sales/',
        '--output_path': 's3://my-bucket/silver/sales/',
        '--environment': 'prod',
        '--batch_date': '2026-04-23'
    }
)
```
