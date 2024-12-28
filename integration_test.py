import json

import boto3


def get_lambda_arn(cf_client, n):
    stack_name = f"Lambda{n}Stack"
    response = cf_client.describe_stacks(StackName=stack_name)
    outputs = response["Stacks"][0].get("Outputs", [])
    return next(
        (output["OutputValue"] for output in outputs if output["OutputKey"] == "LambdaFunctionArn"),
        None,
    )


def call_function(lambda_client, arn):
    return lambda_client.invoke(FunctionName=arn, InvocationType="RequestResponse")


def test_lambda(n, expected, cf_client, lambda_client):
    arn = get_lambda_arn(cf_client, n)
    response = call_function(lambda_client, arn)
    response = json.loads(response["Payload"].read())
    print(response)
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == expected


def main():
    cf_client = boto3.client("cloudformation", region_name="eu-central-1")
    lambda_client = boto3.client("lambda", region_name="eu-central-1")

    print("Calling Lambda 1...")
    test_lambda(1, "Hello from Lambda with orjson! Common value: 123", cf_client, lambda_client)
    print("Calling Lambda 2...")
    test_lambda(2, "Hello from Lambda with stdlib json and pydantic!", cf_client, lambda_client)
    print("Test successful!")


if __name__ == "__main__":
    main()
