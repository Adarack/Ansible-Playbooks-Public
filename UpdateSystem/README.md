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
ansible-playbook -i inventory/hosts.yml main.yml --limit pihole
```

## What It Does

- **System Updates**: Updates all packages on Debian, Red Hat, and Arch-based systems
- **Pi-hole Updates**: Updates Pi-hole components and gravity database (if installed)
- **PiKVM Updates**: Runs `pikvm-update` with read-only filesystem handling
- **Safe Ordering**: Pi-holes and K3s nodes are updated (and rebooted) one at a time; K3s nodes are drained before reboot
- **Pre-flight Checks**: Fails early if `/` or `/boot` is low on space
- **Summary**: Prints per-host pending packages / reboot status at the end
- **Multi-Platform**: Supports x86_64, ARM64, and ARM32 architectures
- **Automatic Reboots**: Hosts reboot when an update requires it (`system_update_reboot_if_required` in `group_vars/all.yml`; groups listed in `system_update_reboot_excluded_groups` only get a warning)

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

# Only run Pi-hole updates (skip OS packages) on all hosts
ansible-playbook -i inventory/hosts.yml main.yml --tags pihole

# Only OS packages / only PiKVM
ansible-playbook -i inventory/hosts.yml main.yml --tags system
ansible-playbook -i inventory/hosts.yml main.yml --tags pikvm

# Pi-holes one at a time, rebooting when needed, verifying DNS after each
ansible-playbook -i inventory/hosts.yml pihole_update_serial.yml

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

✅ Reboots only when required, one host at a time for Pi-hole and K3s
✅ Optional reboot-excluded groups (e.g. `[vps]`)
✅ PiKVM filesystem always remounted read-only, even if the update fails
✅ Graceful Pi-hole detection (skips if not installed)
✅ Check mode support for dry runs
✅ Idempotent - safe to run multiple times
✅ ansible-lint production compliance

## Project Structure

```
UpdateSystem/
├── main.yml                    # Main playbook (serial plays for pihole/k3s)
├── pihole_update_serial.yml    # Pi-holes one at a time with DNS verification
├── tasks/update_host.yml       # Shared per-host steps used by every play
├── ansible.cfg                 # Ansible configuration
├── inventory/hosts.yml         # Target systems
├── group_vars/all.yml          # Centralized config
└── roles/
    ├── system_update/          # Multi-distro package updates + reboot handling
    ├── pihole_update/          # Pi-hole updates
    └── pikvm_update/           # PiKVM updates
```
