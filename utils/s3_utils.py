from io import StringIO
import logging
import os

import boto3

logger = logging.getLogger(__name__)
S3 = boto3.client("s3")

BUCKET = os.getenv('BUCKET_NAME')


def get_matching_s3_objects(bucket=BUCKET, prefix='', suffix='.csv'):
    """Generate objects in an S3 bucket.
    
    Keyword Arguments:
        bucket {str} -- Name of the S3 bucket. (default: {BUCKET})
        prefix {str} -- Only fetch objects whose key starts with
                        this prefix (optional) (default: {''})
        suffix {str} -- Only fetch objects whose keys end with
                        this suffix (optional) (default: {'.csv'})
    Yields:
        [str] -- key to an s3 object
    """    
    paginator = S3.get_paginator("list_objects_v2")
    kwargs = {'Bucket': bucket}

    prefixes = (prefix, ) if isinstance(prefix, str) else prefix

    for p in prefixes:
        kwargs["Prefix"] = f'{p}/'

        for page in paginator.paginate(**kwargs):
            try:
                contents = page["Contents"]
            except KeyError:
                return

            for obj in contents:
                key = obj["Key"]
                if key.endswith(suffix):
                    yield obj


def get_matching_s3_keys(bucket=BUCKET, prefix="",  suffix='.csv'):
    """Generate the keys in an S3 bucket.
    
    Keyword Arguments:
        bucket {str} -- Name of the S3 bucket. (default: {BUCKET})
        prefix {str} -- Only fetch keys that start with this prefix (optional).
                        (default: {""})
        suffix {str} -- Only fetch keys that end with this suffix (optional). 
                        (default: {'.csv'})
    
    Yields:
        [str] -- key to an s3 object
    """    
    for obj in get_matching_s3_objects(bucket, prefix, suffix):
        yield obj["Key"]


def read_object(key, bucket=BUCKET):
    """Reads an s3 object and returns contents
    
    Arguments:
        key {str} -- key for s3 object
    
    Keyword Arguments:
        bucket {str]} -- name of the s3 bucket (default: {BUCKET})
    
    Returns:
        file-like object -- contents of the s3 object
    """    
    obj = S3.get_object(Bucket=bucket, Key=key)
    data = StringIO(obj.get('Body').read().decode('utf-8'))
    
    return data


def put_object(data, key, bucket=BUCKET):
    """Put an object into S3
    
    Arguments:
        data {str} -- contents of the csv file as a str
        key {str} -- key for the s3 object (e.g. file path)
    
    Keyword Arguments:
        bucket {str} -- name of the bucket (default: {BUCKET})
    """    
    body = bytes(data.encode('UTF-8'))
    params = {
        'Bucket': bucket,
        'Key': key,
        'Body': body,
        'ContentType': 'text/csv'
    }
    try:
        S3.put_object(**params)
    except Exception as e:
        logger.error(e, exc_info=True)
