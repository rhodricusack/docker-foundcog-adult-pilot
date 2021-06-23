from ecs_control import register_task, run_task, wait_for_completion
import boto3
import msgpack
import msgpack_numpy as m
from os import path

def run_subjects(subjlist, wait_for_completion=True, output_bucket='neurana-imaging', output_prefix='hcp-test'):   
    response=[]
    for subj in subjlist:
        response.append(run_task(client, command = ['python3','/app/roi_extract_one_subject.py', "--subject", subj,  "--output_bucket",output_bucket, "--output_prefix",output_prefix ]))
    
    if wait_for_completion:
        wait_for_completion(client, response)
    
    return response
    
def get_results(subjlist, output_bucket=None, output_prefix=None):
    session = boto3.session.Session()
    client = session.client('s3')
    allresults={}
    for sub in subjlist:
        outfn=f'sub-{sub}_roi.msgpack-numpy'
        localfn=path.join('/tmp', outfn)
        client.download_file(output_bucket, path.join(output_prefix, outfn),localfn)
        with open(localfn, "rb") as data_file:
            byte_data = data_file.read()
        x_rec = msgpack.unpackb(byte_data, object_hook=m.decode)
        allresults[sub] = x_rec

    return allresults

if __name__=='__main__':
    output_bucket='neurana-imaging'
    output_prefix='hcp_test'
    session = boto3.session.Session()
    client = session.client('ecs', region_name='eu-west-1')
    #response = register_task(client)
    subjlist = ['178950','189450'] #,'199453','209228','220721']
    #response = run_subjects(subjlist, output_bucket=output_bucket, output_prefix=output_prefix)
    allresults=get_results(subjlist, output_bucket=output_bucket, output_prefix=output_prefix )
    print(allresults)