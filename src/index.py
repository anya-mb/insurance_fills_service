from http import HTTPStatus
import os

import json
import boto3
from botocore.exceptions import ClientError

import boto3
import random
import string

from time import gmtime, strftime


def lambda_handler():  # event, context
    s3 = boto3.client('s3')

    # Generate a random file name
    file_name = ''.join(random.choices(string.ascii_lowercase, k=10))

    # Generate a random file content
    curr_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    file_content = f'This is a random file content created: {curr_time}'

    # Upload the file to S3
    s3.put_object(Bucket='filled-insurance-forms', Key=file_name, Body=file_content)

    return {
        'statusCode': 200,
        'body': f'File uploaded successfully! file_name: {file_name}'
    }


def get_secret():

    secret_name = "insurance_fills_secrets"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']

    return json.loads(secret)


def handler(event, context):
    try:

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(lambda_handler(), indent=2),
            "headers": {
                "content-type": "application/json",
            },
        }

    except Exception as e:
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": f"Exception={e}",
            "headers": {
                "content-type": "text/plain",
            },
        }

    return response