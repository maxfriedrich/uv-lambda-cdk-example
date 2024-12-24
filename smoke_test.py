import boto3
import requests


def get_lambda_url(cf_client, n):
    stack_name = f"Lambda{n}Stack"
    response = cf_client.describe_stacks(StackName=stack_name)
    outputs = response["Stacks"][0].get("Outputs", [])
    return next(
        (output["OutputValue"] for output in outputs if output["OutputKey"] == "LambdaFunctionUrl"),
        None,
    )


def test_lambda1(cf_client):
    response = requests.get(get_lambda_url(cf_client, 1))
    assert response.status_code == 200
    print(response.text)
    assert response.text == "Hello from Lambda with orjson! Common value: 42"


def test_lambda2(cf_client):
    response = requests.get(get_lambda_url(cf_client, 2))
    assert response.status_code == 200
    print(response.text)
    assert response.text == "Hello from Lambda with stdlib json!"


def main():
    cf_client = boto3.client("cloudformation", region_name="eu-central-1")
    test_lambda1(cf_client)
    test_lambda2(cf_client)
    print("Smoke test successful!")


if __name__ == "__main__":
    main()
