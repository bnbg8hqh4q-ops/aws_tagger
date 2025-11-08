
import boto3
from .crypto_utils import decrypt

#Builds the boto3 session from profile that is loaded as parameter. 
def build_session(profile_row):
    access_key = decrypt(profile_row.access_key_id)
    secret_key = decrypt(profile_row.secret_access_key)
    return boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=profile_row.default_region or 'us-east-1'
    )
#Using created session, list all regions
def list_regions(session):
    ec2 = session.client('ec2')
    regions = ec2.describe_regions(AllRegions=True)['Regions']
    return sorted([r['RegionName'] for r in regions])

#Gets instances from AWS using boto3 session.
def fetch_instances(session, region, instance_ids=None):
    ec2 = session.client('ec2', region_name=region)
#We create and empty disctionary. That helps to check if user had instance IDs provided in a list or not. If yes then saves this to isntance_ids.
    kwargs = {}
    if instance_ids:
        kwargs['InstanceIds'] = instance_ids
    resp = ec2.describe_instances(**kwargs)
#Parsing the jason response from boto3 to a list of dictionaries.
    instances = []
    for r in resp['Reservations']:
        for inst in r['Instances']:
            instances.append({
                'InstanceId': inst['InstanceId'],
                'State': inst['State']['Name'],
                'Type': inst.get('InstanceType'),
                'AZ': inst.get('Placement', {}).get('AvailabilityZone'),
                'Name': next((t['Value'] for t in inst.get('Tags', []) if t['Key']=='Name'), ''),
            })
    return instances

#Adds the tags
def bulk_tag_instances(session, region, instance_ids, tags_dict):
    if not instance_ids:
        return 0
    ec2 = session.client('ec2', region_name=region)
    tags = [{'Key': k, 'Value': v} for k, v in tags_dict.items()]
    ec2.create_tags(Resources=instance_ids, Tags=tags)
    return len(instance_ids)
