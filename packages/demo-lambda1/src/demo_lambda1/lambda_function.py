import orjson
from demo_common import common_value


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": orjson.dumps(f"Hello from Lambda with orjson! Common value: {common_value}"),
    }
