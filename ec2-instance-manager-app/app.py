from flask import Flask, render_template, jsonify, request
import boto3
import os
from botocore.exceptions import ClientError
import sqlite3
from contextlib import contextmanager

app = Flask(__name__)


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

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise Exception("AWS credentials are not set. Please set the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")

# Configuration storage
DATABASE = 'instance_configs.db'
TABLE_NAME = 'configs'

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if table exists
        cursor.execute(f'''
            SELECT count(name) FROM sqlite_master 
            WHERE type='table' AND name='{TABLE_NAME}'
        ''')
        if cursor.fetchone()[0] == 0:
            cursor.execute(f'''
                CREATE TABLE {TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_id TEXT,
                    s3_bucket TEXT,
                    s3_key TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_viewed TIMESTAMP
                )
            ''')
            conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    try:
        yield conn
    finally:
        conn.close()

init_db()  # Initialize the database

def get_config_to_dict(row):
    return {
        'id': row[0],
        'instance_id': row[1],
        's3_bucket': row[2],
        's3_key': row[3]
    }

def load_configs(sort_by_last_viewed=True):
    with get_db() as conn:
        cursor = conn.cursor()
        if sort_by_last_viewed:
            cursor.execute(f'''
                SELECT id, instance_id, s3_bucket, s3_key 
                FROM {TABLE_NAME} 
                ORDER BY last_viewed DESC NULLS LAST, created_at DESC
            ''')
        else:
            cursor.execute(f'''
                SELECT id, instance_id, s3_bucket, s3_key 
                FROM {TABLE_NAME} 
                ORDER BY created_at DESC
            ''')
        rows = cursor.fetchall()
        return [get_config_to_dict(row) for row in rows]

def save_config(config):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'INSERT INTO {TABLE_NAME} (instance_id, s3_bucket, s3_key) VALUES (?, ?, ?)',
            (config.get('instance_id'), config.get('s3_bucket'), config.get('s3_key'))
        )
        conn.commit()

def get_instance_id_from_config(config):
    instance_id = None
    # If direct instance ID is configured, use it
    if config.get('instance_id'):
        instance_id = config['instance_id']
    # If S3 configuration exists, try to load from S3
    if config.get('s3_bucket') and config.get('s3_key'):
        try:
            response = get_s3_client().get_object(
                Bucket=config['s3_bucket'],
                Key=config['s3_key']
            )
            with response['Body'] as f:
                instance_id = f.read().decode('utf-8').strip()
        except ClientError as e:
            raise Exception(f"Error loading default instance ID from S3: {e}")
    return instance_id
        
def get_default_instance_id():
    configs = load_configs(sort_by_last_viewed=True)
    # Get the active configuration (first one in the list, if any)
    if not configs:
        return None
    config = configs[0]  # Use the first config as the active one
    return get_instance_id_from_config(config)

def get_instance_info(instance_id):
    ec2 = get_ec2_client()
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        return {
            'status': 'success',
            'state': instance['State']['Name'],
            'instance_id': instance['InstanceId'],
            'public_ip': instance.get('PublicIpAddress', 'Not available')
        }
    except ClientError as e:
        return {'status': 'error', 'message': str(e)}

def get_instance_info_from_instance_id(instance_id):
    instance_info = get_instance_info(instance_id)
    if instance_info.get('status') == 'success':
        return jsonify({'status': 'success', 'instance_id': instance_id, 'instance_info': instance_info})
    return jsonify({'status': 'error', 'instance_id': instance_id, 'message': 'Invalid Instance ID'})


#====================== API endpoints

@app.route('/api/config', methods=['GET'])
def get_configs():
    return jsonify(load_configs(sort_by_last_viewed=True))

@app.route('/api/config', methods=['POST'])
def add_config():
    new_config = request.json
    save_config(new_config)
    return jsonify({'status': 'success'})

@app.route('/api/config/select/<int:config_id>', methods=['POST'])
def select_config(config_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE {TABLE_NAME} SET last_viewed = CURRENT_TIMESTAMP WHERE id = ?',
            (config_id,)
        )
        if cursor.rowcount > 0:
            selected_config_row = cursor.execute(f'SELECT * FROM {TABLE_NAME} WHERE id = ?', (config_id,)).fetchone()
            conn.commit()
            selected_config = get_config_to_dict(selected_config_row)
            instance_id = get_instance_id_from_config(selected_config)
            return get_instance_info_from_instance_id(instance_id)
    return jsonify({'status': 'error', 'message': 'Invalid configuration ID'})

@app.route('/api/config/delete/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {TABLE_NAME} WHERE id = ?', (config_id,))
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Invalid configuration ID'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status/<instance_id>')
def get_status(instance_id):
    return get_instance_info_from_instance_id(instance_id)

@app.route('/api/start/<instance_id>')
def start_instance(instance_id):
    ec2 = get_ec2_client()
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        return jsonify({'status': 'success', 'message': 'Instance starting'})
    except ClientError as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/stop/<instance_id>')
def stop_instance(instance_id):
    ec2 = get_ec2_client()
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        return jsonify({'status': 'success', 'message': 'Instance stopping'})
    except ClientError as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4999, debug=True)
