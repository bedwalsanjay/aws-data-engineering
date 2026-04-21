# AWS CloudShell - Notes

---

## What is CloudShell

AWS CloudShell is a **browser based terminal** built directly into the AWS Console. It gives you a command line environment without any installation, configuration, or SSH keys.

- Pre-authenticated with your current AWS Console credentials
- Pre-installed with all common tools a data engineer needs
- Completely free to use

---

## How to Open CloudShell

- AWS Console → top navigation bar → **CloudShell icon** (terminal icon)
- Or search **CloudShell** in the AWS search bar
- Takes 30-60 seconds to initialize on first launch

---

## Already Authenticated - No aws configure Needed

This is the biggest advantage of CloudShell.

```
You login to AWS Console as sanjay-dev
        ↓
Open CloudShell
        ↓
CloudShell automatically inherits sanjay-dev's credentials
        ↓
No need to run aws configure
No access keys needed
No secret keys needed
```

Whatever IAM permissions your logged in user has, CloudShell inherits them automatically.

**Verify who you are:**
```bash
aws sts get-caller-identity
```

---

## Pre-installed Tools

No installation needed for any of these:

```bash
aws --version        # AWS CLI
python3 --version    # Python 3
pip3 --version       # pip package manager
git --version        # Git
boto3               # Python AWS SDK, already installed
```

---

## Persistent Storage

- **1 GB** of persistent storage per region in your home directory (`/home/cloudshell-user`)
- Files you create survive session restarts and browser closes
- Storage is **region specific** - files created in `us-east-1` are not visible in `ap-south-1`

```bash
# Files here persist across sessions
cd ~
echo "this file will survive session restart" > notes.txt
ls
```

---

## Region Awareness

CloudShell runs in whichever region you have selected in the AWS Console:

```
Console region = ap-south-1
        ↓
CloudShell opens in ap-south-1
        ↓
All AWS CLI commands default to ap-south-1

Switch console to us-east-1
        ↓
Open new CloudShell tab
        ↓
Now running in us-east-1
```

---

## Useful Demo Commands

### General
```bash
# Check logged in identity
aws sts get-caller-identity

# Check current region
aws configure get region
```

---

### S3 Commands
```bash
# List all S3 buckets
aws s3 ls

# List objects in a bucket
aws s3 ls sanjay-de-bucket-2026

# List objects under a specific prefix
aws s3 ls sanjay-de-bucket-2026/raw/

# Upload a file to S3
aws s3 cp C:\multi_folder\recording.conf s3://sanjay-de-bucket-2026

# Upload entire local folder to S3
aws s3 cp C:\multi_folder s3://sanjay-de-bucket-2026 --recursive
aws s3 cp C:\multi_folder s3://sanjay-de-bucket-2026/multi_folder --recursive

# Download a file from S3
aws s3 cp s3://sanjay-de-bucket-2026/raw/orders/orders.csv .

# Download entire prefix from S3
aws s3 cp s3://your-bucket-name/raw/ ./local-folder --recursive

# Sync local folder with S3 (only uploads changed files)
aws s3 sync ./local-folder s3://your-bucket-name/raw/

# Move file from one S3 location to another
aws s3 mv s3://your-bucket-name/raw/test.txt s3://your-bucket-name/silver/test.txt

# Delete a specific object
aws s3 rm s3://your-bucket-name/raw/test.txt

# Delete all objects under a prefix
aws s3 rm s3://your-bucket-name/raw/ --recursive

# Check size of a bucket or prefix
aws s3 ls s3://your-bucket-name/ --recursive --human-readable --summarize

# Create a new bucket
aws s3 mb s3://my-new-bucket --region ap-south-1

# Delete a bucket (must be empty first)
aws s3 rb s3://my-new-bucket

# Delete a bucket and all its contents
aws s3 rb s3://my-new-bucket --force
```

---

### AWS Glue Commands
```bash
# List all Glue jobs
aws glue list-jobs

# Get details of a specific Glue job
aws glue get-job --job-name test_python_job_1

# Run a Glue job
aws glue start-job-run --job-name test_python_job_1

# Run a Glue job with custom arguments
aws glue start-job-run \
  --job-name my-etl-job \
  --arguments '{"--input_path":"s3://your-bucket/raw/","--output_path":"s3://your-bucket/silver/"}'

# Check status of a specific Glue job run
aws glue get-job-run \
  --job-name test_python_job_1 \
  --run-id jr_918ec84940e0442565927328dbfee31e54a35c0081723829f22693a1e3c85cc8

# List all runs of a Glue job (most recent first)
aws glue get-job-runs \
  --job-name my-etl-job

# List only last 5 runs
aws glue get-job-runs \
  --job-name my-etl-job \
  --max-results 5

# Stop a running Glue job
aws glue batch-stop-job-run \
  --job-name my-etl-job \
  --job-run-ids jr_abc123

# List all Glue crawlers
aws glue list-crawlers

# Run a Glue crawler
aws glue start-crawler --name my-crawler

# Check crawler status
aws glue get-crawler --name my-crawler

```
###
```
#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ./glue_job.sh <job-name>"
  exit 1
fi

JOB_NAME=$1

JOB_RUN_ID=$(aws glue start-job-run \
  --job-name $JOB_NAME \
  --query 'JobRunId' \
  --output text)

echo "Job started with ID: $JOB_RUN_ID"

while true; do
  STATUS=$(aws glue get-job-run \
    --job-name $JOB_NAME \
    --run-id $JOB_RUN_ID \
    --query 'JobRun.JobRunState' \
    --output text)

  echo "Current status: $STATUS"

  if [ "$STATUS" = "SUCCEEDED" ]; then
    echo "Job completed successfully"
    break
  elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "ERROR" ] || [ "$STATUS" = "STOPPED" ]; then
    echo "Job failed with status: $STATUS"
    break
  fi

  echo "Waiting 5 seconds..."
  sleep 5
done



---
bash glue_job_run.sh test_python_job_1

```



---

### AWS Lambda Commands
```bash
# List all Lambda functions
aws lambda list-functions

# Get details of a specific function
aws lambda get-function --function-name my-function

# Invoke a Lambda function and get response
aws lambda invoke \
  --function-name my-function \
  --payload '{}' \
  response.json && cat response.json

# Invoke Lambda with input payload
aws lambda invoke \
  --function-name my-function \
  --payload '{"bucket":"sanjay-de-bucket-2026","key":"raw/sales.csv"}' \
  response.json && cat response.json

# Check Lambda function logs (last 5 minutes)
aws logs filter-log-events \
  --log-group-name /aws/lambda/my-function \
  --start-time $(date -d '5 minutes ago' +%s000)

# Get Lambda function configuration
aws lambda get-function-configuration --function-name my-function
```

---

### EC2 Commands
```bash
# List all running EC2 instances
aws ec2 describe-instances \
  --filters Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,PublicIpAddress]' \
  --output table

# Create a t3.micro EC2 instance
aws ec2 run-instances \
  --image-id ami-0f58b397bc5c1f2e8 \
  --instance-type t3.micro \
  --key-name your-key-pair-name \
  --security-group-ids sg-xxxxxxxx \
  --count 1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=my-test-instance}]'

# Note: copy the InstanceId from the output above

# Check status of a specific instance
aws ec2 describe-instances \
  --instance-ids i-xxxxxxxxxxxxxxxxx \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress]' \
  --output table

# Stop an EC2 instance (can be restarted)
aws ec2 stop-instances --instance-ids i-xxxxxxxxxxxxxxxxx

# Start a stopped EC2 instance
aws ec2 start-instances --instance-ids i-xxxxxxxxxxxxxxxxx

# Terminate an EC2 instance (permanent, cannot be undone)
aws ec2 terminate-instances --instance-ids i-xxxxxxxxxxxxxxxxx

# Verify instance is terminated
aws ec2 describe-instances \
  --instance-ids i-xxxxxxxxxxxxxxxxx \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' \
  --output table
```

> **Important:** `stop` is like shutting down your laptop - can be restarted. `terminate` is permanent deletion - cannot be undone.

---

## Session Timeout

- CloudShell session closes after **20-30 minutes of inactivity**
- Files in home directory **persist** after session ends
- Running processes and in-memory data are **lost** when session closes
- Simply reopen CloudShell to start a new session - your files will still be there

---

## Limitations

| Limitation | Detail |
|---|---|
| Storage | 1 GB per region only |
| Not for heavy workloads | Lightweight terminal, not a replacement for EC2 |
| No persistent processes | Running jobs stop when session ends |
| No permanent sudo installs | Can install packages temporarily but lost after session |
| Compute | Limited CPU and memory, not for data processing |

---

## Why CloudShell is Useful for Data Engineers

| Use Case | How CloudShell helps |
|---|---|
| Quick S3 operations | No local CLI setup needed |
| Test boto3 scripts | Python + boto3 pre-installed |
| Run Glue or EMR commands | AWS CLI ready to use |
| Access from client laptop | No installation on client machine |
| Learning and demos | Zero setup friction |
| Ad-hoc data checks | Quick queries without spinning up EC2 |

---

## CloudShell vs Local AWS CLI Setup

| | CloudShell | Local AWS CLI |
|---|---|---|
| Setup required | None | Install + configure |
| Authentication | Auto from console | Access keys needed |
| Available from | Any browser | Only your machine |
| Persistent files | 1 GB per region | Your local disk |
| Pre-installed tools | Yes | You install manually |
| Best for | Quick tasks, learning, demos | Daily development work |

---

## Cost

**CloudShell itself is completely free.**

You are only charged for AWS resources you interact with via CloudShell:
- S3 PUT/GET requests
- EC2 instances you start
- Any other AWS service you use via CLI

The CloudShell environment, compute, and storage (1 GB) are all free.
