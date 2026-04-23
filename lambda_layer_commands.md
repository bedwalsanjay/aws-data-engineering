# Lambda Layer - Setup and Commands

---

## Table of Contents

1. [Setup Python 3.12 in CloudShell](#1-setup-python-312-in-cloudshell)
2. [Create and Upload Pandas Layer](#2-create-and-upload-pandas-layer)
3. [Create and Upload Requests Layer](#3-create-and-upload-requests-layer)

---

## 1. Setup Python 3.12 in CloudShell

```bash
# Install Python 3.12
sudo yum install python3.12 -y

# Set aliases so python3 and pip3 point to 3.12
echo "alias python3='python3.12'" >> ~/.bashrc
echo "alias pip3='python3.12 -m pip'" >> ~/.bashrc

# Reload .bashrc
source ~/.bashrc

# Install pip for Python 3.12
python3.12 -m ensurepip --upgrade

# Install boto3
python3.12 -m pip install boto3

# Verify
python3 --version
pip3 --version
```

---

## 2. Create and Upload Pandas Layer

```bash
# Create the python folder
mkdir python

# Install pandas into the python folder
pip3 install pandas -t python/

# Zip the python folder
zip -r pandas.zip python/

# Upload to S3
aws s3 cp pandas.zip s3://YOUR-BUCKET-NAME/layers/pandas.zip
```

> After uploading to S3, go to Lambda Console → Layers → Create layer → Upload from S3.

---

## 3. Create and Upload Requests Layer

```bash
# Clean up previous python folder
rm -rf python

# Create fresh python folder
mkdir python

# Install requests into the python folder
pip3 install requests -t python/

# Zip the python folder
zip -r requests.zip python/

# Upload to S3
aws s3 cp requests.zip s3://YOUR-BUCKET-NAME/layers/requests.zip
```

> After uploading to S3, go to Lambda Console → Layers → Create layer → Upload from S3.

---

## Important Notes

- Always build layers in **CloudShell or Linux** - never on Windows
- Windows builds produce Windows binaries that fail on Lambda
- The folder must be named **`python`** - Lambda requires this exact name
- Replace `YOUR-BUCKET-NAME` with your actual S3 bucket name
- Match the Python version used here with your Lambda function runtime
