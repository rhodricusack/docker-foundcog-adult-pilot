import boto3
import nilearn
import nibabel as nib
import numpy as np
from matplotlib import pyplot as plt
import logging
from botocore.exceptions import ClientError
import argparse
import msgpack
import msgpack_numpy as m
from os import path

def parse_args():
    parser = argparse.ArgumentParser(description='ROI Extraction from HCP Data')

    parser.add_argument('--subject', type=str, default=None, help='HCP subject number')
    parser.add_argument('--profile_name', type=str, default=None, help='HCP subject number')
    parser.add_argument('--bucket', type=str, default='neurana-imaging', help='HCP subject number')
    parser.add_argument('--output_prefix', type=str, default='roi_extract', help='HCP subject number')
  
    return parser.parse_args()

import boto3
import base64
from botocore.exceptions import ClientError
import json
import os

def get_aws_hcp_keys():
    # First try environment variables
    print(os.getenv('HCP_KEYS'))
        
    secret_name = "aws/hcp"
    region_name = "eu-west-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        print(e.response['Error']['Code'])
        
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        
        secret = json.loads(get_secret_value_response['SecretString'])
        
    return secret


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3') # Don't use special profile
    response = s3_client.upload_file(file_name, bucket, object_name)
    print(f'Uploading to bucket {bucket} object_name {object_name}')
    return response

def main(args):
    sub=args.subject
    print(f'Working on subject {sub}')

    hcp_keys = get_aws_hcp_keys()
    session = boto3.Session(aws_access_key_id=hcp_keys['AWS_ACCESS_KEY_ID'], aws_secret_access_key=hcp_keys['AWS_SECRET_ACCESS_KEY'])

    s3 = session.client('s3')

    # List of tasks and contrasts to be analysed for each
    taskcondict = {
        'tfMRI_WM': [8, 9, 14, 15, 16, 17], # 2BK, 0BK, BODY, FACE, PLACE, TOOL
        'tfMRI_EMOTION': [0, 1],     # FACES, SHAPES
        }   

    # ROIS (DLPFC left and right
    # We should change this to all regions
    roilist=[26, 67, 68, 70, 71, 73, 83, 84, 85, 86, 87, 96, 98, 206, 247, 148, 250, 251, 253, 264, 265, 266, 267, 276, 278]

    # Load up ROI files for L and R
    roi_L_img=nib.load('rois/Q1-Q6_RelatedParcellation210.L.CorticalAreas_dil_Colors.32k_fs_LR.dlabel.nii')
    roi_R_img=nib.load('rois/Q1-Q6_RelatedParcellation210.R.CorticalAreas_dil_Colors.32k_fs_LR.dlabel.nii')
    roi_L_dat=roi_L_img.get_fdata().ravel().astype(int)
    roi_R_dat=180 + roi_R_img.get_fdata().ravel().astype(int)
    roi_dat=np.concatenate((roi_L_dat,roi_R_dat))

    # Handy later 
    nroi = len(roilist)
    ntask = len(taskcondict)

    # Initialise a space for the output summary values
    meanact={}
    for task, taskcon in taskcondict.items():
        meanact[task]=np.zeros((len(taskcon), nroi))
        

    # Main loop over contrast files
    for task, taskcon in taskcondict.items():
        # For each task
        # Download file from HCP S3. 
        s3.download_file('hcp-openaccess', f'HCP_1200/{sub}/MNINonLinear/Results/{task}/{task}_hp200_s2_level2.feat/{sub}_{task}_level2_hp200_s2.dscalar.nii', '/tmp/timeseries.nii')     
        task_img = nib.load('/tmp/timeseries.nii')

        # Pick out only voxels on the cortical surface
        task_dat=task_img.get_fdata()
        task_surfmask=task_img.header.get_axis(1).surface_mask
        task_dat_surf=task_dat[:,task_surfmask]

        # For each ROI, summarise activity in the selected regions and contrasts for this task
        for roiind, roi in enumerate(roilist):
            sel=task_dat_surf[:, roi_dat == roi]
            meanact[task][:, roiind] = np.mean(sel, 1)[taskcon]

    # Write output file 
    outfn=f'sub-{sub}_roi.msgpack-numpy'
    outpth='/tmp'
    x_enc = msgpack.packb(meanact, default=m.encode)
    with open(path.join(outpth,outfn),'wb') as f:
        msgpack.dump(meanact, f, default=m.encode)

    # Upload to s3
    print(upload_file(path.join(outpth,outfn), args.bucket, path.join(args.output_prefix, outfn)))
        
if __name__=='__main__':
    args = parse_args()
    main(args)

