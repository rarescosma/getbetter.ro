Title: Hybrid cloud federation - authenticating from GCP into AWS

### Intro

This article is part of an upcoming series focusing on hosting all the container
images of an organization in a centralized ECR repository. 

The scenario presupposes that we start with a hybrid cloud setup: GCP + AWS.

Hence, the first problem we're going to solve is authenticating from GCP into
AWS.

Since 2024 is the [year of the serverless***less***ness](https://www.youtube.com/watch?v=aWfYxg-Ypm4),
we're going to assume we have _somewhere_ to run our code on the GCP side. Most
of the time that'll be just a [Cloud Build](https://cloud.google.com/build/docs) pipeline.

The main implication here is that the authentication flow will be executed using a GCP [Service Account](https://cloud.google.com/iam/docs/service-account-overview).

Successfully authenticating from this Service Account into AWS will let us,
for example, push resulting container images into ECR.

### Sneak peek: authentication flow

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

!!! info "But why?"

    At this point you might be wondering: "Why go through all _that_, when I can
    generate some long-lived AWS credentials, store them somewhere in GCP and
    decode them when needed?"

    Because long-lived credentials are a [bad idea](https://medium.com/datamindedbe/why-you-should-not-use-iam-users-d0368dd319d3).

We'll use Python to express the flow with the ambition level that the resulting 
code should be runnable by any GCP Cloud Builds.

But first, let's do some quick terraform to define the assumable AWS IAM role and the GCP Service Account.

### Prerequisite: creating an assumable IAM role in AWS

In this section we'll focus on creating an IAM role in AWS that's assumable 
by the GCP Service Account. 

We'll be using the [terraform language](https://developer.hashicorp.com/terraform/language) 
to define our resources.

Let's start by defining our provider:

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

Next, let's define a few variables common to all upcoming resources:

```terraform
# in variables.tf
variable "prefix" {
  type    = string
  default = "acme"
}

variable "gcp_service_account" {
  description = "GCP service account email to allow federated login from."
  type        = string
  nullable    = false
  default     = "gcp-assumer@gcp-project-id.iam.gserviceaccount.com"
}

variable "target_audience" {
  description = "An internal URL for scoping the federated login."
  type        = string
  nullable    = false
  default     = "https://gcp-to-aws-federation.acme.com"
}
```

The GCP service account is usually a valid "email" address in the form:
`gcp-assumer@gcp-project-id.iam.gserviceaccount.com`.

Creating the AWS IAM role is straightforward:

```terraform
# in federated_role.tf
resource "aws_iam_role" "gcp_to_aws" {
  name               = "${var.prefix}-gcp-to-aws"
  assume_role_policy = data.aws_iam_policy_document.gcp_to_aws_policy.json
}
```

We'll then attach a role-assuming policy checking both the target audience and the
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

Then go through a `terraform init; terraform plan; terraform apply` cycle,
making sure to replace the defaults in the `variables.tf` files with the values
from your organization / setup. Alternatively, you can pass the values via
`-var` command line arguments to terraform.

If all worked well, you should have a new IAM role in your AWS account that's 
assumable via federation.

Hurray! 🥳

### Prerequisite: creating a GCP Service Account

This section focuses on defining the GCP Service Account.

First, define the gcloud provider:

```terraform
# in providers.tf
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = ">= 5.26"
    }
  }
}
```

!!! warning

    Use a different directory for this set of `.tf` files than the one you used
    in the previous step. Separation of concerns and all that.

We'll capture our GCP project name in a variable, since it tends to be a required
property of most resources:

```terraform
# in variables.tf
variable "project" {
  type = string
  default = "genial-theory-419908"
}
```

Finally we'll define our service account making sure to grant the ["Service Account Token Creator"](https://cloud.google.com/iam/docs/service-account-permissions#token-creator-role) 
role which will allow it to generate JWT tokens and exchange them for OAuth tokens.

We'll also grant the `cloudbuild.builds.builder` and `logging.logWriter` roles 
to be able to use the SA for cloud builds and allow it to log.

```terraform
# in service_account.tf
resource "google_service_account" "gcp-sa" {
  project = var.project
  account_id = "gcp-assumer"
}

resource "google_project_iam_member" "gcp-project-iam-member" {
  project = var.project
  for_each = toset([
    "roles/iam.serviceAccountTokenCreator",
    "roles/logging.logWriter",
    "roles/cloudbuild.builds.builder",
  ])
  role = each.key
  member = "serviceAccount:${google_service_account.gcp-sa.email}"
}
```

Another `terraform init; terraform plan; terraform apply` cycle and the new 
Service Account should pop up in the GCP IAM console.

Hurray again! 🥳

### The federation dance

Ok, now let's move on to the Python code. This code will be executed
by the GCB runner (using the Service Account we created earlier) and will go 
through the flow described at the beginning of the article.

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

!!! info

    For brevity, I'll skip over the `import` statements in the sample code, but you're
    welcome to grab the final version of the script from [this gist](https://gist.github.com/rarescosma/03a50a9695ef420f23faad12bbb990f8).

Let's obtain credentials from GCP that we can later use to generate the 
signed JWT token. For code running inside Cloud Build the `auth/userinfo.email` 
scope would suffice. However, we'd like to test this code locally so we'll add the `auth/iam` scope.

```python
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
JWT_BEARER_TOKEN_EXPIRY_TIME: int = 3600
OAUTH_TOKEN_URI: str = "https://www.googleapis.com/oauth2/v4/token"


def _get_signed_jwt(
    service_account: str,
    target_audience: str,
    credential_provider: Callable[..., Optional[Credentials]] = _get_default_credentials,
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

!!! note

    We're using a simple "dependency injection" pattern here and passing the function
    generating the credentials as an argument of `_get_signed_jwt`. This will help
    with writing tests.

The other two arguments of this function are the service account identifier
and the target audience, both of which should precisely match what we used earlier
in the Terraform code.

Next, we'll exchange the signed JWT token for an OAuth token:

```python
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

We'll wrap the result in a [dataclass](https://docs.python.org/3/library/dataclasses.html) 
so it's strongly typed and we have a convenient place for format transformations. 
As an example, we can format them as shell export block, 
so the output of our program could be directly `eval`-ed in a shell script.

```python
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

For the TLDR-inclined among us, here's [a gist](https://gist.github.com/rarescosma/03a50a9695ef420f23faad12bbb990f8) 
with the final version of the script. 

To test the entire script locally we'll [impersonate](https://cloud.google.com/docs/authentication/use-service-account-impersonation)
the GCP Service Account locally and call our python script with it:

```shell
gcloud auth application-default login --impersonate-service-account=gcp-assumer@gcp-project-id.iam.gserviceaccount.com

./auth.py \
  --gcp-service-account gcp-assumer@gcp-project-id.iam.gserviceaccount.com \
  --target-audience-url https://gcp-to-aws-federation.acme.com \
  --aws-iam-role-arn arn:aws:iam::123456123456:role/acme-gcp-to-aws \
  --aws-session-name test-session
```

Replace with your own GCP project ID, AWS account ID, the target audience URL
you used when defining the AWS IAM role and the proper prefix (instead of `acme`)
and give it a go. If all worked well, you should be getting temporary AWS credentials,
formated shell-exportable variables:

```shell
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
```

And that's all folks. Stay tuned for part two, where we'll continue our federation
journey, this time going from GitHub actions into AWS.
