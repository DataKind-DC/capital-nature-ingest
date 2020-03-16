from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from io import StringIO
import os
import re

import boto3
from botocore.exceptions import ClientError

import config

SES = boto3.client('ses')
S3 = boto3.client("s3")

BUCKET = os.getenv('BUCKET_NAME')


def is_put_scrape_report(event):
    records = event['Records']
    for record in records:
        key = record['s3']['object']['key']
        if 'scrape-report' in key:
            return True


def get_report_key(data_key):
    date_with_file_extension = "-".join(data_key.split("-")[4:])
    report_key = f'reports/scrape-report-{date_with_file_extension}'
    
    return report_key


def get_attachments():
    attachments = []
    keys = []
    for match in get_matching_s3_keys(BUCKET, prefix='data/', suffix='.csv'):
        keys.append(match)
    
    report_key = get_report_key(keys[0])
    keys.append(report_key)
    
    for key in keys:
        obj = S3.get_object(Bucket=BUCKET, Key=key)
        data = StringIO(obj.get('Body').read().decode('utf-8'))
        filename = key.split("/")[1]
        attachments.append((filename, data))

    return attachments


def get_matching_s3_objects(bucket, prefix="", suffix=""):
    """
    Generate objects in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch objects whose key starts with
        this prefix (optional).
    :param suffix: Only fetch objects whose keys end with
        this suffix (optional).
    """
    paginator = S3.get_paginator("list_objects_v2")

    kwargs = {'Bucket': bucket}

    # We can pass the prefix directly to the S3 API.  If the user has passed
    # a tuple or list of prefixes, we go through them one by one.
    prefixes = (prefix, ) if isinstance(prefix, str) else prefix

    for key_prefix in prefixes:
        kwargs["Prefix"] = key_prefix

        for page in paginator.paginate(**kwargs):
            try:
                contents = page["Contents"]
            except KeyError:
                break

            for obj in contents:
                key = obj["Key"]
                if key.endswith(suffix):
                    yield obj


def get_matching_s3_keys(bucket, prefix="", suffix=""):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    for obj in get_matching_s3_objects(bucket, prefix, suffix):
        yield obj["Key"]


def send_email(attachments):
    #TODO: config the email
    message = MIMEMultipart()
    recipients = ['you@domain.com', 'me@domain.com']
    message['Subject'] = 'email subject string'
    message['From'] = 'sender.email@domain.com'
    message['To'] = ', '.join(recipients)
    # message body (as html, opitonally)
    part = MIMEText('email body string', 'html')
    message.attach(part)
    # attachments
    for filename, attachment in attachments:
        part = MIMEApplication(str.encode(attachment))
        part.add_header(
            'Content-Disposition',
            'attachment',
            filename=filename
        )
        message.attach(part)
    try:
        response = SES.send_raw_email(
            Source=message['From'],
            Destinations=recipients,
            RawMessage={
                'Data': message.as_string()
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
