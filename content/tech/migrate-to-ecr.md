Title: Migrating from a heterogeneous Docker setup to a centralized ECR registry

### The Problem

Say our organization that uses Kubernetes, powered by EKS on AWS, has 
"organically" evolved to a state where its Docker images are built and/or hosted on 
an amalgamation of vendors, cloud providers & services:

- some are built on GCP using Cloud Build and then pushed to Artifact Registry
- some are built on GitHub actions and then pushed to Artifact Registry and/or ECR
- others are simply pulled by the EKS worker nodes from random registries all over the Internet

The third point should especially make you cringe, especially if, like me, you
have a history with financial services. With the frequency of supply 
chain attacks these days, pulling Docker images from outside-the-house
registries is a big no-no.

But I digress: the point of this article is to present a solution for migrating
all of the Docker images pulled by the EKS workers onto a private container
registry on AWS, powered by ECR.

To make things spicy we'll also make a couple of scale- and isolation-related
assumptions:

- our fictive organization uses multiple different AWS _accounts_ (think `prod`, `staging`, `ci`)
- our fictive organization has EKS clusters in different _regions_

### The Solution

#### Federated authentication from Google CloudBuild to AWS ECR

First, we'll need to make sure the GCP service account building our docker images
can authenticate towards AWS. We'll use Terraform syntax to encode the IAM resources
required on the AWS side and a bit of Python glue code to perform all the token
juggling.

This is how the authentication flow will look like:

```
GCB Service Account                      GCP API                      AWS API
  |                                         |                            |
  |-------- GET signed JWT token ---------->|                            |
  |                                         |                            |
  |<--------- Signed JWT token -------------|                            |
  |                                         |                            |
  |-- Exchange JWT token for OAuth token -->|                            |
  |                                         |                            |
  |<------------ OAuth token ---------------|                            |
  |                                         |                            |
  |---------- Exchange OAuth token for temporary IAM credentials ------->|
  |                                         |                            |
  |<----------------------- Temporary IAM credentials -------------------|
  |                                         |                            |
```

First, we'll need to create an IAM role that's assumable by the GCB Service 
Account. For brevity, we'll give this role full administrative permissions
over the ECR service, but in a real-world scenario you should definitely distill
these down to only the actions/repositories that you intend to let GCB push to.

First, let's define some variables that we'll use to parametrize our resources.


```terraform
# in variables.tf
variable "prefix" {
  type    = string
  default = "acme-inc"
}

variable "gcp_service_account" {
  description = "GCP service account email to allow federated login from."
  type        = string
  nullable    = false
  default     = "replace@me.com"
}

variable "target_audience" {
  description = "An internal URL for scoping the federated login."
  type        = string
  nullable    = false
  default     = "https://gcp-to-aws-federation.acme.com"
}
```

The GCP service account is usually a valid "email" address in the form:
`role-name@<gcp-project-id>.iam.gserviceaccount.com`.

Creating the AWS IAM role is straightforward:

```terraform
# in federated_role.tf
resource "aws_iam_role" "gcp_to_aws" {
  name               = "${var.prefix}-gcp-to-aws-role"
  assume_role_policy = data.aws_iam_policy_document.gcp_to_aws_policy.json
}
```

We'll give it a role assuming policy checking both the target audience and the
requesting service account:

```terraform
# in federated_role.tf
data "aws_iam_policy_document" "gcp_to_aws_policy" {
  statement {
    sid     = ""
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "accounts.google.com:oaud"
      values   = [var.target_audience]
    }

    condition {
      test     = "StringEquals"
      variable = "accounts.google.com:aud"
      values   = [var.gcp_service_account]
    }

    condition {
      test     = "Null"
      variable = "accounts.google.com:oaud"
      values   = ["false"]
    }

    condition {
      test     = "Null"
      variable = "accounts.google.com:aud"
      values   = ["false"]
    }

    principals {
      type        = "Federated"
      identifiers = ["accounts.google.com"]
    }
  }
}
```

Then we'll create a role policy that allows all actions to be performed on
all ECR repositories and attach the policy to our new role:

```terraform
# in federated_role.tf
resource "aws_iam_policy" "ecr_push" {
  name   = "${var.prefix}-gcp-to-aws-ecr-permissions"
  policy = data.aws_iam_policy_document.ecr_permissions.json
}

data "aws_iam_policy_document" "ecr_permissions" {
  statement {
    actions   = ["ecr:*"]
    resources = ["*"]
    effect    = "Allow"
  }
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
    effect    = "Allow"
  }
}

resource "aws_iam_role_policy_attachment" "ecr_permissions" {
  role       = aws_iam_role.gcp_to_aws.name
  policy_arn = aws_iam_policy.ecr_permissions.arn
}
```

Don't forget to specify the AWS provider for the Terraform setup:

```terraform
# in providers.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```

Then go through a `terraform init; terraform plan; terraform apply` cycle,
making sure to replace the defaults in the `variables.tf` files with the values
from your organization / setup. Alternatively, you can pass the values via
`-var` command line flags to terraform.

If all worked well, you should have a new IAM role in your account that's 
assumable via federation.

Hurray! 🥳

Ok, now let's move on with the Python glue code. This code will be executed
by the GCB runner and will go through the flow described at the beginning of the
section.

Let's get a minimal Python dev environment going:

```shell
python -m venv .venv
source .venv/bin/activate

cat > requirements.txt <<EOF
boto3>=1.34
botocore>=1.34
click>=8.1
google-api-python-client>=2.126
google-auth-oauthlib>=1.2
EOF

pip install -r requirements.txt
```

This will give us a virtual environment with the minimum requirements for our
purposes:

- `boto3` to interact with the AWS APIs
- `google-api-python-client` and `google-auth-oauthlib` to interact with the GCP APIs
- `click` to wrap it all up in a nice CLI

Let's obtain credentials from GCP that we can later use to generate the 
signed JWT token:

```python
import sys
from typing import Optional

from google.auth.credentials import Credentials
from google.auth import default
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request


def _get_default_credentials() -> Optional[Credentials]:
    credentials, _ = default(
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/iam",
        ]
    )

    try:
        credentials.refresh(Request())
    except GoogleAuthError as e:
        print(f"Failed to refresh credentials: {e}", file=sys.stderr)
        return None

    return credentials
```

Now, let's use these credentials in a function that generates the signed JWT
token:

```python
import sys
import time
from typing import Callable, Optional

from google.auth import jwt
from google.auth.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.iam import Signer
from google.auth.transport.requests import Request

JWT_BEARER_TOKEN_EXPIRY_TIME: int = 3600
OAUTH_TOKEN_URI: str = "https://www.googleapis.com/oauth2/v4/token"


def _get_signed_jwt(
        service_account: str,
        target_audience: str,
        credential_provider: Callable[
            ..., Optional[Credentials]
        ] = _get_default_credentials,
) -> Optional[bytes]:
    if (credentials := credential_provider()) is None:
        return None

    now = int(time.time())
    payload = {
        "iss": service_account,
        "aud": OAUTH_TOKEN_URI,
        "target_audience": target_audience,
        "iat": now,
        "exp": now + JWT_BEARER_TOKEN_EXPIRY_TIME,
    }

    signer = Signer(Request(), credentials, service_account)

    try:
        return jwt.encode(signer, payload)
    except GoogleAuthError as e:
        print(f"Failed to produce a signed JWT token: {e}", file=sys.stderr)
        return None
```

We're using a simple "dependency injection" pattern here and passing the function
generating the credentials as an argument of `_get_signed_jwt`. This will help
with writing tests.

The other two arguments to this function are the service account identifier
and the target audience, both of which should precisely match what we used earlier
in the Terraform code.

After the GCP API has so kindly provided us with a signed JWT token, we'll 
exchange it for an OAuth token:

```python
import sys
from typing import Callable, Optional

import requests

JWT_BEARER_TOKEN_GRANT_TYPE: str = "urn:ietf:params:oauth:grant-type:jwt-bearer"
OAUTH_TOKEN_URI: str = "https://www.googleapis.com/oauth2/v4/token"


def _get_oauth_token(
    signed_jwt: bytes,
    requester: Callable[..., requests.Response] = requests.post,
) -> Optional[str]:
    data = {"grant_type": JWT_BEARER_TOKEN_GRANT_TYPE, "assertion": signed_jwt}
    response = requester(OAUTH_TOKEN_URI, data=data)

    try:
        response.raise_for_status()
        result_dict = response.json()
        return result_dict.get("id_token")
    except requests.exceptions.RequestException as e:
        print(f"Failed to exchange JWT for OAuth token: {e}", file=sys.stderr)
        return None
```

Finally, if all went well, we'll be able to pass the OAuth token to the AWS API
via boto and get those temporary AWS credentials we've worked so hard for.

We'll wrap the result in dataclass (TODO: link) so it's strongly typed and
we have a convenient place for format transformations. As an example, we can
format them as shell export block, so the output of our program could be directly
`eval`-ed.

```python
from dataclasses import dataclass
import sys
from typing import Optional

import boto3
from botocore.exceptions import ClientError as BotoError


@dataclass(frozen=True)
class BotoCredentials:
    access_key_id: str
    secret_access_key: str
    session_token: str

    def as_export_block(self) -> str:
        return (
            f"export AWS_ACCESS_KEY_ID={self.access_key_id}\n"
            f"export AWS_SECRET_ACCESS_KEY={self.secret_access_key}\n"
            f"export AWS_SESSION_TOKEN={self.session_token}\n"
        )


def _get_boto_credentials(
        role_arn: str, session_name: str, token: str
) -> Optional[BotoCredentials]:
    client = boto3.client("sts")

    try:
        response = client.assume_role_with_web_identity(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            WebIdentityToken=token,
        )
    except BotoError as e:
        print(f"Failed to assume AWS role: {e}", file=sys.stderr)
        return None

    return BotoCredentials(
        access_key_id=response["Credentials"]["AccessKeyId"],
        secret_access_key=response["Credentials"]["SecretAccessKey"],
        session_token=response["Credentials"]["SessionToken"],
    )
```

Putting all of it together and wrapping it with some `click` decorators to
get a smooth CLI:

```python
import sys

import click

@click.command
@click.option(
    "--gcp-service-account",
    envvar="GCP_SERVICE_ACCOUNT",
    required=True,
    help="The GCP service account to use for federation.",
    type=str,
)
@click.option(
    "--target-audience-url",
    envvar="TARGET_AUDIENCE_URL",
    required=True,
    help="The target audience URL, same as the one configured in the AWS IAM role trust policy.",
    type=str,
)
@click.option(
    "--aws-iam-role-arn",
    envvar="AWS_IAM_ROLE_ARN",
    required=True,
    help="The AWS IAM role to assume.",
    type=str,
)
@click.option(
    "--aws-session-name",
    envvar="AWS_SESSION_NAME",
    required=True,
    help="An unique name for the assumed role session.",
    type=str,
)
def federate_gcp_to_aws(
    gcp_service_account: str,
    target_audience_url: str,
    aws_iam_role_arn: str,
    aws_session_name: str,
) -> None:
    """
    Use a GCP service account to obtain ephemeral AWS credentials for the given IAM role.
    """
    if (
        _signed_jwt := _get_signed_jwt(
            gcp_service_account,
            target_audience=target_audience_url,
        )
    ) is None:
        sys.exit(1)

    if (_token := _get_oauth_token(_signed_jwt)) is None:
        sys.exit(1)

    if (
        _boto_credentials := _get_boto_credentials(
            role_arn=aws_iam_role_arn,
            session_name=aws_session_name,
            token=_token,
        )
    ) is None:
        sys.exit(1)
    print(_boto_credentials.as_export_block())


if __name__ == "__main__":
    federate_gcp_to_aws()
```

For the TLDR inclined among us, here's the final version of the script [hosted
as a gist](https://gist.github.com/rarescosma/03a50a9695ef420f23faad12bbb990f8).

## TODO
- ditto for github
- horizontal replication: images from the `ci` account should be replicated to ECR repositories
sitting in the `prod` and `staging` accounts
- vertical replication: images in the `prod` and `staging` registries should be available in both `eu-north-1` and `eu-west-1` availability zones
