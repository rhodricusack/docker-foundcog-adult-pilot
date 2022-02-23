# docker-hcp

* Make sure bids are uploaded to s3

## Edits needed to get to run
1. In ecs_control.py change lines 46 and 85 to your username
2. In fmriprep-cusacklab-queue-subjects.py change the deriv path line 16 to be what you want
    1. Line 25 change to input bucket
    2. Line 31 change to subjects needed to run on