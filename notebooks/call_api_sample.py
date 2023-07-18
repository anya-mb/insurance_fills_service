import os
from os.path import dirname

import requests
import boto3
from dotenv import load_dotenv
from requests_aws4auth import AWS4Auth


DIRNAME = dirname(__file__)

load_dotenv(f"{DIRNAME}/.env", override=True)
credentials = boto3.Session(
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
).get_credentials()

region = "us-east-1"
service = "execute-api"

# endpoint = "https://c2issjr8el.execute-api.us-east-1.amazonaws.com/"
endpoint = "https://xdxb2u7ul8.execute-api.us-east-1.amazonaws.com/"
headers = {"Content-Type": "application/json"}

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token,
)

response = requests.get(endpoint, auth=awsauth, headers=headers)
print(response.content)