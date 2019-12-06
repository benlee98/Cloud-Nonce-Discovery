# Running Instructions
## Cloud Setup
Before the system can be run the base AMI needs to be created. This has been automated and can be performed by running 
    ./setup.sh
### Instructions
The system assumes usage of
    region_name='us-east-2'
when Terraform set up runs please input *us-east-2* when prompted.
Note that the variables in the script must match the corresponding variables in the *main.tf* file.
## Cloud Running
To run the CND algorithm either modify *run.sh* or type the command:

    python start-ec2.py [-h] [-c c] [-t t] [-p p] k n d ami  

    positional arguments:                                                                                                                                                                                                                                          k           Name of AWS key pair                                                                                                                                                                                                                             n           The number of desired workers to run                                                                                                                                                                                                             d           The desired difficulty                                                                                                                                                                                                                           ami         Name of AMI                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 optional arguments:                                                                                                                                                                                                                                            -h, --help  show this help message and exit                                                                                                                                                                                                                  -c c        Confidence of finding golden nonce within time limit t. Between                                                                                                                                                                                              0 and 1. Notes: overrides n (worker count), t argument must also                                                                                                                                                                                             be passed to use this                                                                                                                                                                                                                            -t t        Time limit (seconds)                                                                                                                                                                                                                             -p p        Cost limit (in dollars ($)). Note: overriden by time limit   


## Local Running
To run the CND algorithm locally either modify *local_script.sh* or type the command:

    local_cloud.py [-h] [-i i] [-s s] [-e e] d

    positional arguments:                                                                                                                                                                                                                                          d           The difficulty of solution. How many bits required of golden                                                                                                                                                                                                 nonce.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      optional arguments:                                                                                                                                                                                                                                            -h, --help  show this help message and exit                                                                                                                                                                                                                  -i i        The input string to the program                                                                                                                                                                                                                  -s s        Start index.                                                                                                                                                                                                                                     -e e        Stop index.   


## Log Files
Logs may be output to three different files:
* cloud_timings.txt
    * for the distributed implementation of CND
* early_shutdown_log.txt
    * in the case the CND system terminates early or is forced to shut down
* local_logs.txt
    * for the local implementation of CND


## Further Information
Further information can be found in setup.sh, run.sh and local_script.sh