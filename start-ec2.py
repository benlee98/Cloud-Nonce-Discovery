#!/usr/bin/python
import sys
import signal
from hunter import Hunter  
import argparse  

# todo: error handling

def main():
    def handler(signum, frame):
        hunter.force_closure = True
        hunter.early_shutdown()

    parser = argparse.ArgumentParser(description='Find a golden nonce.')
    parser.add_argument('k', metavar='k', help='Name of AWS key pair')
    parser.add_argument('n', metavar='n', type=int, help='The number of desired workers to run')
    parser.add_argument('d', metavar='d', type=int, help='The desired difficulty')
    parser.add_argument('ami', metavar='ami', help='Name of AMI')
    parser.add_argument('-c', metavar='c', type=float, help='Confidence of finding golden nonce within time limit t. Between 0 and 1. Notes: overrides n (worker count), t argument must also be passed to use this', default=0.5)
    parser.add_argument('-t', metavar='t', type=float, help='Time limit (seconds)', default=-1)
    parser.add_argument('-p', metavar='p', type=float, help='Cost limit (in dollars ($)). Note: overriden by time limit', default=-1)

    # Create golden nonce finder
    hunter = Hunter(parser)
    signal.signal(signal.SIGINT, handler)
    hunter.start()
  
if __name__== "__main__":
  main()