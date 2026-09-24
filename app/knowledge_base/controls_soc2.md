## CC1.1
The entity demonstrates a commitment to integrity and ethical values. This
is an organizational/cultural control (code of conduct, tone from the top,
disciplinary policies) evidenced by policy documents, training records, and
HR processes -- not something a Terraform state file or live resource
config can confirm or violate. Treat as insufficient information from infra
config alone.

## CC1.2
The board of directors demonstrates independence from management and
exercises oversight of the development and performance of internal control.
Evidenced by board composition, meeting minutes, and charter documents --
not observable in infrastructure configuration.

## CC1.3
Management establishes, with board oversight, structures, reporting lines,
and appropriate authorities and responsibilities in the pursuit of
objectives. This is an org-chart and governance-structure control,
evidenced by organizational documentation, not infrastructure config.

## CC1.4
The entity demonstrates a commitment to attract, develop, and retain
competent individuals in alignment with objectives. Evidenced by hiring,
training, and performance-management records -- not infrastructure config.

## CC1.5
The entity holds individuals accountable for their internal control
responsibilities in the pursuit of objectives. Evidenced by performance
reviews and disciplinary records tied to control responsibilities -- not
infrastructure config.

## CC2.1
The entity obtains or generates and uses relevant, quality information to
support the functioning of internal control. Evidenced by data-quality and
reporting processes -- not directly observable from a single resource's
infrastructure configuration.

## CC2.2
The entity internally communicates information, including objectives and
responsibilities for internal control, necessary to support the functioning
of internal control. Evidenced by internal communications, policy
distribution, and training records -- not infrastructure config.

## CC2.3
The entity communicates with external parties regarding matters affecting
the functioning of internal control. Evidenced by customer/vendor/regulator
communications and disclosure processes -- not infrastructure config.

## CC3.1
The entity specifies objectives with sufficient clarity to enable the
identification and assessment of risks relating to objectives. Evidenced
by documented business/security objectives -- not infrastructure config.

## CC3.2
The entity identifies risks to the achievement of its objectives across the
entity and analyzes risks as a basis for determining how the risks should
be managed. Evidenced by a risk register or risk-assessment process -- not
infrastructure config.

## CC3.3
The entity considers the potential for fraud in assessing risks to the
achievement of objectives. Evidenced by fraud-risk assessments -- not
infrastructure config.

## CC3.4
The entity identifies and assesses changes that could significantly impact
the system of internal control. Evidenced by change-impact assessments at
the organizational level -- not a single resource's infrastructure config
(contrast with CC8.1, which covers change management for individual
infrastructure/software changes).

## CC4.1
The entity selects, develops, and performs ongoing and/or separate
evaluations to ascertain whether the components of internal control are
present and functioning. Evidenced by internal audit or control-testing
programs -- not infrastructure config.

## CC4.2
The entity evaluates and communicates internal control deficiencies in a
timely manner to those parties responsible for taking corrective action,
including senior management and the board of directors, as appropriate.
Evidenced by deficiency-tracking and escalation records -- not
infrastructure config.

## CC5.1
The entity selects and develops control activities that contribute to the
mitigation of risks to the achievement of objectives to an acceptable
level. This is the general design of the control environment -- not a
single resource's config; see CC6/CC7 for the technical controls this
principle produces.

## CC5.2
The entity also selects and develops general control activities over
technology to support the achievement of objectives. Evidenced by IT
general control design (access provisioning process, change management
process, backup process) -- an organizational design control rather than
a single resource's config.

## CC5.3
The entity deploys control activities through policies that establish what
is expected and in procedures that put policies into action. Evidenced by
written policies and procedures -- not infrastructure config.

## CC6.1
The entity implements logical access security software, infrastructure, and
architectures over protected information assets to protect them from
security events to meet the entity's objectives. This includes restricting
access to data storage (buckets, volumes, databases) so that only
authorized identities can read or write to it. Storage resources that
permit public or anonymous read/write access without a documented business
justification are a violation of this control.

## CC6.2
Prior to issuing system credentials and granting system access, the entity
registers and authorizes new internal and external users whose access is
administered by the entity. IAM users, roles, or access grants created
without an associated approval/provisioning record, or credentials issued
before an authorization step, are a violation of this control -- though
confirming this fully typically requires an access-request/approval log
alongside the IAM configuration, not IAM config alone.

## CC6.3
The entity authorizes, modifies, or removes access to data, software,
functions, and other protected information assets based on roles,
responsibilities, or the system design. Identity and access management
roles or policies that grant broad, unscoped permissions (such as
wildcard "*" actions or "*" resources) rather than least-privilege,
task-specific permissions are a violation of this control.

## CC6.4
The entity restricts physical access to facilities and protected
information assets. For cloud infrastructure this is generally inherited
from the cloud provider's own physical/data-center controls rather than
something the customer's Terraform/resource config can violate --
insufficient information from infra config alone in most cases.

## CC6.5
The entity discontinues logical and physical protections over physical
assets only after the ability to read or recover data and software from
those assets has been diminished and is no longer required. Storage
resources (volumes, snapshots) that are deleted or decommissioned without
being securely wiped or without deletion-protection/backup verification
first are a violation of this control.

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

## CC6.8
The entity implements controls to prevent or detect and act upon the
introduction of unauthorized or malicious software. Compute resources
(instances, containers) deployed without endpoint protection, image
scanning, or from unverified/public sources without a vetting process are
a violation of this control.

## CC7.1
To meet its objectives, the entity uses detection and monitoring
procedures to identify (1) changes to configurations that result in the
introduction of new vulnerabilities, and (2) susceptibilities to newly
discovered vulnerabilities. Accounts or environments without vulnerability
scanning, configuration drift detection, or a CVE-monitoring feed enabled
are a violation of this control.

## CC7.2
The entity monitors system components for anomalies that are indicative
of malicious acts, natural disasters, and errors affecting the entity's
ability to meet its objectives, and evaluates monitoring output. Resources
with logging or monitoring explicitly disabled are a violation of this
control.

## CC7.3
The entity evaluates security events to determine whether they could or
have resulted in a failure of the entity to meet its objectives and, if
so, takes actions to prevent or address such failures. Evidenced by an
event-triage/evaluation process -- generally not observable from a single
resource's config alone, though the presence of enabled alerting (see
CC7.2) is a prerequisite.

## CC7.4
The entity responds to identified security incidents by executing a
defined incident-response program to understand, contain, remediate, and
communicate security incidents, as appropriate. Evidenced by a documented
incident-response plan and post-incident records -- not infrastructure
config.

## CC7.5
The entity identifies, develops, and implements activities to recover
from identified security incidents. Evidenced by recovery/backup testing
and post-incident remediation records -- resource-level backup/snapshot
configuration is a relevant but partial signal; the control as a whole is
not fully observable from infra config alone.

## CC8.1
The entity authorizes, designs, develops or acquires, configures,
documents, tests, approves, and implements changes to infrastructure,
data, software, and procedures to meet its objectives. Infrastructure
changes deployed without evidence of review/approval (e.g. resources
created or modified outside of a tracked infrastructure-as-code pipeline,
or without a corresponding change record) are a violation of this control
-- confirming this generally requires change-management/CI records
alongside the resource config, not the resource config alone.

## CC9.1
The entity identifies, selects, and develops risk mitigation activities
for risks arising from potential business disruptions. Evidenced by a
business-continuity/disaster-recovery plan -- resource-level redundancy
(e.g. multi-AZ, backups) is a relevant but partial signal; the control as
a whole is not fully observable from infra config alone.

## CC9.2
The entity assesses and manages risks associated with vendors and business
partners. Evidenced by vendor risk assessments and contracts -- not
infrastructure config.
