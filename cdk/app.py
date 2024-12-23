#!/usr/bin/env python3

import aws_cdk as cdk
from stacks.cdk_stack import CdkStack

app = cdk.App()
CdkStack(app, "CdkStack")

app.synth()
