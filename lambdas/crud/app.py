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


def get_dynamodb_table(table_name: str) -> object:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    return table


def save_to_dynamodb_table(table_name: str, data_to_add: dict):
    table = get_dynamodb_table(table_name)

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
            "conversation_id": random_id,
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


def update_conversation_in_dynamodb(
    table_name: str, conversation_id: str, additional_conversation: list
) -> dict:
    table = get_dynamodb_table(table_name)

    # Retrieve the item from DynamoDB
    response = table.get_item(Key={"conversation_id": conversation_id})
    print("response from table", response)
    chat_history = response.get("Item", {})
    print("chat_history from table", chat_history)

    chat_history["conversation"].extend(additional_conversation)
    print("updated chat_history from table", chat_history)

    # Put the updated item back into DynamoDB
    table.put_item(Item=chat_history)
    print(f"item is stored in the table: {table_name}")

    return chat_history


def generate_assistant_response(
    additional_conversation: dict, chat_history: list
) -> (bool, str):
    is_finished = False
    next_question = "Next question"
    return is_finished, next_question


def lambda_update_form(event, context):
    print("lambda_update_form Handler started")

    try:
        print('event.get("pathParameters")', event.get("pathParameters"))
        conversation_id = event.get("pathParameters")["conversation_id"]
        print("conversation_id:", conversation_id)

        additional_conversation = json.loads(event.get("body"))
        print("additional_conversation:", additional_conversation)

        table_name = os.environ["CONVERSATION_TABLE_NAME"]
        print("CONVERSATION_TABLE_NAME", table_name)

        chat_history = update_conversation_in_dynamodb(
            table_name, conversation_id, additional_conversation
        )

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(chat_history, indent=2),
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
