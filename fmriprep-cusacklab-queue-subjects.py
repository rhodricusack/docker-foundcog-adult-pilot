'''
Using aws fargate to run a fmriprep. Uses our own docker image, which contains a wrapper to download the data from S3 and push it back again.
Rhodri Cusack TCIN 2021-06, cusackrh@tcd.ie
'''

from ecs_control import register_task, run_task, wait_for_completion
import boto3
import msgpack
import msgpack_numpy as m

from os import path

def run_subjects(subjlist, input_bucket, do_wait=True):   
    response=[]
    for subj in subjlist:
        response.append(run_task(client, command = ['./fmriprep-cusacklab.bash', input_bucket, subj, 'int_imaging_bids', 'int_imaging_derivs']))
    
    if do_wait:
        wait_for_completion(client, response)
    
    return response
    

if __name__=='__main__':
    input_bucket='movie-associations'
    session = boto3.session.Session()
    client = session.client('ecs', region_name='eu-west-1')
    response = register_task(client) 
    print(response)
    
    subjlist =['sub-5','sub-7','sub-8','sub-9','sub-10','sub-11']

    response = run_subjects(subjlist, input_bucket=input_bucket)
