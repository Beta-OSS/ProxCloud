# ProxCloud

*Self-service virtual machine deployment purpose-built for Proxmox VE.*

ProxCloud is an open-source web platform for deploying isolated virtual machines from preconfigured templates and providing users with remote access to those machines through RDP.

The project puts a simple web interface between users and the underlying Proxmox infrastructure, allowing users to provision and access virtual machines without requiring direct access to Proxmox itself.

## The ProxCloud Dashboard

The dashboard is the central interface for users. It provides a single place to view their current virtual machines and access the workflow for creating new environments.

<p align="center">
  <img
    width="1220"
    height="548"
    alt="ProxCloud main dashboard"
    src="https://github.com/user-attachments/assets/e0a64f69-c9a5-4e53-addd-275b0c1b8850"
  />
</p>

<p align="center">
  <em>The ProxCloud user dashboard — the central interface for managing and accessing virtual environments.</em>
</p>

From the dashboard, users can see the environments assigned to them and begin the process of creating a new VM from an approved template.

The underlying Proxmox infrastructure remains hidden from the end user. ProxCloud provides the application layer through which users interact with their virtual environments.

> [!IMPORTANT]
> **Status:** Early development.
>
> ProxCloud currently focuses on establishing the architecture and workflow for template-based VM deployment and remote access. Some functionality shown or described in the interface is still under active development.

## Quick Start

ProxCloud is currently intended for self-hosted deployments.

### Requirements

- Proxmox VE
- Docker
- Python 3.13+
- A Proxmox API token

### Installation

#### 1. Clone the repository

```bash
git clone https://github.com/beta-oss/proxcloud.git
cd proxcloud
```

#### 2. Configure the environment

Copy the example environment configuration:

```bash
cp .env.example .env
```

Configure the Proxmox API connection and database settings:

```env
PROXMOX_HOST=proxmox.example.com
PROXMOX_NODE=pve01
PROXMOX_TOKEN_ID=...
PROXMOX_TOKEN_SECRET=...

DATABASE_URL=...
DATABASE_USER=...
DATABASE_PASS=...
```

#### 3. Start ProxCloud

```bash
docker compose up -d
```

#### 3.5. Create an administrator

When you first run ProxCloud, you will have to make an administrato account via the cli:

```bash
docker compose exec portal python -m app.cli create-admin \
  --username admin \
  --email you@example.com
```

You will then be prompted for a password.

#### 4. Open the web interface

Navigate to the ProxCloud web interface and sign in.

From there, administrators can configure available VM templates and users can access the self-service VM workflow.

Detailed deployment instructions and usage documentation will be expanded as the project moves toward its first stable release.

## Why ProxCloud?

Managing virtual machines directly through a hypervisor interface is powerful, but it can be unnecessarily complex for users who simply need a temporary or isolated computing environment.

ProxCloud was inspired by the need to provide investigators with dedicated, isolated workstations while maintaining accountability over the environments in which investigation-related work is performed.

The platform is designed around the idea that actions within an investigation environment should be attributable to a specific user and recorded for auditing, supporting organisational accountability, archival, and chain-of-custody processes.

ProxCloud provides an Azure-inspired self-service workflow:

```text
User
  │
  │ Web browser
  ▼
ProxCloud
  │
  │ Proxmox API
  ▼
Proxmox VE
  │
  ▼
Approved VM Template
  │
  ▼
New Virtual Machine
  │
  │ RDP
  ▼
User's Desktop
```

The goal is to make the process as simple as:

**Choose a template → Deploy a VM → Connect**

while keeping the underlying virtualization infrastructure under administrative control.

## User Workflow

The primary user workflow is centred around the dashboard.

### 1. View current VMs

Users can see the virtual machines currently assigned to them from the main dashboard.

<p align="center">
  <img
    width="1220"
    height="548"
    alt="ProxCloud main dashboard"
    src="https://github.com/user-attachments/assets/e0a64f69-c9a5-4e53-addd-275b0c1b8850"
  />
</p>

### 2. Choose a VM template

Users can select from VM templates that have been approved by an administrator.

<p align="center">
  <img
    width="1220"
    height="548"
    alt="ProxCloud VM template selection"
    src="https://github.com/user-attachments/assets/386592f8-5e24-42ab-88bd-23794052051c"
  />
</p>

Each template provides the base environment from which a user's VM can be provisioned.

### 3. Provision and access the VM

Once deployed, the resulting VM becomes associated with the user. The intended workflow will allow the user to connect to the environment remotely through a dedicated RDP connection.

> VM provisioning and remote access are currently under active development.

## Administration

ProxCloud also provides an administrative interface for managing the platform.

### VM Templates

Administrators can discover VM templates from Proxmox and control which templates are available for user deployment.

<p align="center">
  <img
    width="1219"
    height="547"
    alt="ProxCloud administrator VM template management"
    src="https://github.com/user-attachments/assets/b1d5a0f0-285c-4d4f-bea4-71594d73196b"
  />
</p>

Templates discovered from Proxmox are not automatically made available to users. Administrative approval provides a deliberate boundary between infrastructure discovery and user-facing provisioning.

### User Management

Administrators can manage user accounts through the administrative interface.

<p align="center">
  <img
    width="2437"
    height="1101"
    alt="ProxCloud administrator user management"
    src="https://github.com/user-attachments/assets/49ad61db-3ad4-45c6-ab2c-cb3c08f062ce"
  />
</p>

This provides the foundation for the user ownership and accountability model used throughout ProxCloud.

## Current Features

### Authentication and administration

ProxCloud currently provides:

* User accounts
* Secure account authentication
* Administrator controls
* VM template discovery
* VM template approval
* Proxmox API integration
* A user-facing dashboard
* A user-facing VM template catalogue

### VM deployment

The intended deployment workflow is:

* Select an approved VM template
* Create a new VM from the template
* Assign a VM ID
* Configure the VM
* Start the VM
* Track provisioning status
* Associate the VM with the requesting user
* Provide remote access

The underlying VM provisioning workflow is currently under development.

### Proxmox integration

ProxCloud communicates with Proxmox VE through its API rather than requiring users to interact with Proxmox directly.

This allows ProxCloud to provide a purpose-built application interface while leaving virtualization and infrastructure management to Proxmox.

## Technology

The project is currently built around:

* Python
* FastAPI
* Proxmox VE API
* PostgreSQL
* SQLAlchemy
* Alembic
* Docker
* RDP
* HTML/CSS/JavaScript
* HTMX

The architecture is intended to remain modular so that additional provisioning and infrastructure capabilities can be introduced without coupling the user interface directly to Proxmox.

## Requirements

A basic deployment requires:

* A Proxmox VE server
* A Proxmox API token
* Network connectivity between ProxCloud and Proxmox
* Docker
* Python 3.13+

ProxCloud is designed to run as an application layer in front of an existing Proxmox environment.

## VM Templates

ProxCloud expects VM templates to be prepared in Proxmox before they are made available for deployment.

ProxCloud discovers these templates through the Proxmox API and maintains a separate catalogue of templates within the application.

Administrators can then approve individual templates for user deployment.

This approach keeps operating-system configuration and base-image management within Proxmox while ProxCloud focuses on:

* Template discovery
* Administrative approval
* Self-service deployment
* User ownership
* Remote access
* Accountability

## Security

ProxCloud is intended to sit in front of the Proxmox management layer.

Users should not require direct access to the Proxmox API or web interface.

The application should therefore be deployed with appropriate network isolation and access controls.

Recommended deployment practices include:

* HTTPS for the ProxCloud web interface
* Restricting access to the Proxmox API
* Using a dedicated Proxmox API account/token
* Applying least-privilege permissions
* Isolating deployed VMs appropriately
* Avoiding exposure of the Proxmox management interface to untrusted networks
* Using secure credentials and environment configuration

Security features and hardening remain active areas of development.

## Roadmap

ProxCloud is deliberately starting with a narrow scope.

### Current

* [x] Proxmox API integration
* [x] VM discovery
* [x] User accounts
* [x] Production-ready account authentication
* [x] Administrator controls
* [x] VM template catalogue
* [x] VM template approval
* [x] User dashboard
* [ ] Template-based VM deployment
* [ ] VM lifecycle handling required for deployment
* [ ] Remote VM access
* [ ] Improved provisioning status
* [ ] VM archival to a NAS

### Planned

* [ ] Role-based access control
* [ ] User-owned VMs
* [ ] VM quotas
* [ ] Additional template configuration
* [ ] Cloud-init integration
* [ ] SSH key management
* [ ] VM snapshots
* [ ] Resource limits
* [ ] Multi-node Proxmox support
* [ ] Better networking configuration
* [ ] API/CLI access

The long-term goal is to evolve ProxCloud into a more complete self-service management layer for Proxmox, but the current project intentionally focuses on doing VM deployment and remote access well before expanding its scope.

## Project Status

ProxCloud is currently an early-stage open-source project.

The primary goal of the current development phase is to establish a reliable self-service workflow:

**Template → VM → Provision → Connect**

The project is not intended to replace the Proxmox management interface. Instead, it provides a simplified application layer for users and organisations that need easily deployable virtual machines without requiring users to understand the underlying virtualization infrastructure.

## Contributing

Contributions, ideas, bug reports, and architectural feedback are welcome.

If you are interested in contributing, please see [CONTRIBUTING.md](CONTRIBUTING.md).

Some areas where contributions could be particularly useful include:

* Frontend development
* Deeper Proxmox API integration
* VM provisioning
* Role-based authentication and authorization
* Testing
* Documentation
* Infrastructure and deployment
* Additional ideas

## License

ProxCloud is released under the Apache License 2.0.

See `LICENSE` for the full license text and license terms.

## Disclaimer

ProxCloud is an independent open-source project and is **not affiliated with or endorsed by Proxmox Server Solutions GmbH**.

Proxmox and Proxmox VE are trademarks of their respective owners.
