import os
from functools import wraps
from uuid import uuid4

import boto3

from moto import mock_aws


def secretsmanager_aws_verified(func):
    """
    Function that is verified to work against AWS.
    Can be run against AWS at any time by setting:
      MOTO_TEST_ALLOW_AWS_REQUEST=true

    If this environment variable is not set, the function runs in a `mock_aws` context.
    """

    @wraps(func)
    def pagination_wrapper(**kwargs):
        allow_aws_request = (
            os.environ.get("MOTO_TEST_ALLOW_AWS_REQUEST", "false").lower() == "true"
        )

        if allow_aws_request:
            return create_secret_and_execute(kwargs, func)
        else:
            with mock_aws():
                return create_secret_and_execute(kwargs, func)

    def create_secret_and_execute(kwargs, func):
        sm_client = boto3.client("secretsmanager", "us-east-1")

        secret = sm_client.create_secret(
            Name=f"moto_secret_{str(uuid4())[0:6]}",
            SecretString="old_secret",
        )
        try:
            kwargs["secret"] = secret
            return func(**kwargs)
        finally:
            sm_client.delete_secret(SecretId=secret["ARN"])

    return pagination_wrapper
