import os
import sys
import boto3
from botocore.exceptions import ClientError


AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Initialize AWS clients
def get_ec2_client():
    return boto3.client('ec2',
        region_name='us-east-1',  # Replace with your region
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

def get_s3_client():
    return boto3.client('s3',
        region_name='us-east-1',  # Replace with your region
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

def get_instance_info(instance_id):
    ec2 = get_ec2_client()
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        print(f"""Instance info: 
            Instance ID: {instance_id}
            State: {instance['State']['Name']}
            Public IP: {instance.get('PublicIpAddress', 'Not available')}""")
    except ClientError as e:
        print(f"Error getting instance info for {instance_id}: {str(e)}")
    
def start_instance(instance_id):
    ec2 = get_ec2_client()
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"Instance {instance_id} started")
    except ClientError as e:
        print(f"Error starting instance {instance_id}: {str(e)}")

def stop_instance(instance_id):
    ec2 = get_ec2_client()
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"Instance {instance_id} stopped")
    except ClientError as e:
        print(f"Error stopping instance {instance_id}: {str(e)}")
    

if __name__ == '__main__':

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise Exception("AWS credentials are not set. Please set the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")

    if len(sys.argv) < 3:
        print("Usage: python aws_utils.py <action> <instance-id>")
        print("Actions: start, stop, status")
        sys.exit(1)
        
    action = sys.argv[1]
    instance_id = sys.argv[2]
    
    if action == "start":
        start_instance(instance_id)
    elif action == "stop": 
        stop_instance(instance_id)
    elif action == "status":
        get_instance_info(instance_id)
    else:
        print(f"Unknown action: {action}")
        print("Valid actions are: start, stop, status")
        sys.exit(1)

