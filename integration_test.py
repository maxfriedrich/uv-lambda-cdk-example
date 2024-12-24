import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import get_session


def get_lambda_url(cf_client, n):
    stack_name = f"Lambda{n}Stack"
    response = cf_client.describe_stacks(StackName=stack_name)
    outputs = response["Stacks"][0].get("Outputs", [])
    return next(
        (output["OutputValue"] for output in outputs if output["OutputKey"] == "LambdaFunctionUrl"),
        None,
    )


def call_function_url(url, credentials):
    request = AWSRequest(method="GET", url=url)
    SigV4Auth(credentials, "lambda", "eu-central-1").add_auth(request)

    return requests.request(
        method=request.method, url=request.url, headers=dict(request.headers), data=request.body
    )


def test_lambda1(cf_client, credentials):
    url = get_lambda_url(cf_client, 1)
    response = call_function_url(url, credentials)
    assert response.status_code == 200
    assert response.json() == "Hello from Lambda with orjson! Common value: 123"


def test_lambda2(cf_client, credentials):
    url = get_lambda_url(cf_client, 2)
    response = call_function_url(url, credentials)
    assert response.status_code == 200
    assert response.json() == "Hello from Lambda with stdlib json!"


def main():
    cf_client = boto3.client("cloudformation", region_name="eu-central-1")
    session = get_session()
    credentials = session.get_credentials().get_frozen_credentials()

    print("Calling Lambda 1...")
    test_lambda1(cf_client, credentials)
    print("Calling Lambda 2...")
    test_lambda2(cf_client, credentials)
    print("Test successful!")


if __name__ == "__main__":
    main()
