import os

from constructs import Construct
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    CfnOutput,
    Duration,
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

        secret = sm.Secret.from_secret_name_v2(
            self, "insurance_secret", "insurance_fills_secrets"
        )

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

        # table to store conversation_id and conversation
        conversations_table = dynamodb.Table(
            self,
            "ConversationsTable",
            partition_key=dynamodb.Attribute(
                name="conversation_id", type=dynamodb.AttributeType.STRING
            ),
        )

        # table to store final filled forms
        filled_forms_table = dynamodb.Table(
            self,
            "FilledFormsTable",
            partition_key=dynamodb.Attribute(
                name="conversation_id", type=dynamodb.AttributeType.STRING
            ),
        )

        # POST create forms lambda
        lambda_create_form = lambda_.Function(
            self,
            "InsuranceFunctionCreate",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(os.path.join(DIRNAME, "lambdas/create_get")),
            handler="create_get_lambda.lambda_create_form",
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
        lambda_update = lambda_.Function(
            self,
            "InsuranceFunctionUpdate",
            runtime=lambda_.Runtime.FROM_IMAGE,
            code=lambda_.Code.from_asset_image("lambdas/update"),
            handler=lambda_.Handler.FROM_IMAGE,
            timeout=Duration.seconds(30),
            environment={
                "CONVERSATION_TABLE_NAME": conversations_table.table_name,
                "FILLED_FORMS_TABLE_NAME": filled_forms_table.table_name,
            },
        )

        secret.grant_read(lambda_update)

        # Add a route to POST /form/{conversation_id}
        http_api.add_routes(
            path="/form/{conversation_id}",
            methods=[_apigw.HttpMethod.POST],
            integration=_integrations.HttpLambdaIntegration(
                "LambdaProxyIntegration", handler=lambda_update
            ),
        )

        conversations_table.grant_read_write_data(lambda_update)
        filled_forms_table.grant_read_write_data(lambda_update)

        # GET form lambda
        lambda_get_form = lambda_.Function(
            self,
            "InsuranceFunctionGet",
            # function_name=f"fill_insurance_function_get_{stage}",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(os.path.join(DIRNAME, "lambdas/create_get")),
            handler="create_get_lambda.lambda_get_form",
            timeout=Duration.seconds(30),
            environment={
                "FILLED_FORMS_TABLE_NAME": filled_forms_table.table_name,
            },
        )

        # Add a route to GET /form
        http_api.add_routes(
            path="/form/{conversation_id}",
            methods=[_apigw.HttpMethod.GET],
            integration=_integrations.HttpLambdaIntegration(
                "LambdaProxyIntegration", handler=lambda_get_form
            ),
        )

        filled_forms_table.grant_read_data(lambda_get_form)

        # Outputs
        CfnOutput(
            self,
            "API Endpoint",
            description="API Endpoint",
            value=http_api.api_endpoint,
        )
