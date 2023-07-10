#!/usr/bin/env python3

import aws_cdk as cdk

from insurance_fills_service.insurance_fills_service_stack import InsuranceFillsServiceStack


app = cdk.App()
InsuranceFillsServiceStack(app, "insurance-fills-service")

app.synth()
