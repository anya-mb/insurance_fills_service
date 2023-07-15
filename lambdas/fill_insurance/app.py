from http import HTTPStatus
import os

import json
from botocore.exceptions import ClientError

import boto3
import random
import string

from time import gmtime, strftime

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)


SECRET_NAME = "insurance_fills_secrets"
SECRET_KEY_OPENAI_KEY = "open_ai_key"


def get_openai_quote():
    print("before key")
    openai_key = get_secret()[SECRET_KEY_OPENAI_KEY]

    llm = OpenAI(openai_api_key=openai_key)

    result = llm.predict("Give me a motivational quote")
    print(result)

    quote = result

    save_result = save_to_s3(quote)
    print("saved to s3")
    return save_result


def save_to_s3(file_content):
    s3 = boto3.client('s3')

    bucket = os.environ['BUCKET_NAME']
    print("bucket", bucket)

    file_name = ''.join(random.choices(string.ascii_lowercase, k=10))

    s3.put_object(Bucket=bucket, Key=file_name, Body=file_content)

    return {
        'statusCode': 200,
        'body': f'File uploaded successfully! file_name: {file_name}, content: {file_content}'
    }


def lambda_handler():
    s3 = boto3.client('s3')

    bucket = os.environ['BUCKET_NAME']
    print("bucket", bucket)

    file_name = ''.join(random.choices(string.ascii_lowercase, k=10))

    curr_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    file_content = f'This is a random file content created: {curr_time}'

    s3.put_object(Bucket=bucket, Key=file_name, Body=file_content)

    return {
        'statusCode': 200,
        'body': f'File uploaded successfully! file_name: {file_name}'
    }


def get_secret():

    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=SECRET_NAME
        )
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']

    return json.loads(secret)


def handler(event, context):
    try:
        result = get_openai_quote()
        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(result, indent=2),
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
