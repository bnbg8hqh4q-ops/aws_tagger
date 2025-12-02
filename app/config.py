import os

# Feature Flags
FEATURE_FLAGS = {
    'USE_SECRETS_MANAGER': os.environ.get('USE_SECRETS_MANAGER', 'false').lower() == 'true',
    'USE_RDS_DATABASE': os.environ.get('USE_RDS_DATABASE', 'false').lower() == 'true',
}

# AWS Secrets Manager Configuration
SECRETS_MANAGER_REGION = os.environ.get('AWS_REGION', 'us-east-1')
FLASK_SECRET_NAME = os.environ.get('FLASK_SECRET_NAME', 'aws-tagger/flask-secret')
