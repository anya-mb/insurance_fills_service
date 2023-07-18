import os

from constructs import Construct
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    CfnOutput,
    Duration,
    aws_s3 as s3,
    aws_secretsmanager as sm,
    aws_dynamodb as dynamodb,
)
import aws_cdk.aws_apigatewayv2_alpha as _apigw
import aws_cdk.aws_apigatewayv2_integrations_alpha as _integrations

# from aws_cdk.aws_apigatewayv2_authorizers_alpha import HttpIamAuthorizer

from os.path import dirname

from insurance_fills_service.constructs.user import UsersStack

DIRNAME = dirname(dirname(__file__))


class InsuranceFillsServiceStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, stage: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            "FilledInsuranceBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            bucket_name=f"filled-insurance-bucket-{stage}",
        )

        secret = sm.Secret.from_secret_name_v2(
            self, "insurance_secret", "insurance_fills_secrets"
        )

        # Create the Lambda function to receive the request
        # The source code is in './lambdas' directory
        lambda_fn = lambda_.Function(
            self,
            "InsuranceFunction",
            function_name=f"fill_insurance_function_{stage}",
            runtime=lambda_.Runtime.FROM_IMAGE,
            code=lambda_.Code.from_asset_image("lambdas/fill_insurance"),
            handler=lambda_.Handler.FROM_IMAGE,
            timeout=Duration.seconds(30),
            environment={"BUCKET_NAME": bucket.bucket_name},
        )

        secret.grant_read(lambda_fn)

        bucket.grant_write(lambda_fn)

        UsersStack(self, f"users-{stage}", stage)

        # Create the HTTP API with CORS
        # authorizer = HttpIamAuthorizer()
        http_api = _apigw.HttpApi(
            self,
            "MyHttpApi",
            cors_preflight=_apigw.CorsPreflightOptions(
                allow_methods=[_apigw.CorsHttpMethod.GET],
                allow_origins=["*"],
                max_age=Duration.days(10),
            ),
            # default_authorizer=authorizer,
        )

        # Add a route to GET /
        http_api.add_routes(
            path="/",
            methods=[_apigw.HttpMethod.GET],
            integration=_integrations.HttpLambdaIntegration(
                "LambdaProxyIntegration", handler=lambda_fn
            ),
        )

        # table to store conversation_id and conversation
        conversations_table = dynamodb.Table(
            self,
            "ConversationsTable",
            partition_key=dynamodb.Attribute(
                name="conversation_id", type=dynamodb.AttributeType.STRING
            ),
            table_name=f"ConversationsTable{stage}",
        )
        # # table to store final filled forms
        # filled_forms_table = dynamodb.Table(
        #     self,
        #     "FilledFormsTable",
        #     partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
        #     sort_key=dynamodb.Attribute(name="form_id", type=dynamodb.AttributeType.STRING),
        #     table_name=f"FilledFormsTable{stage}",
        # )

        # POST create forms lambda
        lambda_create_form = lambda_.Function(
            self,
            "InsuranceFunctionCreateForm",
            function_name=f"fill_insurance_function_create_form_{stage}",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(os.path.join(DIRNAME, "lambdas/crud")),
            handler="app.lambda_create_form",
            timeout=Duration.seconds(30),
            environment={"CONVERSATION_TABLE_NAME": conversations_table.table_name},
        )

        # Add a route to POST /form
        http_api.add_routes(
            path="/form",
            methods=[_apigw.HttpMethod.POST],
            integration=_integrations.HttpLambdaIntegration(
                "LambdaProxyIntegration", handler=lambda_create_form
            ),
        )
        conversations_table.grant_write_data(lambda_create_form)

        # POST create forms lambda
        lambda_update_form = lambda_.Function(
            self,
            "InsuranceFunctionUpdateForm",
            function_name=f"fill_insurance_function_update_form_{stage}",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(os.path.join(DIRNAME, "lambdas/crud")),
            handler="app.lambda_update_form",
            timeout=Duration.seconds(30),
            environment={
                "CONVERSATION_TABLE_NAME": conversations_table.table_name,
                # "FILLED_FORMS_TABLE_NAME": filled_forms_table.table_name,
            },
        )

        # Add a route to POST /form/{conversation_id}
        http_api.add_routes(
            path="/form/{conversation_id}",
            methods=[_apigw.HttpMethod.POST],
            integration=_integrations.HttpLambdaIntegration(
                "LambdaProxyIntegration", handler=lambda_update_form
            ),
        )

        conversations_table.grant_read_write_data(lambda_update_form)

        # filled_forms_table.grant_read_write_data(lambda_update_form)

        # Outputs
        CfnOutput(
            self,
            "API Endpoint",
            description="API Endpoint",
            value=http_api.api_endpoint,
        )
