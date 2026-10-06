# Security Policy

## Reporting a Vulnerability

Security vulnerabilities in ProxCloud should be reported privately.

**Please do not open a public GitHub issue for a suspected security vulnerability.**

Publicly disclosing a vulnerability before a fix is available may put users and deployments at risk.

### Preferred Reporting Method

If available, please use GitHub's private vulnerability reporting functionality to submit the vulnerability directly to the project maintainers.

When reporting a vulnerability, please provide as much of the following information as possible:

* A description of the vulnerability
* The affected component or functionality
* Steps required to reproduce the issue
* Proof-of-concept code or requests, where appropriate
* The potential security impact
* The versions or commits known to be affected
* Any suggested mitigations or fixes

Please do not include passwords, API tokens, private keys, personal information, or other sensitive data in a vulnerability report.

### Email Reporting

If private GitHub vulnerability reporting is unavailable, security issues may be reported to: **riley.grimwood@icloud.com**

Please use an appropriate subject such as:

```text
[SECURITY] ProxCloud vulnerability report
```

## What Happens After a Report?

The maintainers will attempt to:

1. Acknowledge receipt of the report.
2. Reproduce and verify the vulnerability.
3. Assess its severity and affected versions.
4. Determine whether existing users or deployments may be affected.
5. Develop and test an appropriate fix.
6. Release a patched version where appropriate.
7. Publish a security advisory when appropriate.

The timeline will depend on the severity and complexity of the vulnerability.

## Coordinated Disclosure

ProxCloud follows a coordinated disclosure approach.

Reporters are asked to allow reasonable time for the maintainers to investigate and address a vulnerability before publicly disclosing technical details.

Once a fix is available, the maintainers may publish a security advisory containing relevant information about the vulnerability, affected versions, and available remediation.

The timing and level of detail of public disclosure may vary depending on the severity of the vulnerability and the availability of a fix.

## Security-Sensitive Areas

Because ProxCloud interacts with virtualization infrastructure, security issues involving the following areas are particularly important:

* Authentication and authorization
* User and role isolation
* VM ownership and access control
* Proxmox API credentials
* VM provisioning
* VM lifecycle operations
* Remote access and RDP configuration
* Network isolation
* Session management
* Audit logging
* Input validation
* Database access
* Administrative functionality

A vulnerability that allows a user to access another user's VM or perform privileged operations against the underlying Proxmox infrastructure should be treated as particularly serious.

## Supported Versions

ProxCloud is currently in early development.

During this period, security fixes will generally be applied to the current development version. Once a stable release is established, this section will document which versions receive security updates.

## Security Research

Security research against ProxCloud is welcome when performed responsibly.

Researchers should avoid:

* Accessing data belonging to other users
* Modifying or deleting infrastructure
* Disrupting services
* Obtaining or exposing credentials
* Performing actions against systems without authorization

Testing should be performed against infrastructure that you own or have explicit permission to test.

## Recognition

With the reporter's permission, security researchers who responsibly disclose vulnerabilities may be credited in the relevant security advisory or release notes.
