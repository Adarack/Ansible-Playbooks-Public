# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of Ansible playbook projects for infrastructure automation and configuration management. Each subdirectory contains a self-contained Ansible project with its own playbooks, roles, inventory, and configuration.

**Current Projects:**
- **Linux-Setup**: Multi-platform Linux system configuration (primary reference template)
- **UpdateSystem**: System and Pi-hole update automation across all platforms
- **k3s-cluster**: K3s Kubernetes cluster deployment and management
- **wyoming-satellite**: Wyoming Satellite voice assistant setup for Home Assistant

**Repository Root Files:**
- `CLAUDE.md` - This file; repository-level guidance for AI assistance
- `README.md` - User-facing documentation with quick start
- `SECURITY.md` - Security policy and vulnerability reporting
- `PRE_COMMIT_CHECKLIST.md` - Detailed security checklist before commits
- `verify-security.sh` - Automated security verification script
- `.gitignore` - Repository-wide ignore patterns

## Repository Structure

```
ansible-wip/
├── CLAUDE.md                    # This file - repository-level guidance
├── Linux-Setup/                 # Multi-platform Linux system setup
│   ├── CLAUDE.md               # Project-specific documentation
│   ├── main.yml                # Main playbook entry point
│   ├── ansible.cfg             # Ansible configuration
│   ├── inventory/
│   │   └── hosts.yml          # Multi-dimensional inventory
│   ├── group_vars/
│   │   └── all.yml            # Centralized configuration
│   ├── roles/                  # Modular role directories
│   └── templates/              # Shared Jinja2 templates
└── UpdateSystem/                # System and Pi-hole updates
    ├── CLAUDE.md               # Project-specific documentation
    ├── main.yml                # Main update playbook
    ├── pihole_update_serial.yml # Serial Pi-hole updates
    ├── ansible.cfg             # Ansible configuration
    ├── inventory/
    │   └── hosts.yml          # Multi-dimensional inventory (shared structure)
    ├── group_vars/
    │   └── all.yml            # Centralized configuration
    └── roles/
        ├── system_update/      # Multi-distribution package updates
        ├── pihole_update/      # Pi-hole component updates
        └── pikvm_update/       # PiKVM read-only filesystem updates
```

## Standard Playbook Organization Pattern

All playbooks in this repository follow the Linux-Setup template structure:

### Required Files
- `main.yml` - Main playbook entry point
- `ansible.cfg` - Ansible configuration (inventory path, logging, connection settings)
- `inventory/hosts.yml` - Inventory definitions with groups and variables
- `inventory/hosts.yml.example` - **Sanitized example inventory (REQUIRED)**
- `group_vars/all.yml` - Centralized configuration (versions, credentials, paths, repos)
- `group_vars/all.yml.example` - **Sanitized example configuration (REQUIRED)**
- `.gitignore` - **Git ignore file to protect sensitive data (REQUIRED)**
- `CLAUDE.md` - Project-specific documentation

### Directory Structure
- `roles/` - Modular role directories with standard Ansible structure
- `templates/` - Shared Jinja2 templates (generic, reusable)
- `group_vars/` - Group-specific variables
- `host_vars/` - Host-specific variables (optional)

### Role Structure Standard
Each role follows Ansible best practices:
```
roles/role_name/
├── meta/main.yml          # Role metadata and dependencies
├── defaults/main.yml      # Default variables (lower precedence)
├── vars/main.yml          # Role variables (higher precedence)
├── tasks/main.yml         # Main task definitions
├── handlers/main.yml      # Event handlers
└── templates/             # Role-specific templates
```

## Centralized Configuration Pattern

**IMPORTANT**: All playbooks use centralized configuration in `group_vars/all.yml` to maintain a single source of truth:

### Configuration Categories

```yaml
# Role enablement - control which roles execute
role_enabled:
  role_name: true/false

# Software versions - centralized version management
software_versions:
  package_name: "version_number"

# Service configuration - MQTT, API endpoints, etc.
mqtt_config:
  host: "ip_address"
  port: 1883
  username: "user"
  password: "password"  # TODO: Use ansible-vault

# Installation paths - standardized directories
paths:
  bin_dir: "/usr/local/bin"
  data_dir: "/data"
  opt_dir: "/opt"
  config_dir: "/etc"
  systemd_dir: "/etc/systemd/system"

# Repository URLs - download sources
repositories:
  package_name:
    base_url: "https://github.com/..."
    architecture: "linux-arm64"

# Architecture mapping - multi-platform support
architecture_mapping:
  "x86_64":
    package_name: "linux-amd64"
  "aarch64":
    package_name: "linux-arm64"
```

## Quality Standards

All playbooks and roles MUST adhere to these standards:

### ✅ ansible-lint Compliance
- Production-level linting with zero warnings
- FQCN (Fully Qualified Collection Names) for all modules
  - Use `ansible.builtin.module_name` instead of `module_name`
  - Use `ansible.posix.authorized_key` instead of `authorized_key`
- Proper metadata in all `meta/main.yml` files

### ✅ Variable Naming Conventions
- Role variables prefixed with role name: `rolename_variable`
- Example: `docker_compose_version`, `rpi_exporter_port`
- Centralized infrastructure variables in `group_vars/all.yml`
- No hardcoded values in tasks (use variables)

### ✅ Error Handling
- Use `failed_when` instead of `ignore_errors`
- Proper task conditionals with `when` clauses
- Validate configuration files before deployment

### ✅ DRY Principle (Don't Repeat Yourself)
- Generic, reusable templates (avoid user-specific template files)
- Centralized configuration eliminates duplication
- Single generic role instead of multiple specific roles (e.g., one `users` role, not `user-jason`, `user-pi`, etc.)

### ✅ Security Best Practices
- **TODO marker for unencrypted credentials**: Mark all plaintext passwords with `# TODO: Use ansible-vault`
- SSH key-based authentication preferred
- Centralized credential management in `group_vars/all.yml`
- Future: Encrypt sensitive variables with `ansible-vault`

## Common Commands

### Running Playbooks
```bash
# Navigate to playbook directory first
cd Linux-Setup/

# Run main playbook
ansible-playbook -i inventory/hosts.yml main.yml

# Target specific groups
ansible-playbook -i inventory/hosts.yml main.yml --limit groupname

# Check mode (dry run)
ansible-playbook -i inventory/hosts.yml main.yml --check

# Run specific roles
ansible-playbook -i inventory/hosts.yml main.yml --tags "docker,monitoring"
```

### Validation and Quality Assurance
```bash
# Syntax validation
ansible-playbook -i inventory/hosts.yml main.yml --syntax-check

# Run ansible-lint
ansible-lint main.yml

# Lint specific role
ansible-lint roles/role_name/

# List hosts in inventory
ansible-inventory -i inventory/hosts.yml --list

# List specific group
ansible-inventory -i inventory/hosts.yml --graph groupname
```

### Security Verification
```bash
# Run automated security check (from repository root)
./verify-security.sh

# This checks for:
# - Hardcoded passwords
# - Vault password files
# - SSH private keys
# - Accidentally tracked sensitive files
# - Sensitive files staged for commit
```

### Variable Management
```bash
# Encrypt sensitive variables with ansible-vault
echo 'password123' | ansible-vault encrypt_string --stdin-name 'variable_name'

# Edit encrypted file
ansible-vault edit group_vars/all.yml

# Run playbook with vault
ansible-playbook -i inventory/hosts.yml main.yml --ask-vault-pass
```

## Creating New Playbooks

When creating a new playbook project, follow these steps:

### 1. Create Directory Structure
```bash
mkdir NewProject
cd NewProject
mkdir -p inventory group_vars roles templates
```

### 2. Copy Template Files
```bash
# Copy and customize from Linux-Setup
cp ../Linux-Setup/ansible.cfg .
cp ../Linux-Setup/.gitignore .
cp ../Linux-Setup/inventory/hosts.yml.example inventory/
cp ../Linux-Setup/group_vars/all.yml.example group_vars/

# Customize for your actual environment
cp inventory/hosts.yml.example inventory/hosts.yml
cp group_vars/all.yml.example group_vars/all.yml
# Edit hosts.yml and all.yml with your real values
```

### 3. Create Main Playbook
Create `main.yml` with standard structure:
```yaml
- name: Project Name and Purpose
  hosts: target_group
  gather_facts: true
  become: true
  tasks:
    - name: Task description
      ansible.builtin.import_role:
        name: role_name
      when: role_enabled.role_name | default(true)
```

### 4. Create CLAUDE.md
Document the project-specific architecture, roles, and commands based on the Linux-Setup/CLAUDE.md template.

### 5. Configure Centralized Variables
Edit `group_vars/all.yml` with:
- Role enablement flags
- Software versions
- Service configurations
- Installation paths
- Repository URLs

### 6. Create Sanitized Example Files (REQUIRED)
**IMPORTANT**: Always create and maintain sanitized example files:

```bash
# Copy and sanitize inventory
cp inventory/hosts.yml inventory/hosts.yml.example
# Edit to remove real IPs, use example IPs (10.x.x.x, 192.168.x.x)

# Copy and sanitize group_vars
cp group_vars/all.yml group_vars/all.yml.example
# Replace all passwords with "CHANGE_ME"
# Replace all real IPs with example values
# Replace all tokens/secrets with placeholders
```

**Maintenance Rule**: Whenever you modify `inventory/hosts.yml` or `group_vars/all.yml`, you **MUST** immediately update the corresponding `.example` files with sanitized versions.

### 7. Create .gitignore (REQUIRED)
Copy the standard `.gitignore` from Linux-Setup to protect sensitive data:
```bash
cp ../Linux-Setup/.gitignore .
```

## Multi-Platform Support

Playbooks should support multiple architectures and distributions:

### Architectures
- **x86_64**: Intel/AMD 64-bit systems
- **aarch64**: ARM 64-bit systems (Raspberry Pi 4, ARM servers)
- **armv7l**: ARM 32-bit systems (Raspberry Pi 3 and older)

### Distributions
- **Debian Family**: Debian, Ubuntu, Raspbian (apt)
- **Red Hat Family**: RHEL, CentOS, Fedora, Rocky Linux (yum/dnf)
- **Arch Family**: Arch Linux, Manjaro (pacman)

### Platform Detection Pattern
```yaml
# In tasks/main.yml
- name: Task for Debian-based systems
  ansible.builtin.apt:
    # ...
  when: ansible_os_family == "Debian"

- name: Task for Red Hat-based systems
  ansible.builtin.package:
    # ...
  when: ansible_os_family == "RedHat"

# Use architecture mapping from group_vars/all.yml
- name: Download architecture-specific binary
  ansible.builtin.get_url:
    url: "{{ repositories.package.base_url }}/{{ architecture_mapping[ansible_architecture].package }}"
```

## User Management Pattern

When implementing user management:

### Centralized User Configuration
Define users in `group_vars/all.yml`:
```yaml
users_list:
  - name: username
    groups: "sudo,docker,..."
    ssh_public_key: "ssh-rsa AAAAB3..."
    sudo_access: true
```

### Generic User Role
- Single `users` role handles all users
- SSH keys stored in variables, not template files
- Generic sudoers template: `templates/sudoers.j2`
- No user-specific roles or templates

## Inventory Structure Pattern

All playbooks use a **multi-dimensional inventory structure** where hosts can belong to multiple groups simultaneously. This provides maximum flexibility and maintainability.

### Inventory Organization Dimensions

Hosts are organized across three dimensions:

#### 1. OS Family Groups (Distribution-based)
```yaml
all:
  children:
    debian_based:
      children:
        raspberry_pi:        # All Raspberry Pi hosts
        ubuntu_baremetal:    # Ubuntu bare-metal servers
        ubuntu_vm:           # Ubuntu virtual machines
        debian_baremetal:    # Debian bare-metal servers
        debian_vm:           # Debian virtual machines

    redhat_based:
      children:
        centos_baremetal:    # CentOS/Rocky Linux servers
        centos_vm:           # CentOS/Rocky Linux VMs
        fedora_baremetal:    # Fedora workstations
        fedora_vm:           # Fedora VMs

    arch_based:
      children:
        arch_baremetal:      # Arch Linux systems
        arch_vm:             # Arch Linux VMs
```

#### 2. Purpose Groups (Function-based)
```yaml
    ntp:                     # NTP servers
    pihole:                  # Pi-hole DNS servers
    klipper:                 # 3D printer hosts
    zigbee:                  # Zigbee gateways
    pikvm:                   # PiKVM systems
    k3s:                     # Kubernetes cluster
      children:
        control:             # K3s control plane
        worker:              # K3s worker nodes
```

#### 3. Feature Groups (Capability-based)
```yaml
    vm_hardware:             # All virtual machines
      children:
        ubuntu_vm:
        debian_vm:
        centos_vm:
        fedora_vm:
        arch_vm:

    uctronics:               # Hosts with Uctronics OLED displays
```

### Multi-Group Membership Example

A single host can belong to multiple groups:

**Host**: `10.10.2.220` (Kube-Pi-CP01)
- Member of `debian_based` → `raspberry_pi` (OS/hardware type)
- Member of `k3s` → `control` (K3s control plane role)
- Member of `uctronics` (has OLED display feature)

This allows role targeting based on relevant characteristics:
```yaml
# Install on all Raspberry Pi hosts
when: "'raspberry_pi' in group_names"

# Install on all VMs regardless of OS
when: "'vm_hardware' in group_names"

# Install on hosts with Uctronics displays
when: "'uctronics' in group_names"
```

### Inventory Best Practices

1. **Single Host Definition**: Each IP address defined once, inherits from multiple groups
2. **Flat Structure**: Avoid deep nesting; use group inheritance for logical combinations
3. **Clear Naming**: Group names should clearly indicate their purpose
4. **Logical Grouping**: Create groups based on what makes sense to target together
5. **Avoid Mixing**: Don't mix `hosts:` and `children:` in the same group unless absolutely necessary

### Example Targeting

```bash
# Target all Raspberry Pi hosts
ansible-playbook main.yml --limit raspberry_pi

# Target all K3s nodes (control + workers)
ansible-playbook main.yml --limit k3s

# Target multiple groups
ansible-playbook main.yml --limit 'pihole:ntp'

# Target all VMs across all distributions
ansible-playbook main.yml --limit vm_hardware

# View host group memberships
ansible-inventory -i inventory/hosts.yml --host 10.10.2.220
```

## Key Principles

1. **Centralization**: Single source of truth in `group_vars/all.yml`
2. **Reusability**: Generic templates and roles
3. **Standards Compliance**: ansible-lint passing, FQCN, proper naming
4. **Multi-Platform**: Support multiple architectures and distributions
5. **Security**: Vault-encrypted credentials, SSH keys, no hardcoded secrets
6. **Documentation**: Comprehensive CLAUDE.md for each project
7. **Modularity**: Self-contained roles with clear dependencies
8. **Scalability**: Easy to add new hosts, users, or configurations
9. **Multi-Dimensional Inventory**: Hosts belong to multiple groups for flexible targeting
10. **Shared Inventory Structure**: All playbooks use the same inventory organization pattern

## Pre-Commit Security Workflow

**CRITICAL**: Before committing or pushing changes, especially when working with new playbooks:

### 1. Verify Sensitive File Protection
```bash
# Ensure .gitignore exists in playbook directory
test -f .gitignore && echo "✓ .gitignore exists" || echo "✗ MISSING .gitignore"

# Check that sensitive files are properly ignored
git check-ignore -v group_vars/all.yml inventory/hosts.yml
```

### 2. Run Security Verification
```bash
# From repository root
./verify-security.sh
```

### 3. Manual Review Before Commit
```bash
# Review what will be committed
git status
git diff --cached

# Search for potential credentials
grep -r "password.*=" --include="*.yml" --exclude="*.example" --exclude-dir=".git" | grep -v "TODO"
```

### 4. Maintain Example Files
**Rule**: Whenever you modify `inventory/hosts.yml` or `group_vars/all.yml`, you **MUST** update the corresponding `.example` files:

```bash
# After editing actual config, update sanitized example
cp group_vars/all.yml group_vars/all.yml.example
# Then manually sanitize: replace passwords with "CHANGE_ME", IPs with examples
```

## Best Practices for AI Assistance

When working with these playbooks:

1. **Always check existing CLAUDE.md** files for project-specific guidance
2. **Maintain centralized configuration** - add variables to `group_vars/all.yml`, not hardcode in roles
3. **Follow naming conventions** - prefix role variables with role name
4. **Use FQCN** - always use fully qualified collection names for modules
5. **Run ansible-lint** - ensure all changes pass linting
6. **Create generic solutions** - avoid user-specific or host-specific roles when a generic one will work
7. **Document changes** - update CLAUDE.md when making architectural changes
8. **Mark security TODOs** - add `# TODO: Use ansible-vault` for plaintext credentials
9. **Use multi-dimensional inventory** - organize hosts by OS, purpose, and features for flexible targeting
10. **Keep inventory consistent** - all playbooks share the same inventory structure pattern
11. **Run security checks** - always run `./verify-security.sh` before suggesting git commits
12. **Maintain example files** - update `.example` files when modifying actual configs