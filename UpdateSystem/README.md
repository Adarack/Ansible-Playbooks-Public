# UpdateSystem - Ansible Update Playbook

Multi-distribution system update playbook with Pi-hole support.

## Quick Start

```bash
# 1. Configure your inventory
vim inventory/hosts.yml

# 2. Configure update settings
vim group_vars/all.yml

# 3. Run updates on all systems
ansible-playbook -i inventory/hosts.yml main.yml

# 4. Update specific group
ansible-playbook -i inventory/hosts.yml main.yml --limit debian_based
ansible-playbook -i inventory/hosts.yml main.yml --limit pihole_servers
```

## What It Does

- **System Updates**: Updates all packages on Debian, Red Hat, and Arch-based systems
- **Pi-hole Updates**: Updates Pi-hole components and gravity database (if installed)
- **Multi-Platform**: Supports x86_64, ARM64, and ARM32 architectures
- **Safe by Default**: No automatic reboots, graceful handling of missing components

## Supported Platforms

- **Debian/Ubuntu** (apt)
- **RHEL/CentOS/Fedora** (yum/dnf)
- **Arch Linux** (pacman)
- **Pi-hole** (automatic detection)

## Common Tasks

```bash
# Dry run (check mode)
ansible-playbook -i inventory/hosts.yml main.yml --check

# Update with automatic reboot
ansible-playbook -i inventory/hosts.yml main.yml -e "system_update_reboot_if_required=true"

# Only update Pi-hole
ansible-playbook -i inventory/hosts.yml main.yml --limit pihole_servers

# Validate syntax
ansible-playbook -i inventory/hosts.yml main.yml --syntax-check

# Run ansible-lint
ansible-lint main.yml
```

## Configuration

Edit `group_vars/all.yml` to control:
- Role enablement
- Update behavior (autoremove, autoclean)
- Reboot settings
- Pi-hole update options

## Documentation

See [CLAUDE.md](CLAUDE.md) for complete documentation including:
- Detailed role descriptions
- All configuration options
- Scheduling examples
- Troubleshooting guide
- Best practices

## Safety Features

✅ No automatic reboots by default
✅ Graceful Pi-hole detection (skips if not installed)
✅ Check mode support for dry runs
✅ Idempotent - safe to run multiple times
✅ ansible-lint production compliance

## Project Structure

```
UpdateSystem/
├── main.yml                    # Main playbook
├── ansible.cfg                 # Ansible configuration
├── inventory/hosts.yml         # Target systems
├── group_vars/all.yml          # Centralized config
└── roles/
    ├── system_update/          # Multi-distro package updates
    └── pihole_update/          # Pi-hole updates
```
