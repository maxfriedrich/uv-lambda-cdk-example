#!/usr/bin/env python3

import aws_cdk as cdk
from stacks.lambda1_stack import Lambda1Stack
from stacks.lambda2_stack import Lambda2Stack

app = cdk.App()
Lambda1Stack(app, "Lambda1Stack")
Lambda2Stack(app, "Lambda2Stack")

app.synth()
