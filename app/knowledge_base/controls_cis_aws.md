## CIS-2.1.1
Ensure S3 buckets employ encryption-at-rest. S3 buckets should have
either SSE-S3 or SSE-KMS encryption enabled by default so that objects
written to the bucket are encrypted without depending on the uploading
client to set it.

## CIS-2.1.5
Ensure S3 buckets are configured to block public access at the account
and bucket level. Bucket ACLs or policies that grant "AllUsers" or
"AuthenticatedUsers" read or write access expose data to the public
internet and violate this benchmark item.

## CIS-4.1
Ensure no security group allows unrestricted ingress access on port 22
(SSH). Security group rules with a source CIDR of 0.0.0.0/0 on port 22
significantly increase the risk of unauthorized access and brute-force
attacks.

## CIS-4.3
Ensure no security group allows unrestricted ingress from 0.0.0.0/0 to
any port used by a database engine (3306, 5432, 1433, 27017, etc). This
exposes data stores directly to the internet.

## CIS-1.16
Ensure IAM policies are attached only to groups or roles, and that
policies avoid wildcard ("*") actions or resources where a scoped set of
permissions would suffice. Overly permissive policies violate the
principle of least privilege.
