import os
from constructs import Construct
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    CfnOutput,
    Duration,
    aws_s3 as s3,
    aws_secretsmanager as sm,
)
import aws_cdk.aws_apigatewayv2_alpha as _apigw
import aws_cdk.aws_apigatewayv2_integrations_alpha as _integrations

from os.path import dirname


DIRNAME = dirname(dirname(__file__))


class InsuranceFillsServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            "FilledInsuranceBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            bucket_name="filled-insurance-bucket",
        )

        secret = sm.Secret.from_secret_name_v2(
            self, "insurance_secret", "insurance_fills_secrets"
        )

        # Create the Lambda function to receive the request
        # The source code is in './lambdas' directory
        lambda_fn = lambda_.Function(
            self,
            "InsuranceFunction",
            function_name="fill_insurance_function",
            runtime=lambda_.Runtime.FROM_IMAGE,
            code=lambda_.Code.from_asset_image("lambdas/fill_insurance"),
            handler=lambda_.Handler.FROM_IMAGE,
            timeout=Duration.seconds(30),
            environment={"BUCKET_NAME": bucket.bucket_name},
        )

        secret.grant_read(lambda_fn)

        bucket.grant_write(lambda_fn)

        # Create the HTTP API with CORS
        http_api = _apigw.HttpApi(
            self,
            "MyHttpApi",
            cors_preflight=_apigw.CorsPreflightOptions(
                allow_methods=[_apigw.CorsHttpMethod.GET],
                allow_origins=["*"],
                max_age=Duration.days(10),
            ),
        )

        # Add a route to GET /
        http_api.add_routes(
            path="/",
            methods=[_apigw.HttpMethod.GET],
            integration=_integrations.HttpLambdaIntegration(
                "LambdaProxyIntegration", handler=lambda_fn
            ),
        )

        # Outputs
        CfnOutput(
            self,
            "API Endpoint",
            description="API Endpoint",
            value=http_api.api_endpoint,
        )
