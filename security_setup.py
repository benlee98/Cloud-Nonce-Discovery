import boto3
import json
from botocore.exceptions import ClientError
import argparse 

ec2 = boto3.client('ec2')

class Security:
    def __init__(self, parser):
        args = parser.parse_args()

        self.iam = boto3.resource('iam', region_name='us-east-2')
        self.iamc = boto3.client('iam', region_name='us-east-2')
        self.security_group = args.sg
        self.instance_profile = args.sg


    def create_security_group(self):
        exists = False
        groups_response = ec2.describe_security_groups()
        groups = groups_response['SecurityGroups']
        for group in groups:
            if group['GroupName'] == self.security_group:
                exists = True

        if not exists:
            response = ec2.describe_vpcs()
            vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

            try:
                response = ec2.create_security_group(GroupName=self.security_group,
                                                    Description='security group with tcp access for port 22',
                                                    VpcId=vpc_id)
                security_group_id = response['GroupId']
                print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))

                data = ec2.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                        {'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
                    ])
                print('Ingress Successfully Set %s' % data)
            except ClientError as e:
                print(e)
        
    def create_instance_profile(self):
        roles = self.iamc.list_roles()
        role_list = roles['Roles']
        instance_profiles = self.iamc.list_instance_profiles()
        profile_list = instance_profiles['InstanceProfiles']
        profile_role_list = []

        role_exists = False
        profile_exists = False
        profile_role_exists = False

        trust_policy={
                "Version": "2012-10-17",
                "Statement": [
                    {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                    }
                ]
            }

        for key in role_list:
            if key['RoleName'] == self.instance_profile:
                role_exists = True
        if not role_exists:
            self.iamc.create_role(
                RoleName = self.instance_profile,
                AssumeRolePolicyDocument = json.dumps(trust_policy)
            )
            self.iamc.attach_role_policy(RoleName=self.instance_profile, PolicyArn='arn:aws:iam::aws:policy/AmazonSQSFullAccess')

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.InstanceProfile.add_role
        for key in profile_list:
            if key['InstanceProfileName'] == self.instance_profile:
                profile_exists = True
                profile_role_list = key['Roles']
        if not profile_exists:
            instance_profile = self.iam.create_instance_profile(InstanceProfileName=self.instance_profile)

        for key in profile_role_list:
            if key['RoleName'] == self.instance_profile:
                profile_role_exists = True
        if not profile_role_exists:
            instance_profile = self.iam.InstanceProfile(self.instance_profile)
            instance_profile.add_role(RoleName=self.instance_profile)
            

def main():
    parser = argparse.ArgumentParser(description='Set up security groups, IAM role and IAM instance profile.')
    parser.add_argument('sg', metavar='sg', help='Name of security group')

    security = Security(parser)
    security.create_security_group()
    security.create_instance_profile()

if __name__== "__main__":
  main()
