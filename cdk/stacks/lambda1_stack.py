from aws_cdk import Stack, aws_ssm
from constructs import Construct

from stacks.constructs.python_lambda_function import PythonLambdaFunction


class Lambda1Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        function = PythonLambdaFunction(
            self,
            "Lambda1",
            package_name="demo-lambda1",
            handler="demo_lambda1.lambda_function.lambda_handler",
        )
        url = function.add_function_url()
        aws_ssm.StringParameter(
            self,
            "Lambda1Url",
            parameter_name="/demo/lambda1/url",
            string_value=url.to_string(),
        )
