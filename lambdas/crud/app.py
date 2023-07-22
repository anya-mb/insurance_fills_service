import json
import logging
import os
import random
import string
from http import HTTPStatus
from time import gmtime, strftime

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
        user_input = json.loads(event.get("body"))[0]

        conversation.append(user_input)

        logger.debug(f"conversation: {user_input}")

        random_id = get_random_id()

        input_dict = {"conversation_id": random_id, "conversation": conversation}

        table_name = os.environ["CONVERSATION_TABLE_NAME"]

        save_to_dynamodb_table(table_name, input_dict)

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(input_dict, indent=2),
            "headers": {"content-type": "application/json"},
        }
    except Exception as e:
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": f"Exception={e}",
            "headers": {"content-type": "text/plain"},
        }
    return response


def update_conversation_in_dynamodb(
    table_name: str, conversation_id: str, additional_conversation: list
) -> dict:
    """
    Function to update a conversation in DynamoDB
    """
    table = get_dynamodb_table(table_name)
    response = table.get_item(Key={"conversation_id": conversation_id})
    chat_history = response.get("Item", {})
    chat_history["conversation"].extend(additional_conversation)

    table.put_item(Item=chat_history)
    logger.info(f"Item is stored in the table: {table_name}")

    return chat_history


def generate_assistant_response(chat_history: list) -> (bool, str):
    """
    Function to generate assistant response
    """
    is_finished = False
    next_question = {
        "role": "assistant",
        "content": "Yes, we do offer car insurance. To complete your application, \
        I would need some additional information. Could you please provide your phone number?",
    }
    return is_finished, next_question


def lambda_update_form(event, context) -> dict:
    """
    Lambda function to update form
    """
    logger.info("lambda_update_form Handler started")
    try:
        conversation_id = event.get("pathParameters")["conversation_id"]
        additional_conversation = json.loads(event.get("body"))
        conversations_table_name = os.environ["CONVERSATION_TABLE_NAME"]

        chat_history = update_conversation_in_dynamodb(
            conversations_table_name, conversation_id, additional_conversation
        )

        is_finished, value = generate_assistant_response(chat_history)
        result = {"next_question": value, "is_finished": is_finished}

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(result, indent=2),
            "headers": {"content-type": "application/json"},
        }

        if is_finished:
            filled_form = value
            filled_form["conversation_id"] = conversation_id
            filled_form["create_time"] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            forms_table_name = os.environ["FILLED_FORMS_TABLE_NAME"]
            save_to_dynamodb_table(forms_table_name, filled_form)
        else:
            additional_conversation = {"role": "assistant", "content": value}
            chat_history = update_conversation_in_dynamodb(
                conversations_table_name, conversation_id, additional_conversation
            )

            logger.debug(f"Next question: {value}")
            logger.debug(f"chat_history updated with next question: {chat_history}")
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
