#!/usr/bin/env python3
import os

import aws_cdk as cdk

from insurance_fills_service.insurance_fills_service_stack import (
    InsuranceFillsServiceStack,
)

stage = os.environ.get("STAGE", default="dev")

app = cdk.App()
InsuranceFillsServiceStack(app, f"insurance-fills-service-{stage}", stage=stage)

app.synth()
