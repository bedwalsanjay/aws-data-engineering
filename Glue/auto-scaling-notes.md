# Auto Scaling Workers — Native Spark vs AWS Glue

## How it works in Native Spark

In native Spark (on EMR, Databricks, or a self-managed cluster), auto scaling is called **Dynamic Resource Allocation (DRA)**.

You enable it via Spark config:

```properties
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=1
spark.dynamicAllocation.maxExecutors=10
spark.dynamicAllocation.initialExecutors=1
spark.shuffle.service.enabled=true   # required for DRA to work
```

**How DRA decides to scale:**
- If tasks are **backlogged** (pending tasks > available executor slots) for `spark.dynamicAllocation.schedulerBacklogTimeout` (default 1s) → add executor
- If an executor is **idle** for `spark.dynamicAllocation.executorIdleTimeout` (default 60s) → remove it

**The catch — Shuffle Service:**  
DRA requires an **external shuffle service** running on each node. This is because when an executor is removed, its shuffle data must still be accessible to other executors. Without it, removing an executor loses its shuffle output and tasks fail.

On a self-managed cluster you must deploy and configure this separately. On EMR it comes pre-configured.

---

## How it works in AWS Glue

Glue wraps DRA into a one-click feature called **"Automatically scale the number of workers"**.

- No shuffle service config needed — Glue handles it internally
- You just set **Maximum number of workers** — that's the ceiling
- Glue starts with 1 executor and scales up when tasks are backlogged
- Scales back down when executors go idle

Under the hood, Glue uses the same Spark DRA config:
```
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=1
spark.dynamicAllocation.maxExecutors=N   (derived from your max workers setting)
```

**Key difference from native Spark:**  
In native Spark you manage the shuffle service, cluster nodes, and scaling policies yourself. In Glue, AWS manages all of that — you only set the max workers and enable the toggle.
