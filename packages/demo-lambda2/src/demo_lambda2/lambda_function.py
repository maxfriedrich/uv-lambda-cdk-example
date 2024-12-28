import json

import pydantic  # noqa


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps("Hello from Lambda with stdlib json and pydantic!"),
    }
