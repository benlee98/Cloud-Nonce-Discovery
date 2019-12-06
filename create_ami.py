#!/usr/bin/python
import boto3
from botocore.exceptions import ClientError
import time
import argparse
import os

class AmiMaker():
    def __init__(self, parser):
        self.args = parser.parse_args()
        self.name = self.args.ami
        self.ec2 = boto3.resource('ec2', region_name='us-east-2')
        self.ec2c = boto3.client('ec2', region_name='us-east-2')

    def get_instance_ids(self):
        instance_ids = []
        for instance in self.get_active_instances():
            for tag in instance.tags:
                if tag['Key'] == 'Name':
                    if tag['Value'] == self.name:
                        instance_ids.append(instance.id)
        return instance_ids

    def get_active_instances(self):
        return self.ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

    def is_image_available(self, image_id):
        try:
            available = 0
            while available == 0:
                print("AMI not yet available. Sleeping for 10 seconds...")
                time.sleep(10)
                image = self.ec2c.describe_images(ImageIds=[image_id])
                if image['Images'][0]['State'] == 'available':
                    available = 1
            if available == 1:
                print("Image is now available for use.")
                return True
        except Exception as e:
            print(e)

def main():
    parser = argparse.ArgumentParser(description='Create AMI.')
    parser.add_argument('ami', metavar='ami', help='Name of AMI')
    ami_maker = AmiMaker(parser)

    ids = ami_maker.get_instance_ids()
    for instance in ids:
        print(instance)    
    response = ami_maker.ec2c.create_image(InstanceId=ids[0], Name=ami_maker.name)
    image_id = response["ImageId"]
    ami_maker.is_image_available(image_id)

if __name__== "__main__":
  main()