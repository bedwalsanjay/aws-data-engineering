# IAM Role Switching and SSO - Notes

---

## 1. IAM User Role Switching - Step by Step

Scenario: IAM user `sanjay-dev` assumes a role called `s3-full-access-role` to access S3.

### Step 1 - Create the IAM Role
- IAM Console → **Roles** → **Create Role**
- Trusted entity type → **AWS Account** → **This account**
- Attach policy → `AmazonS3FullAccess`
- Name the role → `s3-full-access-role`
- Create Role

### Step 2 - Edit the Role Trust Policy
The trust policy defines who is allowed to assume this role.

- IAM → Roles → `s3-full-access-role` → **Trust relationships** → **Edit**
- Replace with:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/sanjay-dev"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

> Replace `123456789012` with your actual AWS Account ID.

### Step 3 - Give the IAM User Permission to Assume the Role (Only needed for cross-account)

For same account - trust policy alone is sufficient, skip this step.
For cross-account - attach this inline policy to the user:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": [
                "arn:aws:iam::361116840744:role/swtichroleDataEngineer",
                "arn:aws:iam::361116840744:role/dataEngineer"
            ]
        }
    ]
}

```

**How to create inline policy:**
- IAM → Users → `sanjay-dev` → **Permissions** tab
- Add permissions → **Create inline policy**
- Click **JSON** tab → paste the policy above
- Click Next → name it `allow-assume-s3-role` → **Create policy**

### Step 4 - Assume the Role via Console
- Login as `sanjay-dev`
- Top right → account menu → **Switch Role**
- Enter Account ID and Role name (`s3-full-access-role`)
- Click **Switch Role**
- To go back → top right → **Switch Back**

---

## 2. Same Account vs Cross Account Role Assumption

| Scenario | Trust Policy | sts:AssumeRole on User |
|---|---|---|
| Same account | Required | Not required |
| Cross account | Required | Also required |

**Why same account works without the permission:**
> AWS treats it as - the account owner already approved this by setting up the trust policy. For cross-account, both sides must explicitly allow it.

---

## 3. How Role Assumption Works Under the Hood

```
sanjay-dev (IAM User)
    ↓ calls sts:AssumeRole
AWS STS (Security Token Service)
    ↓ checks trust policy on role
    ↓ checks user has sts:AssumeRole permission (cross-account only)
    ↓ issues temporary credentials
sanjay-dev now acts as s3-full-access-role
    ↓ temporary creds expire after session duration
sanjay-dev back to original permissions
```

---

## 4. IAM User Role Switch vs SSO Role Switch

Both use STS to issue temporary credentials under the hood but the mechanism and setup are completely different.

| | IAM User Role Switch | SSO / Federation Role Switch |
|---|---|---|
| Identity lives in | AWS IAM | Okta / Azure AD / IAM Identity Center |
| Login page | console.aws.amazon.com | Company SSO portal |
| IAM user needed | Yes | No |
| Role selection | Manual (type role name) | Radio buttons / dropdown |
| Used in | Personal accounts, small teams | Enterprises, client projects |
| Multi-account | Possible but manual | Built-in, seamless |
| MFA | Per IAM user | Handled by IdP |
| Setup complexity | Simple | Complex (admin sets it up) |

---

## 5. What is SAML?

SAML stands for **Security Assertion Markup Language**. It is an open standard (XML based) for exchanging authentication and authorization data between two parties.

- Allows you to login once and access multiple applications - called **Single Sign On (SSO)**
- Version used everywhere today is **SAML 2.0**

**Two key roles in SAML:**

| Term | What it means | Example |
|---|---|---|
| Identity Provider (IdP) | The one who verifies your identity | Okta, Azure AD, IAM Identity Center |
| Service Provider (SP) | The service you want to access | AWS Console, Salesforce, GitHub |

> SAML is like a passport. Your government (IdP) issues it and verifies who you are. When you travel (SP), they trust the passport without needing to verify you themselves.

---

## 6. SAML 2.0 Flow - Architecture Diagram

```
─────────────────────────────────────────────────────────────────
                    SAML 2.0 FLOW WITH IAM IDENTITY CENTER
─────────────────────────────────────────────────────────────────

  YOUR BROWSER
  ┌─────────────┐
  │    User     │
  │  sanjay-dev │
  └──────┬──────┘
         │
         │ 1. Go to SSO Portal URL
         │    https://d-xxxxx.awsapps.com/start
         ▼
─────────────────────────────────────────────────────────────────
  IDENTITY PROVIDER (IdP) [ OKTA , PING etc]
  ┌──────────────────────────────────────────┐
  │         AWS IAM Identity Center          │
  │                                          │
  │  ┌────────────┐     ┌─────────────────┐  │
  │  │   Users    │     │     Groups      │  │
  │  │ sanjay-dev │────▶│ data-engineers  │  │
  │  └────────────┘     └─────────────────┘  │
  │                                          │
  │  2. Verify username + password           │
  │  3. Check what accounts + roles          │
  │     this user is assigned to            │
  │                                          │
  │  4. Generate SAML Assertion (XML token)  │
  │     "This is sanjay-dev,                 │
  │      allow role: AdminAccess"            │
  └──────────────────────────────────────────┘
         │
         │ 5. SAML Assertion sent back to browser
         │    (encrypted XML document)
         ▼
  YOUR BROWSER
  ┌──────────────────────────────┐
  │                              │
  │  6. Shows you role list      │
  │     across all accounts      │──────────────────────────────┐
  │                              │  User picks one role         │
  │  Dev Account (123456789012)  │                              │
  │  🔘 dev_admin                │                              │
  │  🔘 dev_readonly             │                              │
  │                              │                              │
  │  Prod Account (987654321098) │                              │
  │  🔘 prod_readonly            │                              │
  │                              │                              │
  │  Data Account (112233445566) │                              │
  │  🔘 data_engineer            │                              │
  └──────────────────────────────┘                              │
                                                                │
         ┌──────────────────────────────────────────────────────┘
         │ 7. Browser posts SAML Assertion to AWS
         ▼
─────────────────────────────────────────────────────────────────
  SERVICE PROVIDER (SP)
  ┌──────────────────────────────────────────┐
  │               AWS STS                    │
  │       (Security Token Service)           │
  │                                          │
  │  8. Validates SAML Assertion             │
  │  9. Checks IAM Role trust policy         │
  │     (does it trust this IdP?)            │
  │  10. Issues temporary credentials        │
  │      - AccessKeyId                       │
  │      - SecretAccessKey                   │
  │      - SessionToken                      │
  │      - Expiry (1-12 hours)               │
  └──────────────────────────────────────────┘
         │
         │ 11. Temporary credentials used to
         │     access AWS Console / CLI
         ▼
─────────────────────────────────────────────────────────────────
  SUMMARY OF STEPS
─────────────────────────────────────────────────────────────────

  1.  User hits SSO portal URL
  2.  IdP verifies identity (username + password + MFA)
  3.  IdP checks user's assigned accounts and roles
  4.  IdP generates SAML Assertion (signed XML token)
  5.  SAML Assertion returned to browser
  6.  User selects a role from the list
  7.  Browser sends SAML Assertion to AWS STS
  8.  STS validates the assertion
  9.  STS checks IAM role trust policy
  10. STS issues temporary credentials
  11. User accesses AWS with those credentials

─────────────────────────────────────────────────────────────────
```

**Key things to note:**
- The user's password never goes to AWS - it only goes to the IdP
- AWS only receives the SAML Assertion (a signed token saying "trust this user")
- Temporary credentials are issued every session - no permanent access keys
- One user can access multiple AWS accounts with different roles from one portal
- If the user is removed from Identity Center, they instantly lose access to all accounts

---

## 7. IAM Identity Center Setup - Step by Step

### Step 1 - Enable IAM Identity Center
- AWS Console → search **IAM Identity Center** → Open
- Click **Enable**
- Pick a region and stick with it (e.g., `us-east-1`)
- Click **Enable IAM Identity Center**
- Note: This requires AWS Organizations to be enabled - AWS will prompt you automatically

### Step 2 - Create Users
- Left sidebar → **Users** → **Add user**
- Fill in username, email, first and last name
- AWS sends a verification email → open it → set password
- This user is separate from your IAM user, it lives inside Identity Center

### Step 3 - Create Groups
- Left sidebar → **Groups** → **Create group**
- Name it e.g., `data-engineers`
- Add your user to the group

### Step 4 - Create Permission Sets
Permission sets are role templates that define what access a user gets when they log in.

- Left sidebar → **Permission sets** → **Create permission set**
- Choose **Predefined permission set**
- Select `AdministratorAccess` → Next → Name it `AdminAccess` → Create
- Repeat and create a second one with `ReadOnlyAccess`

### Step 5 - Assign User to AWS Account with Permission Sets
- Left sidebar → **AWS accounts**
- Select your account → **Assign users or groups**
- Select your user → Next
- Select both permission sets → Submit
- AWS auto-creates IAM roles behind the scenes for each permission set

### Step 6 - Find Your SSO Portal URL
- Left sidebar → **Dashboard**
- Copy the **AWS access portal URL**:
  ```
  https://d-xxxxxxxxxx.awsapps.com/start
  ```
- Optionally customize it via Settings → Configure

### Step 7 - Login via SSO Portal
- Open a new incognito window
- Go to your portal URL
- Login with Identity Center user credentials
- You will see the role selection page grouped by AWS account
- Click any role → Management Console → you are in with that role's permissions

### Step 8 - Configure AWS CLI with SSO (Bonus)
```bash
aws configure sso

# SSO session name: my-sso
# SSO start URL: https://d-xxxxxxxxxx.awsapps.com/start
# SSO region: us-east-1
# SSO registration scopes: press enter (default)
```
- Browser opens → login → authorize
- Select account and role from CLI

```bash
# Use the SSO profile
aws s3 ls --profile my-sso

# Or set as default for the session
export AWS_PROFILE=my-sso
```

---

## 8. Does IAM Identity Center Cost Money?

**No. Completely free.**

| Component | Cost |
|---|---|
| IAM Identity Center | Free |
| Users and Groups | Free |
| Permission Sets | Free |
| SSO Portal | Free |
| AWS Organizations | Free |
| CLI SSO sessions | Free |

> Only costs money if you spin up paid AWS services (EC2, Redshift etc.) after logging in via SSO. The SSO setup itself is zero cost.

---

## 9. Free Identity Provider Options for Individual Practice

| IdP | Free Plan | Complexity |
|---|---|---|
| AWS IAM Identity Center | Free, built into AWS | Easiest |
| Okta | Free developer account (up to 100 users) | Easy |
| Azure AD | Free tier available | Medium |
| Keycloak | Fully free, self-hosted | Medium |

**Recommended learning path:**
1. Start with **IAM Identity Center** - 30 mins setup, exact enterprise experience
2. Then try **Okta + AWS** - closest to real client project setup, 1-2 hours

---

## 10. Key Concepts Summary

| Concept | Description |
|---|---|
| Trust Policy | JSON on the role that defines who can assume it |
| sts:AssumeRole | Permission needed by user to assume a role (cross-account only) |
| SAML Assertion | Signed XML token that proves who you are |
| IdP | Verifies your identity (Identity Center, Okta) |
| SP | Service you want to access (AWS) |
| STS | AWS service that issues temporary credentials |
| Permission Set | Role template in Identity Center |
| SSO Portal | The page with radio buttons to pick a role |
| Temporary Credentials | Short-lived keys issued per session, no permanent access keys |
