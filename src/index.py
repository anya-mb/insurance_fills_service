from http import HTTPStatus
import json
import os


def handler(event, context):
    try:

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps('hello world!', indent=2),
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