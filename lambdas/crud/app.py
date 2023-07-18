import json
import os
import random
import string
from http import HTTPStatus
import boto3

# SECRET_NAME = "insurance_fills_secrets"
# SECRET_KEY_OPENAI_KEY = "open_ai_key"


def get_random_id() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=10))


def save_to_dynamodb_table(table_name: str, data_to_add: dict):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    table.put_item(Item=data_to_add)
    print(f"Successful put to the table: {table_name}")
    print("Added data", data_to_add)


def lambda_create_form(event, context):
    print("lambda_create_form Handler started")

    try:

        conversation = json.loads(event.get("body"))
        print("conversation:", conversation)

        random_id = get_random_id()

        data_to_add_to_db = {
            "id": random_id,
            "conversation": conversation,
        }

        table_name = os.environ["CONVERSATION_TABLE_NAME"]
        print("CONVERSATION_TABLE_NAME", table_name)

        save_to_dynamodb_table(table_name, data_to_add_to_db)

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(data_to_add_to_db, indent=2),
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
