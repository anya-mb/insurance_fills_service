import json
import os
import random
import string
from http import HTTPStatus
import boto3
from time import gmtime, strftime


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


def generate_assistant_response(chat_history: list) -> (bool, str):
    # is_finished = True
    # next_question = {
    #     "first_name": "Bob",
    #     "last_name": "Smith",
    #     "age": "24",
    #     "type_of_insurance": "Auto",
    #     "phone_number": "9876543210",
    # }
    is_finished = False
    next_question = {
        "role": "assistant",
        "content": "Yes, we do offer car insurance. To complete your application, \
        I would need some additional information. Could you please provide your phone number?",
    }
    return is_finished, next_question


def lambda_update_form(event, context) -> dict:
    print("lambda_update_form Handler started")

    try:
        print('event.get("pathParameters")', event.get("pathParameters"))
        conversation_id = event.get("pathParameters")["conversation_id"]
        print("conversation_id:", conversation_id)

        additional_conversation = json.loads(event.get("body"))
        print("additional_conversation:", additional_conversation)

        conversations_table_name = os.environ["CONVERSATION_TABLE_NAME"]
        print("CONVERSATION_TABLE_NAME", conversations_table_name)

        chat_history = update_conversation_in_dynamodb(
            conversations_table_name, conversation_id, additional_conversation
        )

        is_finished, value = generate_assistant_response(chat_history)

        result = {
            "next_question": value,
            "is_finished": is_finished,
        }

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(result, indent=2),
            "headers": {
                "content-type": "application/json",
            },
        }

        if is_finished:
            filled_form = value
            filled_form["conversation_id"] = conversation_id

            form_create_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            filled_form["create_time"] = form_create_time

            forms_table_name = os.environ["FILLED_FORMS_TABLE_NAME"]
            print("FILLED_FORMS_TABLE_NAME", forms_table_name)
            save_to_dynamodb_table(forms_table_name, filled_form)

        else:
            additional_conversation = {"role": "assistant", "content": value}
            chat_history = update_conversation_in_dynamodb(
                conversations_table_name, conversation_id, additional_conversation
            )

            print("Next question", value)
            print("chat_history updated with next question", chat_history)

    except Exception as e:
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": f"Exception={e}",
            "headers": {
                "content-type": "text/plain",
            },
        }

    return response


def lambda_get_form(event, context) -> dict:
    print("lambda_get_form Handler started")

    try:
        forms_table_name = os.environ["FILLED_FORMS_TABLE_NAME"]
        print("FILLED_FORMS_TABLE_NAME", forms_table_name)
        forms_table = get_dynamodb_table(forms_table_name)

        conversation_id = event.get("pathParameters")["conversation_id"]
        print("conversation_id:", conversation_id)

        # Retrieve the item from DynamoDB
        response = forms_table.get_item(Key={"conversation_id": conversation_id})
        print("response", response)
        filled_form = response.get("Item", {})
        print("filled_form from table", filled_form)

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(filled_form, indent=2),
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
