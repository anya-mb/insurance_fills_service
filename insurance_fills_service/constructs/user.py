from aws_cdk import Stack
from aws_cdk.aws_iam import User, Policy, PolicyStatement
from constructs import Construct


class UsersStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, stage: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.api_caller_user = User(self, "API-caller", user_name=f"API-caller-{stage}")
        policy = Policy(
            self,
            "API-caller_policy",
            statements=[
                PolicyStatement(resources=["*"], actions=["execute-api:Invoke"])
            ],
        )
        policy.attach_to_user(self.api_caller_user)
