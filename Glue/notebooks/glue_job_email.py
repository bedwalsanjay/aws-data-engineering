import sys
import boto3
from awsglue.utils import getResolvedOptions

# Get job parameters
args = getResolvedOptions(sys.argv, ['S3_BUCKET', 'S3_KEY', 'SNS_TOPIC_ARN'])

# Initialize AWS clients
s3 = boto3.client('s3')
sns = boto3.client('sns')

def check_file_and_notify(bucket, key, topic_arn):
    response = s3.head_object(Bucket=bucket, Key=key)
    print(type(response))
    print(f"Response: {response}")
    file_size = response.get('ContentLength', 0)

    if file_size == 0:
        message = f"The file {key} in bucket {bucket} is empty."
        sns.publish(TopicArn=topic_arn, Message=message)
        print(f"Notification sent: {message}")
    else:
        print(f"File {key} has size {file_size} bytes. No action needed.")

# Run the check
check_file_and_notify(args['S3_BUCKET'], args['S3_KEY'], args['SNS_TOPIC_ARN'])