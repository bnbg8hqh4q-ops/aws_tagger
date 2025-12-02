import boto3
import json
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name='us-east-1'):
    """Retrieve a secret from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            return response['SecretString']
        return response['SecretBinary']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        raise e

def create_secret(secret_name, secret_value, region_name='us-east-1'):
    """Create a new secret in AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    
    try:
        client.create_secret(Name=secret_name, SecretString=secret_value)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceExistsException':
            # Update existing secret
            client.update_secret(SecretId=secret_name, SecretString=secret_value)
            return True
        raise e

def store_profile_credentials(profile_name, access_key, secret_key, region_name='us-east-1'):
    """Store AWS profile credentials in Secrets Manager"""
    secret_name = f"aws-tagger/profiles/{profile_name}"
    secret_value = json.dumps({
        'access_key_id': access_key,
        'secret_access_key': secret_key
    })
    return create_secret(secret_name, secret_value, region_name)

def get_profile_credentials(profile_name, region_name='us-east-1'):
    """Retrieve AWS profile credentials from Secrets Manager"""
    secret_name = f"aws-tagger/profiles/{profile_name}"
    secret_value = get_secret(secret_name, region_name)
    if secret_value:
        return json.loads(secret_value)
    return None

def delete_profile_credentials(profile_name, region_name='us-east-1'):
    """Delete AWS profile credentials from Secrets Manager"""
    secret_name = f"aws-tagger/profiles/{profile_name}"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    
    try:
        client.delete_secret(SecretId=secret_name, ForceDeleteWithoutRecovery=True)
        return True
    except ClientError:
        return False
