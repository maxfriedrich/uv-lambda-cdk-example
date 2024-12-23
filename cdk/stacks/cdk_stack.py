from aws_cdk import Stack
from constructs import Construct

from stacks.constructs.python_lambda_function import PythonLambdaFunction


class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        PythonLambdaFunction(
            self,
            "Lambda1",
            package_name="demo-lambda1",
            handler="demo_lambda1.lambda_function.lambda_handler",
        )

        PythonLambdaFunction(
            self,
            "Lambda2",
            package_name="demo-lambda2",
            handler="demo_lambda2.lambda_function.lambda_handler",
        )
