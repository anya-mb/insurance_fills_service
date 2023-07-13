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
    print(f"after key, {openai_key[:5]}")

    llm = OpenAI(openai_api_key=openai_key)
    # chat = ChatOpenAI(temperature=0.5, openai_api_key=openai_key)

    result = llm.predict("Give me a motivational quote")
    print(result)

    # result = chat.predict_messages([HumanMessage(content="Give me a motivational quote")])
    # quote = result.content

    quote = result  #"dummy value"

    save_result = save_to_s3(quote)
    print("saved to s3")
    return save_result


def save_to_s3(file_content):
    s3 = boto3.client('s3')

    bucket = os.environ['BUCKET_NAME']
    print("bucket", bucket)

    # Generate a random file name
    file_name = ''.join(random.choices(string.ascii_lowercase, k=10))

    # Upload the file to S3
    s3.put_object(Bucket=bucket, Key=file_name, Body=file_content)

    return {
        'statusCode': 200,
        'body': f'File uploaded successfully! file_name: {file_name}, content: {file_content}'
    }


def lambda_handler():  # event, context
    s3 = boto3.client('s3')

    bucket = os.environ['BUCKET_NAME']
    print("bucket", bucket)

    # Generate a random file name
    file_name = ''.join(random.choices(string.ascii_lowercase, k=10))

    # Generate a random file content
    curr_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    file_content = f'This is a random file content created: {curr_time}'

    # Upload the file to S3
    s3.put_object(Bucket=bucket, Key=file_name, Body=file_content)

    return {
        'statusCode': 200,
        'body': f'File uploaded successfully! file_name: {file_name}'
    }


def get_secret():

    # secret_name = "insurance_fills_secrets"
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
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']

    return json.loads(secret)


def handler(event, context):
    try:
        result = get_openai_quote()  #get_openai_quote()
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
