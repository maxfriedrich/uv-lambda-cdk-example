from aws_cdk import CfnOutput, Stack
from constructs import Construct
from python_lambda_function import PythonLambdaFunction


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

        CfnOutput(self, "LambdaFunctionUrl", value=url.url)
