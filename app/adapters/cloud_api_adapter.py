"""
Pulls live resource config directly from AWS via boto3 -- no Terraform
required. Outputs the same normalized shape as terraform_adapter.py.

IMPORTANT: this must only ever run with read-only credentials
(AWS managed policy `ReadOnlyAccess`, or a tighter custom policy scoped to
s3:Get*/List*, ec2:Describe*, iam:Get*/List*). This scanner inspects infra,
it never needs write access to it.
"""
import boto3

from app.config import settings
from app.models import ResourceConfig
from app.runtime_config import get_runtime_config


def _session() -> boto3.Session:
    """Prefers explicit keys from the runtime settings panel; falls back
    to a local AWS profile (~/.aws/credentials) if none were supplied.
    Never logs or persists whichever credentials get used here."""
    rc = get_runtime_config()
    if rc.aws_access_key_id and rc.aws_secret_access_key:
        return boto3.Session(
            aws_access_key_id=rc.aws_access_key_id,
            aws_secret_access_key=rc.aws_secret_access_key,
            region_name=rc.aws_region or settings.aws_region,
        )
    return boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)


def _pull_s3_buckets(session: boto3.Session) -> list[ResourceConfig]:
    s3 = session.client("s3")
    resources = []
    for bucket in s3.list_buckets().get("Buckets", []):
        name = bucket["Name"]
        config = {}

        try:
            acl = s3.get_bucket_acl(Bucket=name)
            config["grants"] = [
                {
                    "grantee": g.get("Grantee", {}).get("URI", g.get("Grantee", {}).get("ID")),
                    "permission": g.get("Permission"),
                }
                for g in acl.get("Grants", [])
            ]
        except Exception as e:  # noqa: BLE001 -- best-effort inspection, log and continue
            config["acl_error"] = str(e)

        try:
            enc = s3.get_bucket_encryption(Bucket=name)
            config["encryption"] = enc["ServerSideEncryptionConfiguration"]
        except s3.exceptions.ClientError:
            config["encryption"] = None  # no encryption configured -- itself a finding

        resources.append(
            ResourceConfig(
                resource_type="aws_s3_bucket",
                name=name,
                config=config,
                source="live_api",
            )
        )
    return resources


def _pull_security_groups(session: boto3.Session) -> list[ResourceConfig]:
    ec2 = session.client("ec2")
    resources = []
    for sg in ec2.describe_security_groups().get("SecurityGroups", []):
        resources.append(
            ResourceConfig(
                resource_type="aws_security_group",
                name=sg.get("GroupName", sg["GroupId"]),
                config={
                    "group_id": sg["GroupId"],
                    "ip_permissions": sg.get("IpPermissions", []),
                },
                source="live_api",
            )
        )
    return resources


def _pull_iam_roles(session: boto3.Session) -> list[ResourceConfig]:
    iam = session.client("iam")
    resources = []
    for role in iam.list_roles().get("Roles", []):
        role_name = role["RoleName"]
        policies = iam.list_role_policies(RoleName=role_name).get("PolicyNames", [])
        inline_policy_docs = []
        for p_name in policies:
            doc = iam.get_role_policy(RoleName=role_name, PolicyName=p_name)
            inline_policy_docs.append(doc.get("PolicyDocument"))

        resources.append(
            ResourceConfig(
                resource_type="aws_iam_role_policy",
                name=role_name,
                config={"inline_policies": inline_policy_docs},
                source="live_api",
            )
        )
    return resources


def pull_all() -> list[ResourceConfig]:
    """Pick 2-3 resource types for day one -- these three cover the classic
    SOC2 findings (public exposure, missing encryption, over-permissioning)."""
    session = _session()
    return (
        _pull_s3_buckets(session)
        + _pull_security_groups(session)
        + _pull_iam_roles(session)
    )


if __name__ == "__main__":
    for r in pull_all():
        print(f"{r.resource_type}: {r.name}")
