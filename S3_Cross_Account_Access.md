# S3 Cross Account Access - Step by Step

---

## Overview

This guide covers how to grant access to an S3 bucket in one AWS account to principals (users/roles) in a different AWS account.

---

## How Cross Account S3 Access Works

Cross account access requires **both sides** to allow access:

```
Account A (bucket owner)
    Bucket Policy → "I allow Account B to access me"
            ↓
Account B (requester)
    IAM Policy → "I allow my users to access Account A's bucket"
            ↓
    Access Granted
```

Think of it as two doors. Both must be unlocked for access to work.

---

## When is Each Side Required

| Bucket Policy Principal | Account B IAM Policy needed |
|---|---|
| `:root` + user has `AdministratorAccess` or `AmazonS3FullAccess` | Not needed, existing policy is enough |
| `:root` + user has zero or unrelated permissions | Yes, mandatory |
| `:root` + user has specific cross account policy | Works |
| Specific user/role ARN | Not needed |
| `*` (everyone/public) | No |

---

## Step 1 - Add Bucket Policy in Account A

This tells the bucket to allow Account B in.

- S3 → `sanjay-de-bucket-2026` → **Permissions** tab
- Scroll to **Bucket policy** → **Edit**
- Paste the following:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCrossAccountList",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::526844078262:root"
            },
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::sanjay-de-bucket-2026"
        },
        {
            "Sid": "AllowCrossAccountRead",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::526844078262:root"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::sanjay-de-bucket-2026/*"
        }
    ]
}
```

- Click **Save changes**

> `arn:aws:iam::526844078262:root` means the entire Account B, not just the root user. Any principal in Account B can potentially access the bucket but only if their IAM policy also allows it.

---

## Alternative - Trust a Specific User Directly

If you want to skip the IAM policy in Account B, you can trust a specific user directly in the bucket policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSpecificUser",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::526844078262:user/sanjay-dev"
            },
            "Action": [
                "s3:ListBucket",
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::sanjay-de-bucket-2026",
                "arn:aws:s3:::sanjay-de-bucket-2026/*"
            ]
        }
    ]
}
```

---

## Cross Account Access vs Public Access

| | Cross Account Access | Public Access |
|---|---|---|
| Who can access | Only specific AWS account(s) | Everyone on the internet |
| Authentication required | Yes, must be authenticated in Account B | No, anyone |
| Principal in bucket policy | Specific account/user ARN | `*` |
| Block Public Access needs to be OFF | No | Yes |
| Risk level | Low | High |
| Use case | Sharing data between teams/accounts | Static websites, public datasets |

---

## Summary

```
Step 1 → Add Bucket Policy in Account A
         Principal: arn:aws:iam::<account-b-id>:root
         Actions: s3:ListBucket, s3:GetObject

Account B user must have either AmazonS3FullAccess, AdministratorAccess
or the following specific policy attached:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListBucket",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::sanjay-de-bucket-2026"
        },
        {
            "Sid": "GetObject",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::sanjay-de-bucket-2026/*"
        }
    ]
}
```
```
