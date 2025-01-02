# Example for Python Lambda Functions in CDK with uv

This repo shows how we build reproducible (byte-for-byte + same CDK asset hash) AWS Lambda .zips from packages in a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/).

Motivation and how and why it works is described in this post: https://maxfriedrich.de/2025/01/02/uv-lambda-cdk/

## Run locally

Make sure CDK (aws-cdk) is installed.

Build asset directories (does not require an AWS account):

```bash
cd cdk
uv run cdk synth
# find the assets in cdk/cdk.out
uv run cdk synth
# no new assets should be added
```

Deploy:

```bash
cd cdk
export AWS_PROFILE=... # or configure AWS account in some other way
uv run cdk bootstrap
uv run cdk deploy --all
uv run cdk diff
# the diff should now show 0 differences, no need to re-deploy
```

Call the Lambda functions:

```bash
export AWS_PROFILE=... # or configure AWS account in some other way
uv run pytest tests -m integration
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
  - invoke-function (to call the functions for testing, constrain the resource if needed):
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": [
                    "*"
                ]
            }
        ]
    }
    ```
