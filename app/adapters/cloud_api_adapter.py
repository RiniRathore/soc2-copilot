"""
Pulls live resource config directly from AWS via boto3 -- no Terraform
required. Outputs the same normalized shape as terraform_adapter.py.

IMPORTANT: this must only ever run with read-only credentials
(AWS managed policy `ReadOnlyAccess`, or a tighter custom policy scoped to
s3:Get*/List*, ec2:Describe*, iam:Get*/List*, rds:Describe*,
cloudtrail:Describe*/Get*, kms:List*/Describe*/Get*, config:Describe*).
This scanner inspects infra, it never needs write access to it.

Two kinds of checks this covers, modeled differently:
- Per-instance (S3 buckets, EBS volumes, RDS instances, security groups,
  IAM users/roles, KMS keys): one ResourceConfig per actual resource found.
- Account/region-level "is X enabled at all" (CloudTrail, AWS Config, IAM
  password policy): always emits exactly one ResourceConfig even when the
  underlying resource is *absent* -- e.g. zero CloudTrail trails is itself
  the finding, but a for-loop over an empty list would silently check
  nothing. These are captured as an explicit "not configured" state
  instead of being skipped.
"""
import boto3
from botocore.exceptions import ClientError

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
        except ClientError as e:
            config["acl_error"] = str(e)

        try:
            enc = s3.get_bucket_encryption(Bucket=name)
            config["encryption"] = enc["ServerSideEncryptionConfiguration"]
        except s3.exceptions.ClientError:
            config["encryption"] = None  # no encryption configured -- itself a finding

        try:
            pab = s3.get_public_access_block(Bucket=name)
            config["public_access_block"] = pab["PublicAccessBlockConfiguration"]
        except ClientError:
            config["public_access_block"] = None  # not configured -- itself a finding

        try:
            policy = s3.get_bucket_policy(Bucket=name)
            config["bucket_policy"] = policy["Policy"]
        except ClientError:
            config["bucket_policy"] = None

        try:
            ver = s3.get_bucket_versioning(Bucket=name)
            config["versioning_status"] = ver.get("Status")
            config["mfa_delete"] = ver.get("MFADelete")
        except ClientError as e:
            config["versioning_error"] = str(e)

        try:
            logging_cfg = s3.get_bucket_logging(Bucket=name)
            config["logging_enabled"] = "LoggingEnabled" in logging_cfg
        except ClientError as e:
            config["logging_error"] = str(e)

        resources.append(
            ResourceConfig(
                resource_type="aws_s3_bucket",
                name=name,
                config=config,
                source="live_api",
            )
        )
    return resources


def _pull_ebs_volumes(session: boto3.Session) -> list[ResourceConfig]:
    ec2 = session.client("ec2")
    resources = []
    for vol in ec2.describe_volumes().get("Volumes", []):
        resources.append(
            ResourceConfig(
                resource_type="aws_ebs_volume",
                name=vol["VolumeId"],
                config={
                    "encrypted": vol.get("Encrypted"),
                    "size": vol.get("Size"),
                    "availability_zone": vol.get("AvailabilityZone"),
                    "state": vol.get("State"),
                },
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
                    "vpc_id": sg.get("VpcId"),
                    "ip_permissions": sg.get("IpPermissions", []),
                },
                source="live_api",
            )
        )
    return resources


def _pull_network_acls(session: boto3.Session) -> list[ResourceConfig]:
    ec2 = session.client("ec2")
    resources = []
    for nacl in ec2.describe_network_acls().get("NetworkAcls", []):
        resources.append(
            ResourceConfig(
                resource_type="aws_network_acl",
                name=nacl["NetworkAclId"],
                config={
                    "vpc_id": nacl.get("VpcId"),
                    "is_default": nacl.get("IsDefault"),
                    "entries": nacl.get("Entries", []),
                },
                source="live_api",
            )
        )
    return resources


def _pull_vpc_flow_logs(session: boto3.Session) -> list[ResourceConfig]:
    """Account/region-level per-VPC check: every VPC must have a flow log.
    Modeled as one pseudo-resource per VPC (not per flow log) so a VPC with
    zero flow logs still gets evaluated instead of silently skipped."""
    ec2 = session.client("ec2")
    vpc_ids = [v["VpcId"] for v in ec2.describe_vpcs().get("Vpcs", [])]
    flow_logs_by_vpc: dict[str, list] = {}
    for fl in ec2.describe_flow_logs().get("FlowLogs", []):
        flow_logs_by_vpc.setdefault(fl.get("ResourceId"), []).append(fl)

    return [
        ResourceConfig(
            resource_type="aws_flow_log",
            name=vpc_id,
            config={"vpc_id": vpc_id, "flow_logs": flow_logs_by_vpc.get(vpc_id, [])},
            source="live_api",
        )
        for vpc_id in vpc_ids
    ]


def _pull_rds_instances(session: boto3.Session) -> list[ResourceConfig]:
    rds = session.client("rds")
    resources = []
    for db in rds.describe_db_instances().get("DBInstances", []):
        resources.append(
            ResourceConfig(
                resource_type="aws_db_instance",
                name=db["DBInstanceIdentifier"],
                config={
                    "engine": db.get("Engine"),
                    "publicly_accessible": db.get("PubliclyAccessible"),
                    "storage_encrypted": db.get("StorageEncrypted"),
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


def _pull_iam_users(session: boto3.Session) -> list[ResourceConfig]:
    iam = session.client("iam")
    resources = []
    for user in iam.list_users().get("Users", []):
        user_name = user["UserName"]

        has_console_access = True
        try:
            iam.get_login_profile(UserName=user_name)
        except iam.exceptions.NoSuchEntityException:
            has_console_access = False

        mfa_devices = iam.list_mfa_devices(UserName=user_name).get("MFADevices", [])
        access_keys = iam.list_access_keys(UserName=user_name).get("AccessKeyMetadata", [])

        resources.append(
            ResourceConfig(
                resource_type="aws_iam_user",
                name=user_name,
                config={
                    "has_console_access": has_console_access,
                    "mfa_device_count": len(mfa_devices),
                    "access_keys": [
                        {
                            "id": k["AccessKeyId"],
                            "status": k["Status"],
                            "create_date": str(k["CreateDate"]),
                        }
                        for k in access_keys
                    ],
                },
                source="live_api",
            )
        )
    return resources


def _pull_iam_account_settings(session: boto3.Session) -> list[ResourceConfig]:
    """Account-wide IAM posture: password policy + root account MFA/keys.
    Always emitted, even when no password policy exists at all -- that
    absence is itself CIS-1.7/1.8's finding."""
    iam = session.client("iam")

    try:
        policy = iam.get_account_password_policy()["PasswordPolicy"]
    except iam.exceptions.NoSuchEntityException:
        policy = None  # no password policy configured at all -- itself a finding

    summary = iam.get_account_summary().get("SummaryMap", {})

    return [
        ResourceConfig(
            resource_type="aws_iam_account_password_policy",
            name="account-password-policy",
            config={"password_policy": policy},
            source="live_api",
        ),
        ResourceConfig(
            resource_type="aws_iam_account_password_policy",  # same control area: root account posture
            name="root-account",
            config={
                "root_mfa_enabled": bool(summary.get("AccountMFAEnabled")),
                "root_access_keys_present": bool(summary.get("AccountAccessKeysPresent")),
            },
            source="live_api",
        ),
    ]


def _pull_cloudtrail_trails(session: boto3.Session) -> list[ResourceConfig]:
    """Account-level: emits one resource per trail found, or one explicit
    "no trail configured" resource if there are none -- CIS-3.1 must be
    evaluable either way."""
    ct = session.client("cloudtrail")
    trails = ct.describe_trails().get("trailList", [])

    if not trails:
        return [
            ResourceConfig(
                resource_type="aws_cloudtrail",
                name="no-trail-configured",
                config={"trail_exists": False},
                source="live_api",
            )
        ]

    resources = []
    for trail in trails:
        name = trail["Name"]
        try:
            status = ct.get_trail_status(Name=trail["TrailARN"])
        except ClientError:
            status = {}
        resources.append(
            ResourceConfig(
                resource_type="aws_cloudtrail",
                name=name,
                config={
                    "is_multi_region_trail": trail.get("IsMultiRegionTrail"),
                    "log_file_validation_enabled": trail.get("LogFileValidationEnabled"),
                    "kms_key_id": trail.get("KmsKeyId"),
                    "cloud_watch_logs_log_group_arn": trail.get("CloudWatchLogsLogGroupArn"),
                    "is_logging": status.get("IsLogging"),
                },
                source="live_api",
            )
        )
    return resources


def _pull_config_recorder(session: boto3.Session) -> list[ResourceConfig]:
    """Account-level: AWS Config recorder status. Always emitted, even
    when no recorder exists -- CIS-3.5's finding either way."""
    cfg = session.client("config")
    recorders = cfg.describe_configuration_recorders().get("ConfigurationRecorders", [])

    if not recorders:
        return [
            ResourceConfig(
                resource_type="aws_config_configuration_recorder",
                name="no-recorder-configured",
                config={"recorder_exists": False},
                source="live_api",
            )
        ]

    statuses = {
        s["name"]: s
        for s in cfg.describe_configuration_recorder_status().get("ConfigurationRecordersStatus", [])
    }
    return [
        ResourceConfig(
            resource_type="aws_config_configuration_recorder",
            name=r["name"],
            config={
                "recording_group": r.get("recordingGroup"),
                "recording": statuses.get(r["name"], {}).get("recording"),
            },
            source="live_api",
        )
        for r in recorders
    ]


def _pull_kms_keys(session: boto3.Session) -> list[ResourceConfig]:
    kms = session.client("kms")
    resources = []
    for key in kms.list_keys().get("Keys", []):
        key_id = key["KeyId"]
        try:
            meta = kms.describe_key(KeyId=key_id)["KeyMetadata"]
        except ClientError:
            continue
        if meta.get("KeyManager") != "CUSTOMER":
            continue  # rotation status is only meaningful for customer-managed keys

        try:
            rotation = kms.get_key_rotation_status(KeyId=key_id).get("KeyRotationEnabled")
        except ClientError:
            rotation = None

        resources.append(
            ResourceConfig(
                resource_type="aws_kms_key",
                name=key_id,
                config={
                    "enabled": meta.get("Enabled"),
                    "key_state": meta.get("KeyState"),
                    "rotation_enabled": rotation,
                },
                source="live_api",
            )
        )
    return resources


def _pull_ec2_instances(session: boto3.Session) -> list[ResourceConfig]:
    ec2 = session.client("ec2")
    resources = []
    for reservation in ec2.describe_instances().get("Reservations", []):
        for inst in reservation.get("Instances", []):
            if inst.get("State", {}).get("Name") == "terminated":
                continue
            metadata_options = inst.get("MetadataOptions", {})
            resources.append(
                ResourceConfig(
                    resource_type="aws_instance",
                    name=inst["InstanceId"],
                    config={
                        "public_ip_address": inst.get("PublicIpAddress"),
                        "http_tokens": metadata_options.get("HttpTokens"),  # "required" = IMDSv2 enforced
                        "iam_instance_profile": bool(inst.get("IamInstanceProfile")),
                    },
                    source="live_api",
                )
            )
    return resources


def _pull_secrets_manager_secrets(session: boto3.Session) -> list[ResourceConfig]:
    sm = session.client("secretsmanager")
    resources = []
    for secret in sm.list_secrets().get("SecretList", []):
        resources.append(
            ResourceConfig(
                resource_type="aws_secretsmanager_secret",
                name=secret["Name"],
                config={
                    "rotation_enabled": secret.get("RotationEnabled", False),
                    "kms_key_id": secret.get("KmsKeyId"),
                },
                source="live_api",
            )
        )
    return resources


def _pull_dynamodb_tables(session: boto3.Session) -> list[ResourceConfig]:
    ddb = session.client("dynamodb")
    resources = []
    for table_name in ddb.list_tables().get("TableNames", []):
        table = ddb.describe_table(TableName=table_name)["Table"]

        try:
            backups = ddb.describe_continuous_backups(TableName=table_name)
            pitr_status = backups["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"][
                "PointInTimeRecoveryStatus"
            ]
        except ClientError:
            pitr_status = None

        resources.append(
            ResourceConfig(
                resource_type="aws_dynamodb_table",
                name=table_name,
                config={
                    "sse_status": table.get("SSEDescription", {}).get("Status"),
                    "point_in_time_recovery_status": pitr_status,
                },
                source="live_api",
            )
        )
    return resources


def _pull_cloudwatch_monitoring(session: boto3.Session) -> list[ResourceConfig]:
    """Account-level summary for CIS-4.x (log metric filter + alarm
    checks): rather than one pull per specific alarm type, surfaces every
    configured alarm and log metric filter pattern as one resource and
    lets the reasoning agent judge whether each required alarm type
    (root usage, unauthorized API calls, etc.) is covered -- structurally
    the same "insufficient info if absent" pattern as the other
    account-level checks, just evaluated once instead of per-control."""
    cw = session.client("cloudwatch")
    logs = session.client("logs")

    alarms = [
        {"name": a["AlarmName"], "metric_name": a.get("MetricName"), "namespace": a.get("Namespace")}
        for a in cw.describe_alarms().get("MetricAlarms", [])
    ]

    metric_filters = []
    for log_group in logs.describe_log_groups().get("logGroups", []):
        try:
            filters = logs.describe_metric_filters(logGroupName=log_group["logGroupName"]).get(
                "metricFilters", []
            )
        except ClientError:
            continue
        metric_filters.extend(
            {"log_group": log_group["logGroupName"], "filter_pattern": f.get("filterPattern")}
            for f in filters
        )

    return [
        ResourceConfig(
            resource_type="aws_cloudwatch_metric_alarm",
            name="account-alarms-and-metric-filters",
            config={"alarms": alarms, "metric_filters": metric_filters},
            source="live_api",
        )
    ]


def pull_all() -> list[ResourceConfig]:
    """Deterministic, fixed enumeration -- every listed pull runs every
    time, guaranteeing coverage rather than leaving discovery up to model
    judgment. Extend this list (and RELEVANT_RESOURCE_TYPES in
    terraform_adapter.py) as more services get their own knowledge-base
    controls; see app/knowledge_base/ for what's currently covered."""
    session = _session()
    return (
        _pull_s3_buckets(session)
        + _pull_ebs_volumes(session)
        + _pull_security_groups(session)
        + _pull_network_acls(session)
        + _pull_vpc_flow_logs(session)
        + _pull_rds_instances(session)
        + _pull_iam_roles(session)
        + _pull_iam_users(session)
        + _pull_iam_account_settings(session)
        + _pull_cloudtrail_trails(session)
        + _pull_config_recorder(session)
        + _pull_kms_keys(session)
        + _pull_ec2_instances(session)
        + _pull_secrets_manager_secrets(session)
        + _pull_dynamodb_tables(session)
        + _pull_cloudwatch_monitoring(session)
    )


if __name__ == "__main__":
    for r in pull_all():
        print(f"{r.resource_type}: {r.name}")
