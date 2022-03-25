
#!/bin/bash
if [ $# -lt 2 ]; 
    then echo "fmriprep_cusacklab.bash [s3 bucket] [participant] [[input_prefix, default bids]] [[output_prefix, default deriv]],"
fi

BUCKET=$2
SUBJECT=$3
INPUT_PREFIX=${4:-bids}
OUTPUT_PREFIX=${5:-deriv}

echo "BUCKET $BUCKET"
echo "SUBJECT $SUBJECT"
echo "INPUT_PREFIX $INPUT_PREFIX"
echo "OUTPUT_PREFIX $OUTPUT_PREFIX"

# Get ready for inputs and outputs
mkdir -p /data
mkdir -p /out

# Download the requested subject, but all the other files
aws s3 sync --exclude 'sub-??/*' s3://${BUCKET}/${INPUT_PREFIX} /data
aws s3 sync s3://${BUCKET}/${INPUT_PREFIX}/${SUBJECT} /data/${SUBJECT}

# Run fMRIprep only on this participant
/usr/local/miniconda/bin/fmriprep /data /out participant --participant-label ${SUBJECT} --output-spaces MNI152NLin2009cAsym fsaverage5

# Upload deriv
aws s3 sync /out s3://${BUCKET}/${OUTPUT_PREFIX}/