# ProxCloud

*Self-service virtual machine deployment purpose-built for Proxmox VE.*

[image goes here later]

ProxCloud is an open-source web platform for deploying isolated virtual machines from preconfigured templates and providing users with remote access to those machines through RDP.

The project is designed to put a simple web interface between users and the underlying Proxmox infrastructure, allowing them to provision and access a VM without requiring direct access to Proxmox itself.

> [!IMPORTANT]
> **Status:** Early development.
>
> ProxCloud currently focuses on template-based VM deployment and remote access. More advanced infrastructure management features are planned for future releases.

## Why ProxCloud?

Managing virtual machines directly through a hypervisor interface is powerful, but it can be unnecessarily complex for users who simply need a temporary or isolated computing environment.

ProxCloud was inspired by the need to provide investigators with dedicated, isolated workstations while maintaining accountability over the environments in which investigation-related work is performed. The platform is designed around the idea that actions within an investigation environment should be attributable to a specific user and recorded for auditing, supporting organisational accountability, archival, and chain-of-custody processes.

ProxCloud solves this problem with a simple Azure-inspired workflow:

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
VM Template
  │
  ▼
New Virtual Machine
  │
  │ RDP
  ▼
User's Desktop
```

A user can select an available VM template, deploy an instance, wait for provisioning to complete, and connect to the resulting environment remotely.

The underlying Proxmox infrastructure remains hidden from the end user, while ProxCloud provides the application layer through which users can provision and access virtual workstations.

## Current Features
### VM deployment

Deploy a new virtual machine from a preconfigured Proxmox template.

ProxCloud handles the basic lifecycle required to make the VM available to the user:

- Select a VM template
- Create a new VM from the template
- Assign a VM ID
- Configure the VM
- Start the VM
- Track provisioning status
- Display the resulting VM to the user
- Remote access through a dedicated .rdp file

Once a VM has been deployed, users can connect to it remotely using the provided .rdp file. VMs can additionally be configured to only allow access through the use of the .rdp file, providing a secure and accountable workstation.

### Proxmox integration

ProxCloud communicates with Proxmox VE through its API rather than requiring users to interact with Proxmox directly or get system administrators to configure an environment for them.

This allows the application to provide a purpose-built interface while leaving virtualization and infrastructure management to Proxmox.

## Technology

The project is currently built around:

- Python
- FastAPI
- Proxmox VE API
- PostgreSQL
- Docker
- RDP
- HTML/CSS/JavaScript frontend

The architecture is intended to remain modular so that additional provisioning and infrastructure capabilities can be introduced without coupling the user interface directly to Proxmox.


## Requirements

A basic deployment requires:

- A Proxmox VE server
- Access to a Proxmox API key and ID
- Network connectivity between ProxCloud and Proxmox
- Docker
- Python 3.13+

To create a Proxmox API access point:

## Installation

### 1. Clone the repository
```
git clone https://github.com/beta-oss/proxcloud.git
cd proxcloud
```

### 2. Configure the environment

Edit the example environment configuration to use your Proxmox API connection and database settings, and copy it into environment variables.
```
PROXMOX_HOST=proxmox.example.com
PROXMOX_NODE=pve01
PROXMOX_TOKEN_ID=...
PROXMOX_TOKEN_SECRET=...

DATABASE_URL=...
DATABASE_USER=...
DATABASE_PASS=...
```
`cp .env.example .env`

### 3. Create an admin user

`docker compose exec portal python -m app.cli create-admin --username admin --email you@example.com`
You will then be prompted for a password (12+ characters).

### 4. Start ProxCloud

`docker compose up -d`

### 5. Open the web interface

Navigate to the ProxCloud web interface and sign in.

From there, a configured VM template can be selected and deployed.

Detailed deployment instructions and usage documentation will be expanded as the project moves toward its first stable release.

## VM Templates

ProxCloud expects VM templates to be prepared in Proxmox before they are made available for deployment.

ProxCloud then uses these templates as the starting point for new virtual machines.

This approach keeps operating-system configuration and base-image management within Proxmox while ProxCloud focuses on self-service deployment and access.

## Security

ProxCloud is intended to sit in front of the Proxmox management layer.

Users should not require direct access to the Proxmox API or web interface.

The application should therefore be deployed with appropriate network isolation and access controls.

Recommended deployment practices include:

- HTTPS for the ProxCloud web interface
- Restricting access to the Proxmox API
- Using a dedicated Proxmox API account/token
- Applying least-privilege permissions
- Isolating deployed VMs appropriately
- Avoiding exposure of the Proxmox management interface to untrusted networks
- Using secure credentials and environment configuration

Security features are an active area of development.

## Roadmap

ProxCloud is deliberately starting with a narrow scope.

### Current

* [X] Proxmox API integration
* [X] VM discovery
* [X] User accounts
* [X] Production-ready account authentication
* [X] Administrator controls
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

The primary goal of the current development phase is to establish a reliable deployment workflow:

`Template → VM → Provision → Connect`

The project is not intended to replace the Proxmox management interface. Instead, it provides a simplified application layer for users and organisations who need access to easily deployable virtual machines without needing to understand the underlying virtualization infrastructure.

## Contributing

Contributions, ideas, bug reports, and architectural feedback are welcome. I am still learning a lot through this project, so collaboration and criticism are encouraged.

If you are interested in contributing, please see [CONTRIBUTING.md](CONTRIBUTING.md).

Some areas where contributions could be particularly useful include:

- Frontend development
- Deeper Proxmox API integration
- VM provisioning
- Role-based authentication and authorization
- Testing
- Documentation
- Infrastructure/deployment
- Additional ideas

## License

ProxCloud is released under the Apache License 2.0.

See `LICENSE` for the full license text and fair use.

## Disclaimer

ProxCloud is an independent open-source project and is **not affiliated** with or endorsed by Proxmox Server Solutions GmbH.

Proxmox and Proxmox VE are trademarks of their respective owners.
