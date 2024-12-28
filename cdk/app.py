#!/usr/bin/env python3

import aws_cdk
from aws_cdk import CfnOutput, Stack, aws_lambda
from constructs import Construct
from python_lambda_function import PythonLambdaFunction


class LambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, function_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        function = PythonLambdaFunction(self, function_id, **kwargs)
        CfnOutput(self, "LambdaFunctionArn", value=function.function_arn)


app = aws_cdk.App()
LambdaStack(
    app,
    "Lambda1Stack",
    function_id="Lambda1",
    path="..",
    package_name="demo-lambda1",
    handler="demo_lambda1.lambda_function.lambda_handler",
)
LambdaStack(
    app,
    "Lambda2Stack",
    function_id="Lambda2",
    path="..",
    package_name="demo-lambda2",
    handler="demo_lambda2.lambda_function.lambda_handler",
    architecture=aws_lambda.Architecture.X86_64,
    runtime=aws_lambda.Runtime.PYTHON_3_11,
    bundling_docker_image="ghcr.io/astral-sh/uv:0.5.13-python3.11-bookworm-slim@sha256:dc0c70e35f899c69cfe3674afac6186b210373d19d7ed77fd8ab1bdc45f8bf15",
)

app.synth()
