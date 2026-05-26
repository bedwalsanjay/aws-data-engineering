# AWS Glue - Notebook ETL Job

---

## Table of Contents

1. [What is a Glue Notebook ETL Job](#1-what-is-a-glue-notebook-etl-job)
2. [Notebook vs Script ETL Job](#2-notebook-vs-script-etl-job)
3. [How to Create a Notebook ETL Job](#3-how-to-create-a-notebook-etl-job)
4. [Cost Considerations](#4-cost-considerations)
5. [Important Settings to Configure](#5-important-settings-to-configure)
6. [The Cluster Starts Immediately - Critical Point](#6-the-cluster-starts-immediately---critical-point)
7. [Job Timeout](#7-job-timeout)
8. [Converting Notebook to a Deployable Glue Job](#8-converting-notebook-to-a-deployable-glue-job)
9. [Best Practices](#9-best-practices)

---

## 1. What is a Glue Notebook ETL Job

A Glue Notebook ETL Job is an **interactive Jupyter-style notebook** that runs on a managed Spark cluster in AWS. It lets you write and run PySpark code cell by cell — exactly like a local Jupyter notebook — but the execution happens on a real AWS Glue Spark cluster.

```
Local Jupyter Notebook:
  Code runs on your laptop → limited memory 

Glue Notebook ETL:
  Code runs on AWS Spark cluster → scalable
  Same cell-by-cell interactive experience
```

**When to use Notebook ETL:**
- Exploring and understanding a new dataset
- Developing and testing ETL logic interactively before deploying as a job
- Teaching and demonstrating Glue/Spark concepts
- One-off data analysis that needs Spark scale

**When NOT to use Notebook ETL:**
- Scheduled production pipelines — use a Script ETL job instead
- Automated runs triggered by events — use a Script ETL job instead

---

## 2. Notebook vs Script ETL Job

| | Notebook ETL | Script ETL Job |
|---|---|---|
| Execution style | Interactive, cell by cell | Runs entire script top to bottom |
| Scheduling | Cannot be scheduled | Can be scheduled via triggers |
| Best for | Development, exploration, teaching | Production pipelines |
| Cluster startup | Starts immediately when notebook opens | Starts when job is triggered |
| Cost risk | High — easy to forget cluster is running | Lower — runs only when triggered |
| Output | Inline results in notebook | CloudWatch logs |

---

## 3. How to Create a Notebook ETL Job

**Step 1 — Go to Glue Console**
```
AWS Console → AWS Glue → ETL Jobs → Create job
```

**Step 2 — Choose job type**
```
Select: Jupyter Notebook
```

**Step 3 — Configure the notebook**
- Give it a name
- Choose IAM role with S3 + Glue permissions
- Set Glue version (use latest — Glue 4.0 or 5.0)
- Set Worker Type
- Set Number of Workers
- Set Job timeout

**Step 4 — Click Create**

> As soon as you click Create and the notebook opens, the Spark cluster starts provisioning in the background. You are being billed from this point.

**Step 5 — Wait for kernel to be ready**

The notebook will show a loading indicator while the cluster starts. This typically takes **2 to 4 minutes**. Once the kernel is ready you can start running cells.

---

## 4. Cost Considerations

### Number of Workers — Keep it Low for Development

The default number of workers in a new Glue notebook is **5**. For development and testing you almost never need 5 workers.

```
Default (5 workers, G.1X):
  5 workers × 1 DPU × $0.44/DPU-hour = $2.20/hour

Recommended for dev (2 workers, G.1X):
  2 workers × 1 DPU × $0.44/DPU-hour = $0.88/hour

Savings: 60% cost reduction just by changing one setting
```

**Rule of thumb:**
- Development and testing → **2 workers** is enough for most datasets under 1 GB
- Production jobs → size based on actual data volume and SLA

### Worker Type — G.1X is Enough for Development

```
G.1X  → 4 vCPU, 16 GB RAM, 1 DPU  → sufficient for dev/test
G.2X  → 8 vCPU, 32 GB RAM, 2 DPU  → use only if you hit memory errors
```

Do not use G.2X or higher for notebook development. Start with G.1X and scale up only if needed.

### Billing Starts When Cluster Starts — Not When You Run Code

This is the most important cost point. The cluster starts the moment you open the notebook. You are billed even when you are just reading the notebook, thinking, or have stepped away.

```
You open notebook at 10:00 AM
You run your first cell at 10:15 AM
You close notebook at 11:00 AM

Billed duration: 10:00 AM to 11:00 AM = 1 hour
NOT 10:15 AM to 11:00 AM
```

---

## 5. Important Settings to Configure

### Number of Workers
Set to **2** for development. Minimum is 2 for Spark ETL (1 driver + 1 worker).

```
Glue Console → Create job → Number of workers → 2
```

### Worker Type
Set to **G.1X** for development.

```
Glue Console → Create job → Worker type → G.1X
```

### Job Timeout
Default is **2880 minutes (48 hours)**. This means if you forget to close the notebook, the cluster will keep running for up to 48 hours and you will be billed for all of it.

**Always set a lower timeout for notebooks:**
```
For development notebooks → set to 60 minutes (1 hour)
For longer sessions       → set to 120 or 180 minutes
```

```
Glue Console → Create job → Job timeout → 60
```

### Glue Version
Always use the latest available version.

```
Glue Console → Create job → Glue version → Glue 4.0 or 5.0
```

### IAM Role
The role must have:
- `AmazonS3FullAccess` or scoped S3 permissions for your buckets
- `AWSGlueServiceRole` for Glue Catalog access
- `CloudWatchLogsFullAccess` for logging

---

## 6. The Cluster Starts Immediately - Critical Point

This is the most common mistake people make with Glue notebooks.

**What happens when you click Create / Open notebook:**
```
You click "Create" or "Open"
        ↓
AWS immediately starts provisioning a Spark cluster
        ↓
Billing starts
        ↓
Cluster is ready in 2-4 minutes
        ↓
You see "Kernel Ready" in the notebook
```

**You are billed even if you:**
- Never run a single cell
- Close the browser tab (cluster keeps running)
- Step away from your desk
- The notebook is idle

**How to stop billing:**
```
Option 1: Close the notebook properly
  Notebook → File → Shut Down Kernel → then close

Option 2: Stop the session from Glue Console
  Glue Console → Interactive Sessions → find your session → Stop

Option 3: Let the timeout expire
  If you set timeout to 60 minutes, cluster auto-terminates after 60 minutes of total runtime
```

**The timeout is your safety net.** Always set a reasonable timeout so you are not billed for hours if you forget to close the notebook.

---

## 7. Job Timeout

| Setting | Default Value | Recommended for Notebooks |
|---|---|---|
| Job timeout | 2880 minutes (48 hours) | 60 minutes for dev sessions |

**What timeout means:**
- The cluster will be **forcefully terminated** after this many minutes from when it started
- It does NOT reset when you run a cell — it counts from cluster start time
- If your notebook session runs longer than the timeout, the kernel dies and you lose unsaved work

```
Example with 60 minute timeout:

10:00 AM  → Notebook opened, cluster starts, timeout clock starts
10:45 AM  → You are still working
11:00 AM  → Timeout reached, cluster forcefully terminated
            Any running cell is killed
            Unsaved notebook state is lost
```

**Practical advice:**
- Set timeout to slightly more than your expected session length
- Save your notebook frequently
- If you need more time, you can update the timeout before it expires from the Glue Console

---

## 8. Converting Notebook to a Deployable Glue Job

Once you have developed and tested your logic in the notebook, you convert it to a Script ETL job for production deployment.

**Step 1 — Clean up the notebook code**

Remove any exploratory cells like `df.show()`, `df.printSchema()`, `df.count()` that you only needed during development. These are expensive in production as they trigger full Spark actions.

**Step 2 — Make sure these lines are present**

```python
# At the top — required for Job Bookmark and proper job tracking
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# At the bottom — required to save Job Bookmark state
job.commit()
```

**Step 3 — Replace hardcoded paths with job parameters**

```python
# In notebook (hardcoded — fine for dev)
S3_INPUT  = "s3://sanjay-de-bucket-2026/orders_raw/"
S3_OUTPUT = "s3://sanjay-de-bucket-2026/orders_processed/"

# In production script (parameterized)
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'input_path', 'output_path'])
S3_INPUT  = args['input_path']
S3_OUTPUT = args['output_path']
```

**Step 4 — Download the notebook as a script**
```
Notebook → File → Download as → Python (.py)
```

**Step 5 — Upload the script to S3 and create a Script ETL job pointing to it**
```
Glue Console → ETL Jobs → Create job → Spark script editor
→ Upload your .py file
→ Configure workers, timeout, schedule
```

---

## 9. Best Practices

| Practice | Why |
|---|---|
| Set Number of Workers to 2 for dev | Reduces cost by 60% vs default 5 workers |
| Set timeout to 60 minutes for dev sessions | Prevents accidental billing if you forget to close |
| Always shut down kernel when done | Stops billing immediately instead of waiting for timeout |
| Use G.1X worker type for dev | Sufficient for datasets under 1 GB, cheapest option |
| Save notebook frequently | Cluster termination (timeout or manual) loses unsaved state |
| Remove `df.show()` and `df.count()` before production | These trigger full Spark scans, expensive at scale |
| Use job parameters instead of hardcoded paths | Makes the script reusable across environments |
| Enable Spark UI for production jobs | Essential for debugging performance issues |
| Tag your notebook job with team and project | Helps track costs in AWS Cost Explorer |
| Do not use notebooks for scheduled production pipelines | Use Script ETL jobs instead — notebooks are for development only |
