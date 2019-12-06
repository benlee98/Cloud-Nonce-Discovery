#!/usr/bin/python
import boto3
from botocore.exceptions import ClientError
import argparse
import time
import datetime
import threading
import json
import math

# Price per second of t2.micro instance
t2_micro_price_rate = 0.0116/3600
throughput_estimate = 330000
startup_time_estimate = 39

# function calculates the workload splits
def split_into_parts(n, p):
    return [n//p + 1] * (n%p) + [n//p] * (p - n%p)

class Hunter:
    def __init__(self, parser):
        args = parser.parse_args()
        self.image_id = ''
        self.security_group = args.ami
        self.max_val = 2**32
        self.region_name = 'us-east-2'
        # Create ec2 resource and client
        self.ec2 = boto3.resource('ec2', region_name=self.region_name)
        self.ec2c = boto3.client('ec2', region_name=self.region_name)

        self.instance_profile = args.ami

        self.key = args.k

        self.t0 = time.time()

        # Create SQS resource and client
        self.sqs = boto3.resource('sqs', region_name=self.region_name)
        self.sqsc = boto3.client('sqs', region_name=self.region_name)

        self.iam = boto3.resource('iam', region_name=self.region_name)
        self.iamc = boto3.client('iam', region_name=self.region_name)

        self.ami_name = args.ami

        # input queue to send from local to remote instances
        # output queue to send from remote instances to local
        # timing queues for timing remote instances to gather metrics
        self.input_queue = self.sqs.create_queue(QueueName='input_queue')
        self.output_queue = self.sqs.create_queue(QueueName='output_queue')
        self.run_timing_queue = self.sqs.create_queue(QueueName='run_timing_queue')

        self.date_time_string = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        self.difficulty = args.d
        self.vm_count = args.n
        self.confidence = args.c
        self.time_limit = args.t
        self.cost_limit = args.p

        self.t_override = self.time_limit != -1
        self.force_closure = False

        self.index_search_count = 0

        self.all_processes = []

        self.result = -1
        self.ri1 = -1
        self.ri2 = -1
        self.ti1 = -1
        self.ti2 = -1
        self.run_time = -1
        self.calc_time = -1
        self.setup_time = -1
        self.time_taken = -1

        self.results_processed = 0


    def get_ami_id(self):
            response = self.ec2c.describe_images(Owners=['self'])
            for ami in response['Images']:
                if ami['Name'] == self.ami_name:
                    self.image_id = ami['ImageId']

    def shut_down(self):
        self.input_queue.delete(QueueUrl=self.input_queue.url)
        self.output_queue.delete(QueueUrl=self.output_queue.url)
        self.run_timing_queue.delete(QueueUrl=self.run_timing_queue.url)
        instance_ids = []
        for instance in self.get_active_instances():
            print(instance.id, instance.instance_type, instance.public_dns_name)
            instance_ids.append(instance.id)
        self.ec2.instances.terminate()


    def get_active_instances(self):
        return self.ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'pending']}])

    def process_user_data(self):
        # script to be run on instance start
        f = open("user_data.sh", "r")
        self.user_data = f.read()
        self.user_data += ' '
        self.user_data += str(self.difficulty)

    def check_iam_role(self):
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

    def create_instances(self):
        self.check_iam_role()
        # Start EC2 instances for CND processing
        self.ec2.create_instances(ImageId=self.image_id, MinCount = 1, MaxCount = self.vm_count, InstanceType='t2.micro', 
            KeyName=self.key, SecurityGroups=[self.security_group], UserData=self.user_data,
            IamInstanceProfile = {
                'Name': self.instance_profile
            })
    
    def early_shutdown(self):
        # print out number of vms, time searches and number of indices searched 
        if self.force_closure:
            self.time_taken = self.get_time_taken()
        elif self.t_override:
            self.time_taken = self.time_limit
        elif self.cost_limit != -1:
            self.time_taken = self.cost_limit/t2_micro_price_rate
        self.shut_down()
        self.log('early_shutdown_log.txt', early_shutdown=True)

    def get_time_taken(self):
        return time.time() - self.t0

    def countdown_timer(self, t, now=datetime.datetime.now):
        t = int(t)
        target = now()
        one_second_later = datetime.timedelta(seconds=1)
        for remaining in range(t, 0, -1):
            target += one_second_later
            print(datetime.timedelta(seconds=remaining), 'remaining')
            time.sleep((target - now()).total_seconds())
        self.early_shutdown()
        print('\nTIMER ended')
        for process in self.all_processes: 
            process.terminate() 

    def distribute_work(self):
        instances = self.get_active_instances()
        active_count = len([instance for instance in instances])
        print('Number of vm\'s started:', active_count)
        split_list = split_into_parts(self.max_val, active_count)
        start = 0
        # Send workload values (search range)
        for x, instance in enumerate(instances):
            self.input_queue.send_message(MessageBody='find a nonce', MessageAttributes = {
                'Start': {
                    'DataType': 'Number',
                    'StringValue': str(start)
                },
                'End': {
                    'DataType': 'Number',
                    'StringValue': str(start + split_list[x])
                }
            })
            print("start: ", start)
            print("end: ", start + split_list[x])
            start += split_list[x]

            print('Message number:', x)

    def receive_result(self):
        # Receive nonce results back
        while self.result == -1:
            print('polling output queue...')
            for message in self.output_queue.receive_messages(MessageAttributeNames=['Result', 'Start', 'End'], MaxNumberOfMessages=1, WaitTimeSeconds=20):
                print('result received from remote instance')
                if message.message_attributes is not None:
                    print('message attributes not none')
                    self.result = int(message.message_attributes.get('Result').get('StringValue'))
                    self.ri1 = int(message.message_attributes.get('Start').get('StringValue'))
                    self.ri2 = int(message.message_attributes.get('End').get('StringValue'))
                message.delete()
                self.results_processed += 1
            if self.results_processed == self.vm_count:
                break

        if (self.result != -1):
            print('Result is', self.result)
        else:
            print('Nothing returned')

    def receive_timing_info(self):
        while self.ti1 != self.ri1:
            for message in self.run_timing_queue.receive_messages(MessageAttributeNames=['total_time', 'calc_time', 'setup_time', 'Start', 'End'], MaxNumberOfMessages=1, WaitTimeSeconds=20):
                # Get the custom author message attribute if it was set
                print('timing information received from remote instance')
                if message.message_attributes is not None:
                    self.run_time = message.message_attributes.get('total_time').get('StringValue')
                    self.calc_time = message.message_attributes.get('calc_time').get('StringValue')
                    self.setup_time = message.message_attributes.get('setup_time').get('StringValue')
                    self.ti1 = int(message.message_attributes.get('Start').get('StringValue'))
                    self.ti2 = int(message.message_attributes.get('End').get('StringValue'))
                message.delete()


    def log(self, filename, early_shutdown=False):
        f = open(filename,"a+")
        f.write('date&time:')
        f.write(self.date_time_string)
        if (self.result == -1):
            f.write(', failed to find nonce')
        else:
            f.write(', shutdown reason:')
            if self.force_closure:
                f.write('Forced shutdown')
            elif self.t_override:
                f.write('Time limit reached')
            elif self.cost_limit != -1:
                f.write('Cost limit reached') 
            else:
                f.write('Result found')
            
        f.write(', difficulty:')
        f.write(str(self.difficulty))
        f.write(', vm_count:')
        f.write(str(self.vm_count))
        f.write(', index_search_count_estimate:')
        f.write(str(int(throughput_estimate * self.time_taken * self.vm_count)))
        if early_shutdown:
            f.write(', time_taken:')
            f.write(str(self.time_taken))
        else:
            f.write(', result:')
            f.write(str(self.result))
            f.write(', result_start:')
            f.write(str(self.ri1))
            f.write(', result_end:')
            f.write(str(self.ri2))
            f.write(', time_start:')
            f.write(str(self.ti1))
            f.write(', time_end:')
            f.write(str(self.ti2))
            f.write(', total_run_time:')
            f.write(str(self.run_time))
            f.write(', calc_time:')
            f.write(str(self.calc_time))
            f.write(', setup_time:')
            f.write(str(self.setup_time))
            f.write(', local_time:')
            f.write(str(self.time_taken))
        f.write('\n\n')
        f.close() 

    def hunt(self):  
        self.get_ami_id()
        self.process_user_data()
        self.create_instances()
        self.distribute_work()
        self.receive_result()
        self.receive_timing_info()
        self.time_taken = self.get_time_taken()
        print('Local time taken:', self.time_taken)

    def hunt_with_p(self):
        # number of indices necessary to search
        k = math.log(1-self.confidence)/math.log(1-math.pow(0.5, self.difficulty))
        x = k/throughput_estimate
        self.vm_count = int(math.ceil(x/(self.time_limit + startup_time_estimate)))
        print(self.vm_count)

    def start(self):
        if self.time_limit == -1 and self.cost_limit == -1:
            print('standard operation')
            self.hunt()
            self.log('cloud_timings.txt')
            self.shut_down()
        elif self.confidence != -1 and self.time_limit != -1 and self.cost_limit == -1:
            print('confidence set no cost limit')
            self.hunt_with_p()
            self.hunt()
        elif self.confidence != -1 and self.time_limit != -1 and self.cost_limit != -1:
            print('confidence and cost limit set')
            t1 = threading.Thread(target = self.hunt_with_p, args = ())
            t1.daemon = True
            t1.start()
            self.countdown_timer(self.cost_limit/t2_micro_price_rate)
        else:
            t1 = threading.Thread(target = self.hunt, args = ())
            t1.daemon = True
            t1.start()
            if self.t_override:
                self.countdown_timer(self.time_limit)
                print('time limit set')
            elif self.cost_limit != -1:
                print('cost limit set')
                self.countdown_timer(self.cost_limit/t2_micro_price_rate)