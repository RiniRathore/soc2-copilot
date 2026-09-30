"""
Parses a `.tfstate` JSON file into the shared normalized shape.

This adapter and cloud_api_adapter.py both output List[ResourceConfig] --
same shape, so retrieval/reasoning never need to know which one ran.
"""
import json
from pathlib import Path

from app.models import ResourceConfig

# Resource types this scanner knows how to interpret. Extend this list as
# you add more checks -- everything else in the state file is ignored.
# Grouped by the CIS/SOC2 area each maps to in app/knowledge_base/.
RELEVANT_RESOURCE_TYPES = {
    # Storage
    "aws_s3_bucket",
    "aws_s3_bucket_acl",
    "aws_s3_bucket_server_side_encryption_configuration",
    "aws_s3_bucket_policy",
    "aws_s3_bucket_versioning",
    "aws_s3_bucket_logging",
    "aws_ebs_volume",
    "aws_db_instance",  # RDS
    # Networking
    "aws_security_group",
    "aws_network_acl",
    "aws_flow_log",
    "aws_default_security_group",
    # IAM
    "aws_iam_role_policy",
    "aws_iam_policy",
    "aws_iam_user",
    "aws_iam_access_key",
    "aws_iam_account_password_policy",
    # Logging / monitoring
    "aws_cloudtrail",
    "aws_config_configuration_recorder",
    "aws_cloudwatch_metric_alarm",
    # Encryption
    "aws_kms_key",
}


def load_terraform_state(path: str | Path) -> list[ResourceConfig]:
    raw = json.loads(Path(path).read_text())
    resources: list[ResourceConfig] = []

    for res in raw.get("resources", []):
        res_type = res.get("type")
        if res_type not in RELEVANT_RESOURCE_TYPES:
            continue

        for instance in res.get("instances", []):
            values = instance.get("attributes", {})
            resources.append(
                ResourceConfig(
                    resource_type=res_type,
                    name=res.get("name", "unnamed"),
                    config=values,
                    source="terraform",
                )
            )

    return resources


if __name__ == "__main__":
    import sys

    found = load_terraform_state(sys.argv[1] if len(sys.argv) > 1 else "seed_data/sample.tfstate.json")
    for r in found:
        print(f"{r.resource_type}: {r.name}")
