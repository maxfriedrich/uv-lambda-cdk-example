# Example for Python Lambda Functions in CDK with uv

This repo shows how we build reproducible (byte-for-byte + same CDK asset hash) AWS Lambda .zips with uv.

## Run locally

Build asset directories:

```bash
cd cdk
uv run cdk synth
# find the assets in cdk/cdk.out
```

Deploy and check reproducibility:

```bash
cd cdk
export AWS_PROFILE=... # or configure AWS account in some other way
uv run cdk bootstrap
uv run cdk deploy
uv run cdk diff
# the diff should now show 0 differences, no need to re-deploy
```

Call the Lambda functions:

```bash
export AWS_PROFILE=... # or configure AWS account in some other way
uv run integration_test.py
```

## GitHub Actions integration

- Set up [GitHub OIDC](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- Create `GitHubActionsDeployment` role with permissions:
  - assume-cdk-roles (to deploy with CDK):
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sts:AssumeRole"
                ],
                "Resource": [
                    "arn:aws:iam::*:role/cdk-*"
                ]
            }
        ]
    }
    ```
  - AWSCloudFormationReadOnlyAccess (to read the function URLs from CfnOutput for testing)
  - invoke-function-url (to call the functions for testing):
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunctionUrl"
                ],
                "Resource": [
                    "*"
                ]
            }
        ]
    }
    ```
