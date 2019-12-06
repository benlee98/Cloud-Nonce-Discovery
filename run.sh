#!/bin/bash
############################################################################################
# IMPORTANT: Ensure the value for name in this file matches the value for name in setup.sh #
############################################################################################
ami='ami-0f959a2622173aaa7'
key='linux2'
name='bl16266_cnd2'
workers=10
difficulty=20

python start-ec2.py $key $workers $difficulty $name