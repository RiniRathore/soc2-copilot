## CIS-1.3
Ensure no 'root' user account access key exists. The AWS account root user
should not have long-lived access keys at all; any access key belonging
to the root user is a violation of this control.

## CIS-1.4
Ensure multi-factor authentication (MFA) is enabled for the 'root' user
account. A root user configured without MFA is a violation of this
control.

## CIS-1.6
Eliminate use of the 'root' user for administrative and daily tasks. The
root account should be reserved for a small number of account-management
tasks that require it; evidence of routine root-user activity (rather
than IAM users/roles) is a violation of this control -- this generally
requires activity/log data alongside account config, not account config
alone.

## CIS-1.7
Ensure IAM password policy requires a minimum length of 14 characters or
greater. An account password policy with no minimum length or a minimum
length below 14 is a violation of this control.

## CIS-1.8
Ensure IAM password policy prevents password reuse (remembers at least the
last 24 passwords). A password policy without password-reuse prevention
configured is a violation of this control.

## CIS-1.9
Ensure MFA is enabled for all IAM users that have a console password. An
IAM user with console access enabled but no MFA device registered is a
violation of this control.

## CIS-1.10
Ensure there is only one active access key for any single IAM user. An
IAM user with more than one active (non-disabled) access key is a
violation of this control.

## CIS-1.11
Ensure access keys are rotated every 90 days or less. An access key with
a creation or last-rotation date older than 90 days is a violation of
this control.

## CIS-1.12
Ensure credentials unused for 45 days or more are disabled. An IAM user
or access key with no activity for 45+ days that remains enabled is a
violation of this control.

## CIS-1.13
Ensure IAM policies that allow full "*:*" administrative privileges are
not created or attached. An IAM policy with an Allow statement granting
Action "*" and Resource "*" is a violation of this control.

## CIS-1.14
Ensure a support role has been created to manage incidents with AWS
Support. An account with no IAM role granting the AWSSupportAccess
managed policy is a violation of this control.

## CIS-1.15
Ensure IAM instance roles are used for AWS API access from within EC2
instances, rather than long-lived credentials embedded in instance
config, user-data, or application code. An EC2 instance with no attached
IAM instance profile, where the application is known to call AWS APIs, is
a violation of this control.

## CIS-1.16
Ensure IAM policies are attached only to groups or roles, and that
policies avoid wildcard ("*") actions or resources where a scoped set of
permissions would suffice. Overly permissive policies violate the
principle of least privilege.

## CIS-1.18
Ensure IAM Access Analyzer is enabled for all regions. A region/account
with no active IAM Access Analyzer is a violation of this control.

## CIS-2.1.1
Ensure S3 buckets employ encryption-at-rest. S3 buckets should have
either SSE-S3 or SSE-KMS encryption enabled by default so that objects
written to the bucket are encrypted without depending on the uploading
client to set it.

## CIS-2.1.2
Ensure S3 bucket policy denies HTTP (non-TLS) requests. A bucket policy
without an explicit Deny statement for requests where
"aws:SecureTransport" is false is a violation of this control.

## CIS-2.1.3
Ensure MFA delete is enabled on S3 buckets that hold sensitive or
business-critical data. A bucket with versioning enabled but MFA delete
not enabled is a violation of this control.

## CIS-2.1.5
Ensure S3 buckets are configured to block public access at the account
and bucket level. Bucket ACLs or policies that grant "AllUsers" or
"AuthenticatedUsers" read or write access expose data to the public
internet and violate this benchmark item.

## CIS-2.2.1
Ensure EBS volume encryption is enabled by default for the region. An
EBS volume created without encryption enabled is a violation of this
control.

## CIS-2.3.1
Ensure RDS database instances are not publicly accessible. An RDS
instance with "publicly_accessible" (or equivalent) set to true is a
violation of this control.

## CIS-2.3.2
Ensure RDS database instances have encryption at rest enabled. An RDS
instance created without storage encryption enabled is a violation of
this control.

## CIS-3.1
Ensure CloudTrail is enabled in all regions, with a multi-region trail
covering management events. An account with no multi-region CloudTrail
trail, or a trail that is not logging, is a violation of this control.

## CIS-3.2
Ensure CloudTrail log file validation is enabled. A trail configured
without log file validation is a violation of this control.

## CIS-3.3
Ensure CloudTrail logs are encrypted at rest using KMS. A trail whose
target S3 bucket/logs are not encrypted with a KMS key is a violation of
this control.

## CIS-3.4
Ensure CloudTrail trails are integrated with CloudWatch Logs. A trail with
no CloudWatch Logs log group configured is a violation of this control.

## CIS-3.5
Ensure AWS Config is enabled in all regions. A region with no active
AWS Config recorder is a violation of this control.

## CIS-3.6
Ensure S3 bucket access logging is enabled on the CloudTrail S3 bucket.
A CloudTrail target bucket with no server access logging configured is a
violation of this control.

## CIS-3.7
Ensure VPC flow logging is enabled in all VPCs. A VPC with no flow log
configured is a violation of this control.

## CIS-4.1
Ensure a log metric filter and alarm exist for unauthorized API calls.
An account with no CloudWatch alarm wired to a metric filter matching
"errorCode=*UnauthorizedAccess*" or "AccessDenied*" in CloudTrail logs is
a violation of this control.

## CIS-4.2
Ensure a log metric filter and alarm exist for Management Console sign-in
without MFA. An account with no alarm for non-MFA console logins is a
violation of this control.

## CIS-4.3
Ensure a log metric filter and alarm exist for usage of the 'root' user.
An account with no alarm firing on root-user API activity is a violation
of this control.

## CIS-4.4
Ensure a log metric filter and alarm exist for IAM policy changes. An
account with no alarm for IAM policy create/attach/detach/delete events
is a violation of this control.

## CIS-4.5
Ensure a log metric filter and alarm exist for CloudTrail configuration
changes. An account with no alarm for CloudTrail
create/update/delete/stop-logging events is a violation of this control.

## CIS-4.6
Ensure a log metric filter and alarm exist for AWS Management Console
authentication failures. An account with no alarm for repeated failed
console logins is a violation of this control.

## CIS-4.7
Ensure a log metric filter and alarm exist for disabling or scheduled
deletion of customer-managed KMS keys. An account with no alarm for KMS
key disable/schedule-deletion events is a violation of this control.

## CIS-4.8
Ensure a log metric filter and alarm exist for S3 bucket policy changes.
An account with no alarm for S3 PutBucketPolicy/PutBucketAcl events is a
violation of this control.

## CIS-4.9
Ensure a log metric filter and alarm exist for security group changes.
An account with no alarm for security-group rule create/modify/delete
events is a violation of this control.

## CIS-4.10
Ensure a log metric filter and alarm exist for changes to Network Access
Control Lists (NACLs). An account with no alarm for NACL
create/modify/delete/associate events is a violation of this control.

## CIS-4.11
Ensure a log metric filter and alarm exist for changes to network
gateways (internet gateways, NAT gateways). An account with no alarm for
gateway create/delete/attach/detach events is a violation of this
control.

## CIS-4.12
Ensure a log metric filter and alarm exist for route table changes. An
account with no alarm for route table create/modify/delete/associate
events is a violation of this control.

## CIS-4.13
Ensure a log metric filter and alarm exist for VPC changes. An account
with no alarm for VPC create/modify/delete events is a violation of this
control.

## CIS-5.1
Ensure no Network ACL allows unrestricted ingress from 0.0.0.0/0 to
administrative ports (22, 3389). A NACL rule with source 0.0.0.0/0
allowing traffic to these ports is a violation of this control.

## CIS-5.2
Ensure no security group allows unrestricted ingress access on port 22
(SSH). Security group rules with a source CIDR of 0.0.0.0/0 on port 22
significantly increase the risk of unauthorized access and brute-force
attacks.

## CIS-5.3
Ensure no security group allows unrestricted ingress from 0.0.0.0/0 to
any port used by a database engine (3306, 5432, 1433, 27017, etc). This
exposes data stores directly to the internet.

## CIS-5.4
Ensure the default security group of every VPC restricts all traffic. A
default security group with any ingress or egress rules beyond the
implicit deny is a violation of this control -- resources should use
purpose-built security groups instead of the default one.

## CIS-5.5
Ensure no security group allows unrestricted ingress access on port 3389
(RDP). Security group rules with a source CIDR of 0.0.0.0/0 on port 3389
significantly increase the risk of unauthorized access to Windows hosts.
