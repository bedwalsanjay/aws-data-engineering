# Making an S3 Bucket Public - Step by Step

---

## ⚠️ WARNING - Read Before Proceeding

**Do NOT make your S3 bucket public unless you have a very specific reason.**

Making a bucket public means **anyone on the internet** can access your data without any authentication.

**Risks:**

- **Data Breach** - Sensitive data, credentials, personal information exposed to the entire internet
- **Massive AWS Bills** - Costs can increase significantly due to high request rates and data transfer if the bucket is publicly accessible and heavily accessed.
- **Compliance Violations** - Public exposure of sensitive or regulated data can lead to compliance violations under standards like GDPR, HIPAA, and PCI-DSS
- **Reputation Damage** - Public data leaks are irreversible once data is scraped and distributed

---

## 🚨 Real World Incident - The Danger of Public S3 Buckets

**The Bill Shock Problem:**
A common scenario reported by developers on Reddit and AWS forums:
- Developer makes a bucket public for testing
- Forgets to revert it
- A bot discovers the bucket and scrapes it millions of times
- AWS bill goes from $0 to $3,000+ in a single day
- AWS does NOT automatically stop charges when free tier is exceeded for data transfer

> **Rule of thumb:** If you are making a bucket public for learning purposes, put only dummy/fake data in it and delete the bucket immediately after the demo.

---

## Prerequisites

Before starting, make sure:
- You have an S3 bucket created
- The bucket contains only **dummy/test data** - no real credentials, no personal data, no sensitive information
- You will **delete or revert** the bucket settings immediately after testing

---

## Step 1 - Turn Off Block Public Access at Account Level

This is the master override switch. If this is ON, no bucket in your account can be made public regardless of bucket level settings.

- AWS Console → **S3**
- Left sidebar →  **Account and organization settings** 
- **Block Public Access settings for this account**
- Click **Edit**
- **Uncheck** all 4 options:
  - Block all public access
  - Block public access to buckets and objects granted through new ACLs
  - Block public access to buckets and objects granted through any ACLs
  - Block public access to buckets and objects granted through new public bucket or access point policies
- Click **Save changes**
- Type `confirm` in the confirmation box
- Click **Confirm**

> This affects all buckets in your account. Revert this after your demo.

---

## Step 2 - Turn Off Block Public Access at Bucket Level

- S3 → click on your bucket
- Go to **Permissions** tab
- Scroll to **Block public access (bucket settings)**
- Click **Edit**
- **Uncheck** all 4 options
- Click **Save changes**
- Type `confirm` → **Confirm**

---

## Step 3 - Add a Bucket Policy to Grant Public Access

Without this step the bucket is still private. Turning off Block Public Access only removes the safety guard, it does not grant access.

- S3 → your bucket → **Permissions** tab
- Scroll to **Bucket policy**
- Click **Edit**
- Paste the following policy (replace bucket name with yours):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicListBucket",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::sanjay-de-bucket-2026"
        },
        {
            "Sid": "PublicReadObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::sanjay-de-bucket-2026/*"
        }
    ]
}
```

- Click **Save changes**

---

## Step 4 - Verify Public Access

Open a browser in **incognito mode** and visit:

**List bucket contents:**
```
https://sanjay-de-bucket-2026.s3.amazonaws.com/
```

**Access a specific file:**
```
https://sanjay-de-bucket-2026.s3.amazonaws.com/your-file.csv
```

If you can see the bucket contents and download files without logging in, the bucket is now public.

---

## Why Both Permissions Are Needed

| Permission | What it does |
|---|---|
| `s3:ListBucket` | Lets anyone see the list of files in the bucket |
| `s3:GetObject` | Lets anyone download a specific file |

- Without `s3:ListBucket` → bucket URL returns Access Denied, files not visible
- Without `s3:GetObject` → can see file names but cannot download or view them
- Both are needed for full public browsing experience

---

## How the Two Step Design Works

AWS intentionally requires two steps to prevent accidental public exposure:

```
Block Public Access OFF (Step 1 + 2)
        ↓
    Safety guard removed
    Bucket CAN be made public
    But nothing is public yet

Bucket Policy with Principal: * (Step 3)
        ↓
    Access explicitly granted
    Bucket IS now public
```

If Block Public Access is ON, even a bucket policy with `Principal: *` is ignored by AWS. Both must be configured for public access to work.

---

## ⚠️ Revert After Demo - Important

After your demo immediately revert everything:

**Remove the bucket policy:**
- S3 → bucket → Permissions → Bucket policy → Edit → Delete all content → Save

**Turn Block Public Access back ON at bucket level:**
- S3 → bucket → Permissions → Block public access → Edit → Check all 4 → Save

**Turn Block Public Access back ON at account level:**
- S3 → Block Public Access settings for this account → Edit → Check all 4 → Save

**Or simply delete the bucket entirely if it was only for testing.**

---

## Summary

```
Step 1 → Turn off Block Public Access at Account level
Step 2 → Turn off Block Public Access at Bucket level
Step 3 → Add Bucket Policy with Principal: *
Step 4 → Verify via incognito browser
Step 5 → REVERT everything immediately after demo
```
