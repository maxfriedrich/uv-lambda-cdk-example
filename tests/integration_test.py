import json

import boto3
import pytest


@pytest.fixture
def cf_client():
    return boto3.client("cloudformation", region_name="eu-central-1")


@pytest.fixture
def lambda_client():
    return boto3.client("lambda", region_name="eu-central-1")


def get_lambda_arn(cf_client, stack_name):
    response = cf_client.describe_stacks(StackName=stack_name)
    outputs = response["Stacks"][0].get("Outputs", [])
    return next(
        (output["OutputValue"] for output in outputs if output["OutputKey"] == "LambdaFunctionArn"),
        None,
    )


def call_function(lambda_client, arn):
    return lambda_client.invoke(FunctionName=arn, InvocationType="RequestResponse")


@pytest.mark.parametrize(
    ["stack_name", "expected"],
    [
        ("Lambda1Stack", "Hello from Lambda with orjson! Common value: 123"),
        ("Lambda2Stack", "Hello from Lambda with stdlib json and pydantic!"),
        ("DockerLambda1Stack", "Hello from Lambda with orjson! Common value: 123"),
    ],
)
@pytest.mark.integration
def test_lambda(stack_name, expected, cf_client, lambda_client):
    arn = get_lambda_arn(cf_client, stack_name)
    response = call_function(lambda_client, arn)
    response = json.loads(response["Payload"].read())
    print(response)
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == expected
