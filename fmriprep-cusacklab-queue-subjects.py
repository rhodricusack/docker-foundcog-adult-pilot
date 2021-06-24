from ecs_control import register_task, run_task, wait_for_completion
import boto3
import msgpack
import msgpack_numpy as m
from os import path

def run_subjects(subjlist, input_bucket, wait_for_completion=True):   
    response=[]
    for subj in subjlist:
        response.append(run_task(client, command = ['/usr/local/miniconda/bin/fmriprep-cusacklab.bash', input_bucket, subj]))
    
    if wait_for_completion:
        wait_for_completion(client, response)
    
    return response
    

if __name__=='__main__':
    input_bucket='foundcog-adult-pilot'
    session = boto3.session.Session()
    client = session.client('ecs', region_name='eu-west-1')
    response = register_task(client)
    subjlist = ['sub-01'] 
    response = run_subjects(subjlist, input_bucket=input_bucket)
