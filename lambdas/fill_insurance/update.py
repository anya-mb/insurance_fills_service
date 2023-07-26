import json
import os
import logging
from http import HTTPStatus
import boto3
from botocore.exceptions import ClientError
from time import gmtime, strftime
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt


# openai functions
FUNCTIONS = [
    {
        "name": "save_users_questionnaire",
        "description": "If user responded all questions, store fully filled questionnaire to the database",
        "parameters": {
            "type": "object",
            "properties": {
                "user_answers": {
                    "type": "object",
                    "description": "Keys of the dict are questions to the user and values are user's responses \n"
                    "in strings to the corresponding questions",
                },
            },
            "required": ["user_answers"],
        },
    },
    {
        "name": "ask_follow_up_question",
        "description": "If the user didn't answer all the questions, generates an additional question to ask user.",
        "parameters": {
            "type": "object",
            "properties": {
                "next_question": {
                    "type": "string",
                    "description": "Next question which we will ask user to clarify their response",
                },
            },
            "required": ["next_question"],
        },
    },
]


SECRET_NAME = "insurance_fills_secrets"
SECRET_KEY_OPENAI_KEY = "open_ai_key"

GPT_MODEL = "gpt-4-0613"

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_secret():
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=SECRET_NAME)
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response["SecretString"]

    return json.loads(secret)


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


def update_conversation_in_dynamodb(
    table_name: str, conversation_id: str, additional_conversation: list
) -> list:
    """
    Function to update a conversation in DynamoDB
    """
    table = get_dynamodb_table(table_name)
    response = table.get_item(Key={"conversation_id": conversation_id})
    chat_history = response.get("Item", {})
    chat_history["conversation"].extend(additional_conversation)

    table.put_item(Item=chat_history)
    logger.info(f"Item is stored in the table: {table_name}")

    return chat_history["conversation"]


def generate_assistant_response(chat_history: list, openai_key) -> (bool, str):
    """
    Function to generate assistant response
    """
    chat = Chat()
    chat.upload_conversation_history(chat_history)
    is_finished, next_question = chat.generate_response_for_user(openai_key)

    return is_finished, next_question


def lambda_update(event, context) -> dict:
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

        openai_key = get_secret()[SECRET_KEY_OPENAI_KEY]

        is_finished, value = generate_assistant_response(chat_history, openai_key)
        print("is_finished, value")
        print(is_finished, value)
        result = {"next_question": value, "is_finished": is_finished}

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(result, indent=2),
            "headers": {"content-type": "application/json"},
        }

        if is_finished:
            print("is_finished", is_finished)
            filled_form = value
            filled_form["conversation_id"] = conversation_id
            filled_form["create_time"] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            forms_table_name = os.environ["FILLED_FORMS_TABLE_NAME"]
            print("filled_form", filled_form)
            save_to_dynamodb_table(forms_table_name, filled_form)
        else:
            additional_conversation = [{"role": "assistant", "content": value}]
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


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, openai_key, functions=None, model=GPT_MODEL):

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + openai_key,
    }
    print("messages in chat_completion_request")
    print(messages)

    json_data = {"model": model, "messages": messages}
    if functions is not None:
        json_data.update({"functions": functions})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


class Chat:
    def __init__(self):
        self.conversation_history = []
        # self._add_prompt("system", SYSTEM_SETUP_PROMPT)

    def _add_prompt(self, role: str, content: str):
        message = {"role": role, "content": content}
        self.conversation_history.append(message)

    def add_assistant_prompt(self, content: str):
        role = "assistant"
        self._add_prompt(role, content)

    def add_user_prompt(self, content: str):
        role = "user"
        self._add_prompt(role, content)

    def display_conversation(self):
        for message in self.conversation_history:
            print(
                f"{message['role']}: {message['content']}\n\n",
                message["role"],
            )

    def upload_conversation_history(self, conversation_history: list):
        self.conversation_history = conversation_history

    def generate_response_for_user(
        self, openai_key, functions: list = FUNCTIONS
    ) -> (bool, str):

        chat_response = chat_completion_request(
            self.conversation_history, openai_key, functions=functions
        )

        if chat_response is not None:
            print("chat_response:")
            print(chat_response)
            print(chat_response.json())
            # print(chat_response.error)

            response_content = chat_response.json()["choices"][0]["message"]

            message = chat_response.json()["choices"][0]["message"]["content"]

            print("message:")
            print(message)

            if message is not None:
                chat_finished = False
                return chat_finished, message

            if "function_call" in response_content:
                if (
                    response_content["function_call"]["name"]
                    == "save_users_questionnaire"
                ):

                    questionnaire = json.loads(
                        response_content["function_call"]["arguments"]
                    )
                    print("Result questionnaire:")
                    print(questionnaire)

                    chat_finished = True
                    return chat_finished, questionnaire

                elif (
                    response_content["function_call"]["name"]
                    == "ask_follow_up_question"
                ):
                    next_question = json.loads(
                        response_content["function_call"]["arguments"]
                    )["next_question"]
                    print("Next question:")
                    print(next_question)

                    chat_finished = False
                    return chat_finished, next_question

        else:
            print("ChatCompletion request failed. Retrying...")
