# S3 Access Patterns - A Progressive Guide

---

## The Core Question

> "I have data in S3. How do I share it or give access to it?"

This guide walks through 4 progressively better and more secure ways to share S3 data, starting from the most dangerous and moving towards industry best practices.

---

## The Story

Imagine you are a data engineer at a company. You have processed sales data sitting in your S3 bucket `sanjay-de-bucket-2026`. Different people and systems need access to this data in different ways. Each scenario below represents a real world situation you will face.

---

## Scenario 1 - Making the Bucket Public

### The Situation
You are new to AWS and want to quickly share your data with someone. You make the bucket public so anyone can access it via a URL.

### How it works
- Turn off Block Public Access at account and bucket level
- Add bucket policy with `Principal: *`
- Anyone on the internet can access your data

### Why this is dangerous
- Every person, bot, and scraper on the internet can access your data
- Bots discover public buckets within minutes and start hitting them
- Every GET request costs money - millions of requests = massive bill overnight
- Sensitive data exposed permanently once scraped

### Real Incidents
- **Twitch (2021)** - Misconfigured S3 bucket exposed 125 GB of source code and creator payout data
- **Capital One (2019)** - Misconfigured S3 access exposed 100 million customer records, $80 million fine
- **Bill Shock** - Developers regularly report $3,000+ overnight bills from public buckets being scraped by bots

### When to use
- Almost never in production
- Only for truly public datasets like open government data or public research datasets
- Static website hosting with non-sensitive content

### Verdict
❌ Never use for sensitive or internal data

---

## Scenario 2 - Cross Account Access via Bucket Policy

### The Situation
Your company has two AWS accounts - a data engineering account and an analytics account. The analytics team needs to query your S3 data from their account using Athena. You want to give only their account access, not the entire internet.

### How it works
- Add bucket policy in your account (Account A) trusting the analytics account (Account B)
- Users in Account B with S3 permissions can access the bucket
- Access is restricted to specific AWS accounts only, not the public internet

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCrossAccountList",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::<account-b-id>:root"
            },
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::sanjay-de-bucket-2026"
        },
        {
            "Sid": "AllowCrossAccountRead",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::<account-b-id>:root"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::sanjay-de-bucket-2026/*"
        }
    ]
}
```

### When to use
- Sharing data between internal AWS accounts within the same organization
- Analytics team in one account needs data from data engineering account
- Multi account AWS Organizations setup

### Limitations
- Only works for authenticated AWS users in the trusted account
- Cannot share with external vendors or partners who do not have AWS accounts
- Cannot share with a specific person temporarily

### Verdict
✅ Good for internal multi account access within your organization

---

## Scenario 3 - Presigned URLs

### The Situation
A vendor needs to download last month's sales report from your S3 bucket. They do not have an AWS account. You do not want to make the bucket public. You want the access to expire after 24 hours automatically.

### What is a Presigned URL
A presigned URL is a **temporary URL** that grants time-limited access to a specific S3 object. Your AWS credentials are cryptographically embedded in the URL itself. Anyone with the URL can access the object until it expires - no AWS account needed.

```
Normal S3 URL (requires authentication):
https://sanjay-de-bucket-2026.s3.ap-south-1.amazonaws.com/reports/sales.csv
→ AccessDenied for unauthenticated users

Presigned URL (temporary public access):
https://sanjay-de-bucket-2026.s3.ap-south-1.amazonaws.com/reports/sales.csv
?X-Amz-Algorithm=AWS4-HMAC-SHA256
&X-Amz-Credential=AKIAIOSFODNN7...
&X-Amz-Date=20240115T000000Z
&X-Amz-Expires=86400
&X-Amz-Signature=abc123...
→ Works for anyone until expiry
```

### How to generate

**Single file:**
```python
import boto3

s3 = boto3.client('s3', region_name='ap-south-1')

url = s3.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': 'sanjay-de-bucket-2026',
        'Key': 'reports/sales.csv'
    },
    ExpiresIn=86400  # 24 hours
)
print(url)
```

**Multiple files in a folder:**
```python
import boto3

s3 = boto3.client('s3', region_name='ap-south-1')

response = s3.list_objects_v2(
    Bucket='sanjay-de-bucket-2026',
    Prefix='reports/'
)

for obj in response['Contents']:
    url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': 'sanjay-de-bucket-2026',
            'Key': obj['Key']
        },
        ExpiresIn=86400
    )
    print(f"{obj['Key']} → {url}")
```

### Key properties
- Expires automatically - no manual cleanup needed
- Bucket stays private - only this specific URL works temporarily
- No AWS account needed by the recipient
- Can be generated for upload too (`put_object`) not just download
- Maximum expiry: 7 days

### When to use
- Sharing a specific file with an external vendor or partner temporarily
- Allowing a user to download their own report from a web application
- Giving a contractor temporary access to specific files
- Sharing data with someone outside your organization

### Limitations
- Per object only - no folder level presigned URLs
- Once shared, anyone who has the URL can access it until expiry
- Cannot revoke before expiry (unless you delete the object)

### Verdict
✅ Best option for temporary, time-limited sharing with external parties

---

## Summary - Which Access Pattern to Use

| Scenario | Access Pattern | Security Level |
|---|---|---|
| Public dataset, open data | Public Bucket Policy | ⚠️ Low |
| Internal multi account access | Cross Account Bucket Policy | ✅ Medium |
| Temporary external sharing | Presigned URL | ✅ Medium-High |

---

## The Progressive Security Journey

```
Public Bucket (anyone)
        ↓ more secure
Cross Account Policy (specific AWS accounts)
        ↓ more secure
Presigned URL (specific person, time limited)
```

> As you grow in your AWS data engineering journey, you will encounter more advanced access patterns like VPC Endpoint Policies and S3 Access Points. These will be covered in advanced modules.
