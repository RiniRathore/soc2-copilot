## CC6.1
The entity implements logical access security software, infrastructure, and
architectures over protected information assets to protect them from
security events to meet the entity's objectives. This includes restricting
access to data storage (buckets, volumes, databases) so that only
authorized identities can read or write to it. Storage resources that
permit public or anonymous read/write access without a documented business
justification are a violation of this control.

## CC6.3
The entity authorizes, modifies, or removes access to data, software,
functions, and other protected information assets based on roles,
responsibilities, or the system design. Identity and access management
roles or policies that grant broad, unscoped permissions (such as
wildcard "*" actions or "*" resources) rather than least-privilege,
task-specific permissions are a violation of this control.

## CC6.6
The entity implements logical access security measures to protect against
threats from sources outside its system boundaries, including network
segmentation and restriction of inbound traffic. Network security groups
or firewall rules that allow unrestricted inbound access (0.0.0.0/0) on
sensitive ports (SSH, RDP, database ports) without compensating controls
are a violation of this control.

## CC6.7
The entity restricts the transmission, movement, and removal of
information to authorized users and processes, and protects it during
transmission, movement, or removal to meet the entity's objectives. Data
at rest that is not encrypted (e.g. unencrypted storage volumes, buckets,
or database instances) is a violation of this control.

## CC7.2
The entity monitors system components for anomalies that are indicative
of malicious acts, natural disasters, and errors affecting the entity's
ability to meet its objectives, and evaluates monitoring output. Resources
with logging or monitoring explicitly disabled are a violation of this
control.
