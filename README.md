```markdown
# aws_tagger

aws_tagger is a small Flask-based service that discovers AWS resources using boto3 and applies tags directly to those resources. This repository runs as a web service (see wsgi.py and app/routes.py) and contains AWS helpers under app/aws_utils.py.

Important clarifications based on the repository implementation:
- Discovery of resources is done programmatically using boto3 (no pre-read JSON configuration file).
- Tagging operations are applied directly to discovered resources via boto3 calls.
- The project does not perform a separate "search for incorrect tags" workflow — it discovers resources and applies tags according to the runtime request/parameters.

Repository layout (key files)
- wsgi.py — Flask WSGI entrypoint for running the service.
- app/routes.py — HTTP endpoints and request handlers (triggers discovery and tagging operations).
- app/aws_utils.py — boto3 wrappers and helpers for discovering resources and applying tags.
- requirements.txt — Python dependencies.

Requirements
- Python 3.8+
- Install dependencies:
  pip install -r requirements.txt
- AWS credentials available to the process (environment variables, AWS CLI profile, or instance role). The service uses boto3 and therefore follows its credential resolution order.

Running the service (development)
- From the repository root:
  export FLASK_APP=wsgi.py
  flask run --host=0.0.0.0 --port=5000

- For production, run via a WSGI server (gunicorn, uWSGI) using wsgi.py as the application entrypoint.

How it works (high level)
- HTTP requests hit endpoints in app/routes.py.
- The route handlers call helpers in app/aws_utils.py to:
  - Discover resources (EC2 instances, S3 buckets, Lambda functions, etc.) using boto3 Describe/List APIs.
  - Apply tags directly to discovered resources using the service-specific tagging APIs (CreateTags, PutBucketTagging, TagResource, etc.).

Permissions (IAM)
- The service requires IAM permissions to discover and tag resources. Typical permissions include:
  - EC2: DescribeInstances, DescribeTags, CreateTags, DescribeRegions
  - Additional Describe/List/Tag actions for any other services you want to manage
- Prefer least-privilege and scoping to specific accounts/ARNs where possible. Use an IAM role (EC2/ECS/Lambda) or an assume-role flow for cross-account usage.

Safety and best practices
- Because tags are applied directly, always test in a non-production account/region first.
- Use a narrowly scoped IAM role for the service and rotate credentials when appropriate.
- Maintain an audit trail (service logs) of tagging operations; ensure logging is enabled and captured by your observability pipeline.

Development notes
- Inspect app/routes.py to see the available endpoints, required parameters, and expected request payloads.
- Inspect app/aws_utils.py to see how boto3 clients/resources are created and which AWS APIs are used for discovery and tagging.
- Tests and additional validation can be added to ensure safe operation before applying tags at scale.

Contributing
- Report issues and feature requests.
- Create feature branches for changes and submit pull requests with clear descriptions and test coverage where applicable.
- Follow repository style and dependency constraints in requirements.txt.


Acknowledgements
- Built with boto3 and Flask. See app/aws_utils.py and app/routes.py for implementation-specific details.
```
