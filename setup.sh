#!/bin/bash
############################################################################################################
# IMPORTANT: Ensure the value for name and security group in main tf match the $name variable in this file #
############################################################################################################

# set name of keypair
key='linux2'
# set name of system
name='bl16266_cnd2'

python security_setup.py $name
terraform init
terraform plan
terraform apply 
sleep 5
python ssh_script.py $key $name 
python create_ami.py $name 
python terminator.py
