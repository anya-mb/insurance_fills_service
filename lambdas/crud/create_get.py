import json
import os
import random
import string
import logging
from http import HTTPStatus
import boto3

from constants import SYSTEM_SETUP_PROMPT

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_random_id() -> str:
    """
    Function to generate a random string of 10 lowercase alphabets
    """
    return "".join(random.choices(string.ascii_lowercase, k=10))


def get_dynamodb_table(table_name: str) -> object:
    """
    Function to get the DynamoDB table object
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    return table


def save_to_dynamodb_table(table_name: str, data_to_add: dict):
    """
    Function to save a dictionary to DynamoDB table
    """
    table = get_dynamodb_table(table_name)
    table.put_item(Item=data_to_add)
    logger.info(f"Successful put to the table: {table_name}")
    logger.debug(f"Added data: {data_to_add}")


def lambda_create_form(event, context):
    """
    Lambda function to create form
    """
    logger.info("lambda_create_form Handler started")
    try:
        conversation = [{"role": "system", "content": SYSTEM_SETUP_PROMPT}]
        logger.debug(f"conversation: {conversation}")

        random_id = get_random_id()
        data_to_add_to_db = {"conversation_id": random_id, "conversation": conversation}
        table_name = os.environ["CONVERSATION_TABLE_NAME"]

        save_to_dynamodb_table(table_name, data_to_add_to_db)

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(data_to_add_to_db, indent=2),
            "headers": {"content-type": "application/json"},
        }
    except Exception as e:
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": f"Exception={e}",
            "headers": {"content-type": "text/plain"},
        }
    return response


def lambda_get_form(event, context) -> dict:
    """
    Lambda function to get form
    """
    logger.info("lambda_get_form Handler started")
    try:
        forms_table_name = os.environ["FILLED_FORMS_TABLE_NAME"]
        forms_table = get_dynamodb_table(forms_table_name)

        conversation_id = event.get("pathParameters")["conversation_id"]
        response = forms_table.get_item(Key={"conversation_id": conversation_id})
        filled_form = response.get("Item", {})

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(filled_form, indent=2),
            "headers": {"content-type": "application/json"},
        }
    except Exception as e:
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": f"Exception={e}",
            "headers": {"content-type": "text/plain"},
        }
    return response
