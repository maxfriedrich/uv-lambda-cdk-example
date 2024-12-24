# Example for Python Lambda Functions in CDK with uv

GitHub Actions integration:

- Set up [GitHub OIDC](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- Create `GitHubActionsDeployment` role with permissions:
  - assume-cdk-roles:
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
  - AWSCloudFormationReadOnlyAccess (to read the function URLs from CfnOutput)
  - AWSLambdaRole (to call the functions for testing)