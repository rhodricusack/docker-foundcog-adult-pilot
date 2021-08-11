# We didn't acquire SE EPIs for our LR and RL phase-encoding polarity disortion correction
# So, using the mean of GE fMRI as stand-in
# Rhodri Cusack TCIN 2021-06, cusackrh@tcd.ie

import nibabel as nib
import boto3
import tempfile
from os import path
import pandas as pd
import json
import os
from nilearn import image
import numpy as np

s3=boto3.client('s3')

bucket='foundcog-adult-pilot'
dirnames ={'i':'LR', 'i-':'RL'}
tmpdir = tempfile.mkdtemp()

#s3.download_file(bucket, 'bids/participants.tsv', path.join(tmpdir,'participants.tsv') )
#ps = pd.read_csv( path.join(tmpdir,'participants.tsv'), sep='\t')

ps = ['sub-02']
#ps =['sub-02','sub-03', 'sub-04','sub-05', 'sub-06','sub-07','sub-08','sub-09','sub-10','sub-11','sub-12','sub-13','sub-14']
# Removed because images don't match
#ps = ['sub-06','sub-17','sub-03']

create_means = True
create_jsons = True
skip_if_already_fmap = False

for p in ps:
    print(f"'{p}',", end='')


for p in ps:

    print(f'Working on {p}')
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'foundcog-adult-pilot-2/bids/{p}/ses')
    #print(resp)
    sespth=resp['Contents'][0]['Key'].split('/')[:4]

    pmean = path.join('/'.join(sespth),'fmap')
    fmapresp = s3.list_objects_v2(Bucket=bucket, Prefix=pmean)
    print(pmean)
    if fmapresp['KeyCount'] and skip_if_already_fmap:
        print(f'Already have fmap in {p}')
    else:
        funcs3 = sespth
        funcs3.append('func')
        funcs3='/'.join(funcs3)
        funcresp = s3.list_objects_v2(Bucket=bucket, Prefix=funcs3)

        pe = {}
        mnpths = {}

        #print(funcresp.keys())
        for bold in funcresp['Contents']:
            filename, ext=path.splitext(bold['Key'])
            if ext=='.gz':
                filename, ext2=path.splitext(filename)
                ext=ext2 + ext
            
            if ext=='.json' and create_jsons:  
                outpth = path.join(tmpdir,bold['Key'])
                os.makedirs(path.dirname(outpth), exist_ok=True)
                s3.download_file(bucket, bold['Key'], outpth )  
                with open(path.join(tmpdir,bold['Key'])) as json_file:
                    data = json.load(json_file)
                    if not data['PhaseEncodingDirection'] in pe:
                        pe[data['PhaseEncodingDirection']] = []
                    pe[data['PhaseEncodingDirection']].append(filename) 

            if ext=='.nii.gz' and create_means:  
                outpth = path.join(tmpdir,bold['Key'])
                os.makedirs(path.dirname(outpth), exist_ok=True)
                s3.download_file(bucket, bold['Key'], outpth )  
                img=nib.load(outpth)
                mnimg = image.mean_img(img)
                print(img.shape)
                print(mnimg.shape)
                
                mnpth = path.join(tmpdir, filename+'_mean.nii.gz')
                print(mnpth)
                nib.save(mnimg, mnpth)
                mnpths[filename] = mnpth
            print('.')

        for pekey, pelist in pe.items():
            # For each phase encode direction, take mean of all BOLD images with this encoding
            pmean = path.join('/'.join(sespth[:-1]),'fmap',path.basename(pelist[0])[:15] + 'acq-bold_dir-' + dirnames[pekey] + '_epi')
            os.makedirs(path.join(tmpdir,path.dirname(pmean)), exist_ok=True)

            if create_means:
                allimgs=[]
                for im in pelist:
                    img = nib.load(mnpths[im])
                    allimgs.append(img)

                # Count up unique affines
                allaffines=np.vstack([x.affine.ravel() for x in allimgs])
                urows=np.unique(allaffines, axis=0, return_inverse=True, return_counts=True)
                commonrow= np.argmax(urows[2]) # most common affine

                # Mean of most common affine (most often will be all the images)
                totimg = image.concat_imgs(np.array(allimgs)[urows[1]==commonrow])
                mnimg = image.mean_img(totimg)
                nib.save(mnimg,path.join(tmpdir,pmean+ '.nii.gz'))
                print(pmean+ '.nii.gz')  
                #s3.upload_file(path.join(tmpdir,pmean+ '.nii.gz'), bucket, pmean+ '.nii.gz')
                s3.upload_file(path.join(tmpdir,pmean+ '.nii.gz'), bucket, pmean+ '.nii.gz')
                

            # Make the json file, taking as input the first of the matching BOLD files and adding the intended for field
            if create_jsons:
                with open(path.join(tmpdir,pelist[0]+'.json')) as json_file:
                    data = json.load(json_file)
                    data['IntendedFor'] = ['/'.join(x.split('/')[2:])+'.nii.gz' for y in pe.values() for x in y]
                with open(path.join(tmpdir, pmean + '.json'),'w') as json_out:
                    json.dump(data, json_out)
                s3.upload_file(path.join(tmpdir, pmean + '.json'), bucket, pmean+ '.json')    
                
                todelete = path.dirname(pmean)+'.json'
                s3.delete_object(Bucket=bucket, Key=todelete)
                

