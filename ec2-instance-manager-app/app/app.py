from flask import Flask, render_template, jsonify, request
import boto3
import os
from botocore.exceptions import ClientError

app = Flask(__name__)


# Initialize AWS clients
def get_ec2_client():
    return boto3.client('ec2',
        region_name='us-east-1',  # Replace with your region
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

def get_s3_client():
    return boto3.client('s3',
        region_name='us-east-1',  # Replace with your region
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
    print("AWS credentials are not set. Please set the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
    raise Exception("AWS credentials are not set. Please set the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")

# Load default instance ID from S3
def get_default_instance_id():
    try:
        response = get_s3_client().get_object(Bucket='erpnext-instance-ip-20250105030818646100000001', Key='instance-id.txt')
        with response['Body'] as f:
            return f.read().decode('utf-8').strip()
    except ClientError as e:
        print(f"Error loading default instance ID: {e}")
        return None

DEFAULT_INSTANCE_ID = get_default_instance_id()

if DEFAULT_INSTANCE_ID is None:
    raise Exception("Default Instance ID not found. Please check the instance_id.txt file.")

def get_instance_info(instance_id):
    ec2 = get_ec2_client()
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        return {
            'state': instance['State']['Name'],
            'public_ip': instance.get('PublicIpAddress', 'Not available'),
            'status': 'success'
        }
    except ClientError as e:
        return {'status': 'error', 'message': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    instance_id = request.args.get('instance_id', DEFAULT_INSTANCE_ID)
    return jsonify(get_instance_info(instance_id))

@app.route('/api/start')
def start_instance():
    instance_id = request.args.get('instance_id', DEFAULT_INSTANCE_ID)
    ec2 = get_ec2_client()
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        return jsonify({'status': 'success', 'message': 'Instance starting'})
    except ClientError as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/stop')
def stop_instance():
    instance_id = request.args.get('instance_id', DEFAULT_INSTANCE_ID)
    ec2 = get_ec2_client()
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        return jsonify({'status': 'success', 'message': 'Instance stopping'})
    except ClientError as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=False)
    app.run(host='0.0.0.0', port=4999, debug=True)
