import boto3

ec2 = boto3.resource('ec2')
sqs = boto3.resource('sqs', region_name='us-east-2')

instance_ids = []

instances = ec2.instances.filter(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
for instance in instances:
    print(instance.id, instance.instance_type, instance.public_dns_name)
    instance_ids.append(instance.id)

ec2.instances.terminate()