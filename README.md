# docker-hcp

* **All that you need to run in this repository to launch fmriprep on fargate is fmriprep-cusacklab-queue-subjects.py**
    * Setting up a docker container is only necessary if you have to install the things that this script uses.
    * If you can run this (i.e. have all the necessary packages installed) then there's no need to complicate things with docker
* Make sure your aws credentials are set up on whatever machine you are running the above python script on
* Make sure bids are uploaded to s3


## Edits needed to get to run
1. In ecs_control.py change lines 46 and 85 to your username
2. In fmriprep-cusacklab-queue-subjects.py change the deriv path line 16 to be what you want
    1. Line 25 change to input bucket
    2. Line 16 change the input prefix and output (i.e. derivatives) prefix. These must be within the input bucket specified on Line 25. 
    3. Line 31 change to subjects needed to run on
3. Check in fmirprep-cusacklab.bash that the command on line 26 (i.e. the command that runs fmriprep on the fargate clusters) has all your required options.

## Other files not necessary but useful
1. create_ge_fmap.py - this is from when we collected data with out the single band references that fmriprep looks for in ~/fmap of the bids directories to perform distortion correction.
    1. This should not be required if appropriate SB references have been taken at acquisition. 
2. requirements.txt - only needed if you are constructing the docker container which is only necessary to install packages for fmriprep-cusacklab-queue-subjects and ecs_control. Once again, these scripts can be run in a normal manner without any Docker if correct dependencies are installed. 

## TROUBLESHOOTING
1. Fargate gets stuck with X jobs pending
    1. This, for me, meant that the role (task role, line 76 ecs_control) did not have the relevant access to my bucket. If you are can launch the script but are experiencing issues with hanging, ask Rhodri as he may need to assign access to roles for you.
2. In order to debug the issues, you will need to log onto the AWS console through your browser
    1. Go to Elastic Container Sevice dashboard on the console.
    2. Click on cusacklab-fargate-cluster.
    3. Click on Metrics tab, then the "View Container Insights" button to launch CloudWatch in a new window.
    4. On left hand side menu, select "Log Groups"
    5. Within that you should be able to find the relevant logs for your fargate jobs. It may take a few minutes for these to update and appear here, but it's the best way of debugging any issues that I found.
