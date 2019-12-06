import hashlib
import sys
from struct import *
import boto3
import time
import argparse

class Worker:
    def __init__(self):  
        parser = argparse.ArgumentParser(description='Find a golden nonce.')
        parser.add_argument('-i', metavar='i', help='The input string to the program', default='COMSM0010cloud')
        parser.add_argument('d', metavar='d', type=int, help='The difficulty of solution. How many bits required of golden nonce.')
        args = parser.parse_args()

        self.golden_nonce = None

        # max nonce value
        self.max = 2 ** 32
        self.difficulty = args.d

        self.start_index = 0
        self.stop_index = self.max

        # input string
        self.input_string = 'COMSM0010cloud'

        self.setup_time = -1
        self.calc_time = -1
        self.total_time = -1

        # Create SQS client
        self.sqs = boto3.resource('sqs', region_name='us-east-2')

        # Get the queue
        self.input_queue = self.sqs.get_queue_by_name(QueueName='input_queue')
        self.output_queue = self.sqs.get_queue_by_name(QueueName='output_queue')
        self.run_timing_queue = self.sqs.get_queue_by_name(QueueName='run_timing_queue')

    def receive_indices(self):
        print("receiving indices")
        # Receive message from queue with start and end index of search space
        start = 0
        end = max
        for message in self.input_queue.receive_messages(MessageAttributeNames=['Start', 'End'], MaxNumberOfMessages=1):
            # Get the custom author message attribute if it was set
            if message.message_attributes is not None:
                start = message.message_attributes.get('Start').get('StringValue')
                end = message.message_attributes.get('End').get('StringValue')

        self.start_index = int(start)
        self.stop_index = int(end)
        print("start index", self.start_index)
        print("end index", self.stop_index)

    def send_result(self):
        print("sending result")
        self.output_queue.send_message(MessageBody='Here is my result', MessageAttributes = {
            'Result': {
                'DataType': 'Number',
                'StringValue': str(self.golden_nonce)
            },
            'Start': {
                'DataType': 'Number',
                'StringValue': str(self.start_index)
            },
            'End': {
                'DataType': 'Number',
                'StringValue': str(self.stop_index)
            }
        })

    def send_metrics(self):
        print("sending metrics")
        self.run_timing_queue.send_message(MessageBody='Run Time', MessageAttributes = {
            'total_time': {
                'DataType': 'Number',
                'StringValue': str(self.total_time)
            },
            'calc_time': {
                'DataType': 'Number',
                'StringValue': str(self.calc_time)
            },
            'setup_time': {
                'DataType': 'Number',
                'StringValue': str(self.setup_time)
            },
            'Start': {
                'DataType': 'Number',
                'StringValue': str(self.start_index)
            },
            'End': {
                'DataType': 'Number',
                'StringValue': str(self.stop_index)
            }
        })

    # SHA-256 squared
    # Takes bytes type as input
    def doubleSha(self, input):
        hash1 = hashlib.sha256(input).digest()
        hash2 = hashlib.sha256(hash1)
        return hash2

    # Takes an input string, a number of difficulty bits, 
    # and a range to iterate over
    # add range parameter then for x in range(r):
    def pow(self, input, difficulty, start, end):
        print("searching for golden nonce")
        enc_string = input.encode('utf-8')
        for x in range(start, end):
            bnry = pack(">I", x)
            hash = self.doubleSha(enc_string + bnry).hexdigest()
            hex = int(hash, 16)
            if (hex < 2 ** (256 - difficulty)):
                return x
        print("failed to find golden nonce")
        return -1

def main():
    t0 = time.time()

    worker = Worker()
    worker.receive_indices()
    print("received indices")
    t1 = time.time()
    worker.setup_time = t1 - t0

    worker.golden_nonce = worker.pow(worker.input_string, worker.difficulty, worker.start_index, worker.stop_index)
    print("finished searching for golden nonce")
    worker.calc_time = time.time() - t1
    worker.total_time = time.time() - t0

    worker.send_result()
    worker.send_metrics()
    print("done")
if __name__== "__main__":
  main()