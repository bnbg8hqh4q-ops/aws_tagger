# Feature Flags

This application supports feature flags to enable/disable certain functionality.

## Available Feature Flags

### USE_SECRETS_MANAGER
**Default:** `false`

When enabled, the application will:
- Store Flask secret key in AWS Secrets Manager instead of local file
- Store user AWS credentials in AWS Secrets Manager instead of encrypted in SQLite database

**Benefits:**
- Centralized secret management
- Better security (secrets not stored in application files or database)
- Easier secret rotation
- Audit trail via CloudTrail

**Requirements:**
- EC2 instance must have IAM permissions for Secrets Manager:
  - `secretsmanager:GetSecretValue`
  - `secretsmanager:CreateSecret`
  - `secretsmanager:UpdateSecret`
  - `secretsmanager:DeleteSecret`

**Usage:**
```bash
# Enable via environment variable
export USE_SECRETS_MANAGER=true

# Or in .ebextensions/01_flask.config
aws:elasticbeanstalk:application:environment:
  USE_SECRETS_MANAGER: "true"
```

**Secret Names:**
- Flask secret: `aws-tagger/flask-secret`
- Profile credentials: `aws-tagger/profiles/{profile_name}`

### USE_RDS_DATABASE
**Default:** `false`

When enabled, the application will use RDS instead of local SQLite database.

**Note:** This feature is planned but not yet implemented.

## Configuration

Feature flags are configured via environment variables in `app/config.py`.

To enable a feature flag in Elastic Beanstalk, add it to `.ebextensions/01_flask.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    USE_SECRETS_MANAGER: "true"
    AWS_REGION: "us-east-1"
    FLASK_SECRET_NAME: "aws-tagger/flask-secret"
```

## Migration

### Migrating to Secrets Manager

If you have existing profiles in the database and want to migrate to Secrets Manager:

1. Enable the feature flag
2. Existing profiles will continue to work (they use encrypted storage)
3. New profiles will be stored in Secrets Manager
4. To migrate existing profiles, delete and re-create them

The application supports mixed mode - some profiles can use encrypted storage while others use Secrets Manager.
