import hashlib
import sys
from struct import *
import time
import argparse

class Worker:
    def __init__(self):  
        parser = argparse.ArgumentParser(description='Find a golden nonce.')
        parser.add_argument('-i', metavar='i', help='The input string to the program', default='COMSM0010cloud')
        parser.add_argument('d', metavar='d', type=int, help='The difficulty of solution. How many bits required of golden nonce.')
        parser.add_argument('-s', metavar='s', type=int, help='Start index.', default = 0)
        parser.add_argument('-e', metavar='e', type=int, help='Stop index.', default = 2**32)
        args = parser.parse_args()

        self.golden_nonce = None

        self.difficulty = args.d

        self.start_index = args.s
        self.stop_index = args.e

        # input string
        self.input_string = 'COMSM0010cloud'

        self.setup_time = -1
        self.calc_time = -1
        self.total_time = -1

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

    t1 = time.time()
    worker.setup_time = t1 - t0

    worker.golden_nonce = worker.pow(worker.input_string, worker.difficulty, worker.start_index, worker.stop_index)
    print("finished searching for golden nonce")
    worker.calc_time = time.time() - t1
    worker.total_time = time.time() - t0

    f = open("local_logs.txt","a+")
    f.write(', difficulty:')
    f.write(str(worker.difficulty))
    f.write(', result:')
    f.write(str(worker.golden_nonce))
    f.write(', calc_time:')
    f.write(str(round(worker.calc_time, 3)))
    f.write(', setup_time:')
    f.write(str(round(worker.setup_time, 3)))
    f.write(', local_time:')
    f.write(str(round(worker.total_time, 3)))
    f.write(', start_index:')
    f.write(str(worker.start_index))
    f.write(', stop_index:')
    f.write(str(worker.stop_index))
    f.write('\n\n')
    f.close()

    print("done")
    print(worker.golden_nonce)
if __name__== "__main__":
  main()