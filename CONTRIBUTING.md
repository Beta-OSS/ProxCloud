# Contributing to ProxCloud

Thanks for your interest in contributing to ProxCloud!

ProxCloud is an open-source project focused on making it easier to deploy and access isolated virtual machines on Proxmox VE. Contributions of all kinds are welcome, from bug fixes and documentation improvements to new features and architectural ideas.

## Before You Start

ProxCloud is currently in **early development**, so the architecture and APIs may change as the project develops.

Before working on a significant feature, please consider opening an issue to discuss the proposed change. This helps avoid duplicated work and gives us an opportunity to agree on the approach before substantial development begins.

For small fixes, documentation changes, tests, and similar improvements, feel free to open a pull request directly.

---

## Ways to Contribute

There are many ways to contribute beyond writing code.

### Report Bugs

If you encounter a bug, please open an issue and include:

* A clear description of the problem
* Steps to reproduce it
* Expected behaviour
* Actual behaviour
* Relevant error messages or logs
* ProxCloud version or commit
* Proxmox VE version
* Relevant environment information

Please remove passwords, API tokens, private addresses, or other sensitive information from logs before posting them.

### Suggest Features

Feature requests are welcome.

When proposing a feature, remember that ProxCloud is a user-based portal designed for a non-technical audience; try to describe:

1. The problem you are trying to solve
2. Who would benefit from the feature
3. How you expect it to work

ProxCloud is intentionally starting with a relatively narrow scope, so proposals should be considered in the context of the project's goal of providing simple, controlled access to virtual workstations.

### Improve Documentation

Documentation improvements are particularly valuable for an infrastructure project.

Examples include:

* Installation instructions
* Configuration guides
* Proxmox template setup
* Development documentation
* Architecture documentation
* Troubleshooting guides
* Examples
* Fixing unclear or outdated documentation

### Contribute Code

Code contributions can include:

* Bug fixes
* Tests
* Proxmox API integration
* VM provisioning
* Authentication and authorization
* Frontend development
* Database improvements
* Security improvements
* Deployment tooling
* Performance improvements
* Refactoring code for newer library versions

---

## Development Setup

### Requirements

The development environment currently requires:

* Python
* PostgreSQL
* A Proxmox VE environment
* A Proxmox VM template
* Git

If you are working on Windows, Docker Desktop is required for development.

Additional requirements may be introduced as the project develops.

### Clone the Repository

```bash
git clone https://github.com/<your-username>/proxcloud.git
cd proxcloud
```

Configure the required environment variables using the project's development configuration.

> Detailed development setup instructions will be expanded as the project approaches its first stable release.

---

## Branches

Please create a separate branch for your work rather than committing directly to the default branch.

For example:

```text
feature/template-management
fix/vm-provisioning
docs/installation-guide
test/proxmox-client
```

Keep branches focused on a single change where possible.

---

## Commits

Please aim for clear, descriptive commits such as:

```text
Add Proxmox template deployment service
Fix VM provisioning status handling
Add validation for RDP connection details
```

Rather than:

```text
fix stuff
changes
update
more work
```

There is no requirement to follow a strict commit-message convention at this stage, but commits should make the history understandable to someone unfamiliar with the change.

---

## Pull Requests

Before opening a pull request, please make sure that:

* The project builds and runs successfully
* Relevant tests pass
* New functionality includes appropriate tests where practical
* Documentation has been updated if necessary
* No credentials or secrets have been committed
* The pull request addresses a single logical change where possible

A pull request should explain:

* **What changed**
* **Why it changed**
* **How it was implemented**
* **How it was tested**

For example:

```markdown
## What changed

Adds support for deploying VMs from configured Proxmox templates.

## Why

Users need a way to provision a workstation without accessing
the Proxmox interface directly.

## Testing

Tested against Proxmox VE X.X using a Windows VM template.
Verified that the VM is cloned, started, and becomes available
for remote access.
```

---

## Testing

ProxCloud interacts directly with virtualization infrastructure, so changes involving VM provisioning should be tested carefully.

Where possible:

* Test against a dedicated development Proxmox environment
* Avoid testing destructive operations against production VMs
* Test failure conditions as well as successful provisioning
* Add automated tests for logic that does not require a live Proxmox environment

Tests should not depend on private infrastructure or credentials.

---

## Security

Please **do not publicly disclose security vulnerabilities through GitHub issues**.

If you discover a security vulnerability, please report it privately using the process described in [`SECURITY.md`](SECURITY.md).

Security-related contributions are especially welcome, including improvements to:

* Authentication
* Authorization
* Proxmox API permissions
* Credential handling
* VM isolation
* Network security
* Audit logging
* Session management
* Input validation

---

## Sensitive Information

ProxCloud is intended to be an open-source project.

Do not commit:

* Passwords
* API tokens
* Private keys
* Certificates containing private material
* Internal IP addresses that should not be public
* Personal information
* Production configuration
* Investigation data
* Proprietary or confidential material

Use environment variables or local configuration files for secrets.

If you are unsure whether something can be published, **do not commit it**. Ask first.

---

## Architecture Changes

ProxCloud is intended to grow beyond its initial VM deployment functionality, but architectural changes should be approached carefully.

For significant changes, please open an issue or discussion before implementation.

Examples include:

* Changing the database architecture
* Introducing a new backend service
* Replacing the Proxmox integration layer
* Changing the authentication model
* Adding a job/queue system
* Supporting additional hypervisors
* Changing how VMs are provisioned
* Introducing a new frontend framework

The goal is to keep the system modular without introducing unnecessary complexity.

---

## Code Style

Follow the existing conventions in the project.

In particular:

* Prefer clear and readable code over clever implementations
* Keep functions and classes focused
* Avoid unnecessary abstractions
* Add comments where the reasoning behind code is not obvious
* Keep configuration separate from application logic
* Avoid hard-coding infrastructure-specific values
* Use type hints where appropriate
* Use self-descriptive variable/function names

If an existing part of the codebase does something differently from these guidelines, follow the existing pattern unless you are intentionally refactoring it.

---

## Documentation

If a change affects how users install, configure, deploy, or use ProxCloud, update the relevant documentation as part of the same pull request.

Documentation is considered part of the feature, not an optional follow-up.

---

## Community

Please be respectful and constructive when participating in the project.

Contributors are expected to:

* Be welcoming to newcomers
* Assume good intentions
* Provide constructive feedback
* Focus criticism on ideas and implementations rather than individuals
* Keep discussions relevant to the project

Different approaches and opinions are expected in an open-source project. Technical disagreement is healthy when handled constructively.

---

## Licensing

By contributing to ProxCloud, you agree that your contributions may be distributed under the project's license.

ProxCloud is currently licensed under the **Apache License 2.0**.

Please make sure that you have the right to contribute any code or material that you submit to the project.

Do not contribute code copied from proprietary or incompatible sources.

---

## AI-Assisted Contributions

AI-assisted development is permitted and can be useful for contributing to ProxCloud.

Contributors should:

- Review and understand AI-generated code before submitting it
- Test AI-generated code appropriately
- Ensure that generated code does not introduce security vulnerabilities or inappropriate dependencies
- Ensure that the contributor has the right to submit the resulting code under the project's license
- Disclose substantial AI assistance in the pull request

For substantial AI-assisted contributions, briefly describe how AI was used and which parts of the contribution were generated or significantly assisted by AI.

Where known, contributors are encouraged to identify specific sections of code that were substantially generated or modified with AI assistance. This is particularly useful for security-sensitive, infrastructure, authentication, authorization, or other complex parts of the codebase, where additional human review may be appropriate.

AI-assisted code may be introduced or modified further after its initial generation, so contributors are not expected to maintain a complete record of every AI interaction. The purpose of disclosure is to provide useful context for reviewers rather than to track individual prompts or tools.

Contributors are responsible for the code they submit regardless of whether it was written manually or generated with AI.

---

## Getting Started

If you're looking for a place to start, look for issues labelled:

* `good first issue`
* `help wanted`
* `documentation`
* `testing`

If you have an idea that isn't covered by an existing issue, opening a discussion or issue is a good place to start.

**Thank you for helping make ProxCloud better!**
