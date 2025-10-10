# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a generic Ansible project for setting up and configuring Linux systems across multiple architectures and distributions. Originally designed for Raspberry Pi systems, it now supports x86_64, ARM64, and ARM32 architectures running Debian, Ubuntu, RHEL, CentOS, Fedora, and Arch Linux distributions. The project configures new systems with essential software, monitoring tools, and user accounts.

## Architecture

- **Main Playbook**: `main.yml` - Entry point that orchestrates role execution for new Linux systems
- **Inventory**: `inventory/hosts.yml` - Defines target hosts and groups (multiple example templates available)
- **Multi-Platform Support**: Automatic detection and configuration for different architectures and distributions
- **Roles Structure**: Modular roles in `./roles/` directory handle specific configuration aspects:
  - `common-pkg`: Cross-platform system updates and essential package installation
  - `docker`: Multi-distribution Docker and Docker Compose installation
  - `timezone`: NTP and timezone configuration
  - `users`: Generic user management role (replaces individual user-* roles)
  - `sshd_conf`: SSH daemon configuration
  - `rpi_exporter`: Raspberry Pi hardware metrics exporter (Pi-specific)
  - `node_exporter`: System metrics exporter (all platforms)
  - `rpi_reporter`: MQTT reporting service (primarily for ARM devices)
  - `monitoring_server`: Cross-platform monitoring infrastructure
  - `pihole`: Network-wide DNS ad blocker
  - `aaronmyatt.ohmyzsh_plbk`: External role for Oh My Zsh setup

## Supported Platforms

### Architectures
- **x86_64**: Intel/AMD 64-bit systems
- **aarch64**: ARM 64-bit systems (Raspberry Pi 4, ARM servers)
- **armv7l**: ARM 32-bit systems (Raspberry Pi 3 and older)

### Distributions
- **Debian Family**: Debian, Ubuntu, Raspbian (using apt package manager)
- **Red Hat Family**: RHEL, CentOS, Fedora, Rocky Linux (using yum/dnf)
- **Arch Family**: Arch Linux, Manjaro (using pacman)

## Common Commands

### Running the Main Playbook
```bash
ansible-playbook -i inventory/hosts.yml main.yml
```

### Target Specific Groups
```bash
# Configure all Raspberry Pi hosts
ansible-playbook -i inventory/hosts.yml main.yml --limit raspberry_pi

# Configure all K3s nodes (control + workers)
ansible-playbook -i inventory/hosts.yml main.yml --limit k3s

# Configure specific distribution family
ansible-playbook -i inventory/hosts.yml main.yml --limit debian_based
ansible-playbook -i inventory/hosts.yml main.yml --limit redhat_based

# Configure all VMs regardless of OS
ansible-playbook -i inventory/hosts.yml main.yml --limit vm_hardware

# Configure multiple groups
ansible-playbook -i inventory/hosts.yml main.yml --limit 'pihole:ntp'

### Check Mode (Dry Run)
```bash
ansible-playbook -i inventory/hosts.yml main.yml --check
```

### Syntax Validation
```bash
ansible-playbook -i inventory/hosts.yml main.yml --syntax-check
```

### Run Specific Roles
```bash
ansible-playbook -i inventory/hosts.yml main.yml --tags "docker,monitoring"
```

## Configuration

- **ansible.cfg**: Comprehensive Ansible configuration with inventory path, logging, and connection settings
- **Target Hosts**: Playbook targets `all` hosts with role-based conditional execution
- **Multi-Dimensional Inventory**: Hosts organized by OS family, purpose, and features for flexible targeting
- **Authentication**: Uses SSH key authentication with user-specific private keys
- **Privilege Escalation**: Configured for sudo with stored passwords

## Key Variables

- `ansible_user`: SSH connection user (typically "pi")
- `ansible_ssh_private_key_file`: Path to SSH private key
- `ansible_become_password`: Sudo password for privilege escalation (defined in group_vars/all.yml)
- `users_list`: Centralized user configuration with SSH keys and sudo access
- `software_versions`: Centralized version management for all software packages
- `mqtt_config`: Centralized MQTT broker configuration and credentials
- `paths`: Standardized installation paths and directories
- `repositories`: Centralized repository URLs and download sources

## Security Notes

- **Centralized credentials**: All passwords and secrets in `group_vars/all.yml` (TODO: encrypt with ansible-vault)
- **MQTT security**: Broker credentials centralized and should be vault-encrypted
- **SSH key-based authentication**: Preferred over password authentication
- **Privilege escalation**: Centralized sudo password management

## Role Structure

All roles follow Ansible best practices with:
- `meta/main.yml`: Role metadata and dependencies (ansible-lint compliant)
- `defaults/main.yml`: Default variables (lower precedence, proper naming with role prefix)
- `vars/main.yml`: Role-specific variables (higher precedence, proper naming with role prefix)
- `tasks/main.yml`: Main task definitions
- `handlers/main.yml`: Event handlers using proper FQCN modules
- `templates/`: Jinja2 templates for configuration files

## Quality Assurance

- ✅ **ansible-lint**: All roles pass production-level linting
- ✅ **Syntax validation**: Playbook syntax verified
- ✅ **FQCN compliance**: All modules use Fully Qualified Collection Names
- ✅ **Variable naming**: Role variables properly prefixed (e.g., `docker_*`, `rpi_exporter_*`)
- ✅ **Error handling**: Uses `failed_when` instead of `ignore_errors`
- ✅ **DRY compliance**: Generic templates eliminate code duplication
- ✅ **Centralized configuration**: All infrastructure settings in group_vars/all.yml

## User Management

The `users` role provides fully centralized user management through the `users_list` variable in `group_vars/all.yml`. Each user can have:

- **name**: Username to create/configure
- **groups**: Comma-separated list of groups (optional, uses defaults if not specified)
- **ssh_public_key**: SSH public key content (replaces template files)
- **sudo_access**: Boolean flag to grant NOPASSWD sudo access (optional, defaults to false)
- **sudoers_template**: Custom sudoers template (optional, uses generic template by default)

Example configuration:
```yaml
users_list:
  - name: jason
    groups: "adm,dialout,cdrom,sudo,audio,video,plugdev,games,users,input,render,netdev,gpio,i2c,spi,docker"
    ssh_public_key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB... jason@hostname"
    sudo_access: true

  - name: developer
    ssh_public_key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB... dev@hostname"
    # No sudo access, uses default groups
```

To add new users, simply add them to the `users_list` in `group_vars/all.yml` with their SSH public key. No template files needed!

## Centralized Configuration

All infrastructure configuration is centralized in `group_vars/all.yml` for easy management:

### Software Versions
```yaml
software_versions:
  prometheus: "2.44.0"
  grafana: "9.5.2"
  node_exporter: "1.9.1"
  rpi_exporter: "0.8.0"
```

### MQTT Configuration
```yaml
mqtt_config:
  host: "10.10.2.32"
  port: 1883
  username: "hass"
  password: "encrypted_password"  # Use ansible-vault
  discovery_prefix: "homeassistant"
  base_topic: "home/nodes"
```

### Installation Paths
```yaml
paths:
  bin_dir: "/usr/local/bin"
  data_dir: "/data"
  opt_dir: "/opt"
  config_dir: "/etc"
  systemd_dir: "/etc/systemd/system"
```

### Repository URLs
```yaml
repositories:
  prometheus:
    base_url: "https://github.com/prometheus/prometheus/releases/download"
    architecture: "linux-arm64"
```

**Benefits:**
- **Single source of truth** for all configuration
- **Easy version updates** across all roles
- **Environment-specific overrides** possible
- **Reduced role complexity** and duplication

## Recent Changes and Improvements

This project has undergone significant architectural improvements to enhance maintainability, security, and adherence to Ansible best practices:

### Centralized Configuration (Major Update)
- **Complete consolidation**: All infrastructure settings moved to `group_vars/all.yml`
- **Software version management**: Centralized version control for prometheus, grafana, node_exporter, rpi_exporter
- **MQTT configuration**: Unified MQTT broker settings, credentials, and topic configuration
- **Repository management**: Centralized download URLs and architecture specifications
- **Path standardization**: Consistent installation and configuration paths across all roles

### User Management Consolidation
- **Role consolidation**: Replaced 4 individual `user-*` roles with single generic `users` role
- **Template simplification**: Single generic `sudoers.j2` template replaces role-specific templates
- **SSH key centralization**: Moved SSH public keys from template files to `group_vars/all.yml`
- **Scalable architecture**: Add new users by simply updating `users_list` variable

### Production-Level Quality Assurance
- **ansible-lint compliance**: Resolved all lint violations for production readiness
- **FQCN adoption**: All modules use Fully Qualified Collection Names
- **Metadata standardization**: Proper Galaxy role metadata with MIT licensing
- **Error handling**: Replaced `ignore_errors` with proper `failed_when` conditions
- **Security preparation**: Credentials marked for ansible-vault encryption

### Code Quality Improvements
- **DRY principle**: Eliminated code duplication through centralized configuration
- **Variable consistency**: Role variables properly prefixed and standardized
- **Template optimization**: Generic templates reduce maintenance overhead
- **Documentation updates**: Comprehensive CLAUDE.md reflecting architectural changes

These improvements create a more maintainable, secure, and scalable Ansible infrastructure while preserving all existing functionality.

## Inventory Structure

The inventory uses a **multi-dimensional structure** where hosts belong to multiple groups simultaneously:

### Organization Dimensions

**1. OS Family Groups** (distribution-based):
- `debian_based` → `raspberry_pi`, `ubuntu_baremetal`, `ubuntu_vm`, `debian_baremetal`, `debian_vm`
- `redhat_based` → `centos_baremetal`, `centos_vm`, `fedora_baremetal`, `fedora_vm`
- `arch_based` → `arch_baremetal`, `arch_vm`

**2. Purpose Groups** (function-based):
- `ntp` - NTP servers
- `pihole` - Pi-hole DNS servers
- `klipper` - 3D printer hosts
- `zigbee` - Zigbee gateways
- `pikvm` - PiKVM systems
- `k3s` → `control`, `worker` - Kubernetes cluster nodes

**3. Feature Groups** (capability-based):
- `vm_hardware` - All virtual machines (aggregates all *_vm groups)
- `uctronics` - Hosts with Uctronics OLED displays

### Multi-Group Membership Example

Host `10.10.2.220` (Kube-Pi-CP01) belongs to:
- `debian_based` → `raspberry_pi` (OS/hardware)
- `k3s` → `control` (K3s control plane)
- `uctronics` (OLED display feature)

This enables precise role targeting:
```yaml
# Install on all Raspberry Pi hosts
when: "'raspberry_pi' in group_names"

# Install on all VMs
when: "'vm_hardware' in group_names"

# Install on hosts with Uctronics displays
when: "'uctronics' in group_names"
```

### Inventory Commands
```bash
# View complete inventory structure
ansible-inventory -i inventory/hosts.yml --graph

# View specific host's group memberships
ansible-inventory -i inventory/hosts.yml --host 10.10.2.220

# List hosts in specific group
ansible-inventory -i inventory/hosts.yml --graph k3s
```

## Templates

The `templates/` directory contains configuration file templates used by various roles.