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
RELEVANT_RESOURCE_TYPES = {
    "aws_s3_bucket",
    "aws_s3_bucket_acl",
    "aws_s3_bucket_server_side_encryption_configuration",
    "aws_security_group",
    "aws_iam_role_policy",
    "aws_ebs_volume",
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
