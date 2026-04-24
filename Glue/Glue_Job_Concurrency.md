# AWS Glue - Job Concurrency

---

## Table of Contents

1. [What is Glue Job Concurrency](#1-what-is-glue-job-concurrency)
2. [Use Cases for Concurrency Greater Than 1](#2-use-cases-for-concurrency-greater-than-1)
3. [Cons of Accidentally Setting Concurrency Greater Than 1](#3-cons-of-accidentally-setting-concurrency-greater-than-1)
4. [When to Use Which](#4-when-to-use-which)

---

## 1. What is Glue Job Concurrency

By default a Glue job allows only **1 concurrent run** at a time. If a second trigger fires while the job is already running, it gets **rejected immediately** with a `ConcurrentRunsExceededException` error.

```
Default Concurrency = 1

Trigger fires at 10:00 AM → Job Run 1 starts
Trigger fires at 10:05 AM → Job Run 1 still running
                          → Second run is rejected immediately
                          → Error: ConcurrentRunsExceededException
```

**Error message you will see:**
```
Failed to start job
ConcurrentRunsExceededException: Concurrent runs exceeded.
(Service: AWSGlue; Status Code: 400; Error Code: ConcurrentRunsExceededException)
```

> Important: Glue does NOT queue the second run. It fails immediately. If you need queuing behavior, you must implement it yourself using SQS or Step Functions.

**Where to configure:**
- Glue Console → your job → **Edit** → **Advanced properties** → **Max concurrency**

---

## 2. Use Cases for Concurrency Greater Than 1

---

### 2.1 Multiple Independent Data Sources Processed in Parallel

```
You have 10 clients, each with their own S3 folder
Each client's data needs to be processed independently

Without concurrency:
Client 1 → 5 min → Client 2 → 5 min → ... → Client 10 → Total: 50 min

With concurrency = 10:
All 10 clients processed simultaneously → Total: ~5 min
```

---

### 2.2 Hourly Job That Takes More Than 1 Hour

```
EventBridge triggers Glue job every hour
Job takes 90 minutes to complete

At 60 min mark → second trigger fires → first run still running

Without concurrency > 1 → second run fails immediately with ConcurrentRunsExceededException
With concurrency > 1    → both runs execute simultaneously
```

---

### 2.3 Event Driven Pipelines with Unpredictable File Arrival

```
Multiple files land in S3 at the same time
Each file triggers a separate Lambda → each Lambda triggers Glue

Without concurrency → only first job runs, rest fail with ConcurrentRunsExceededException
With concurrency   → all files processed simultaneously
```

---

### 2.4 Backfill Scenarios

```
You need to reprocess 30 days of historical data

Without concurrency:
Day 1 → Day 2 → Day 3 → ... → Day 30 → Total: 30 × job duration

With concurrency = 30:
All 30 days processed simultaneously
Entire backfill completes in the time of a single day's run
```

---

## 3. Cons of Accidentally Setting Concurrency Greater Than 1

---

### 3.1 Duplicate Data in Target

```
Job reads from S3 raw/ and writes to silver/
Two runs start at the same time reading the same files
Both write the same records to the target

Result: duplicate rows in Redshift or duplicate files in S3
```

This is the most common and dangerous side effect of unintended concurrency.

---

### 3.2 Unexpected AWS Costs

```
Concurrency = 10
DPU per run  = 2

10 simultaneous runs = 20 DPUs running at once
Cost multiplies by 10x without you realizing

What you expected: $0.15 per run
What you got:      $1.50 for 10 simultaneous runs
```

---

### 3.3 Race Conditions on Shared Resources

```
Two runs try to write to the same S3 path simultaneously
One run overwrites the other

Result: data loss or corrupted output files
```

---

### 3.4 Database Connection Exhaustion

```
Job connects to RDS or Redshift
Concurrency = 20 means 20 simultaneous DB connections

RDS max connections = 100
20 Glue runs + other applications = connection pool exhausted

Result: all database operations start failing with
"too many connections" error
```

---

### 3.5 Glue Data Catalog Conflicts

```
Two runs try to update the same table partition in Glue Catalog simultaneously
One run's catalog update overwrites the other

Result: partition metadata becomes inconsistent
Athena queries return wrong or missing data
```

---

### 3.6 Hitting AWS Service Limits

```
Each region has a max concurrent Glue job runs limit (default 200)

If concurrency is set too high across multiple jobs
You hit the regional limit

Result: new job runs start failing with throttling errors
```

---

## 4. When to Use Which

| Concurrency | When to Use |
|---|---|
| 1 (default) | Sequential pipelines, jobs writing to same target, jobs sharing DB connections |
| > 1 | Independent parallel workloads, multi-tenant pipelines, backfill, event driven with simultaneous triggers |

**The key question to ask before setting concurrency > 1:**

> "Can two runs of this job safely execute at the same time without interfering with each other?"

- If **YES** → concurrency > 1 is safe
- If **NO** → keep it at 1
