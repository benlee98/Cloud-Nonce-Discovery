#!/usr/bin/python
import boto3
from botocore.exceptions import ClientError
import time
import argparse
import subprocess
import os
import json

ec2 = boto3.resource('ec2', region_name='us-east-2')
ec2c = boto3.client('ec2', region_name='us-east-2')

def get_instance_dns(name):
    instance_ids = []
    for instance in get_active_instances():
        for tag in instance.tags:
            if tag['Key'] == 'Name':
                if tag['Value'] == name:
                    instance_ids.append(instance.public_dns_name)
    return instance_ids

def get_active_instances():
    return ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'pending']}])


def main():        
    parser = argparse.ArgumentParser(description='Setup AMI files and installations.')
    parser.add_argument('k', metavar='k', help='Name of AWS key pair')
    parser.add_argument('ami', metavar='ami', help='Name of AMI')
    args = parser.parse_args()

    dns = get_instance_dns(args.ami)
    os.system("sudo scp -i \"" + args.k + ".pem\" cloud.py ec2-user@" + dns[0] + ":")
    time.sleep(5)
    os.system("sudo ssh -t -i \"" + args.k + ".pem\" ec2-user@" + dns[0] + " \" sudo yum update && sudo yum install python3 -y && sudo pip3 install boto3\"")
    time.sleep(2)


if __name__== "__main__":
  main()