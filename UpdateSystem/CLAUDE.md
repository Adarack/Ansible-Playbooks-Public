# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UpdateSystem is an Ansible playbook designed to update all packages on Linux systems across multiple distributions and architectures. It also handles Pi-hole updates when Pi-hole is detected on target systems.

## Architecture

- **Main Playbook**: `main.yml` - Orchestrates system, Pi-hole, and PiKVM updates in four plays:
  1. `pihole` hosts with `serial: 1` (DNS stays up)
  2. `k3s` hosts with `serial: 1` (etcd quorum kept; nodes drained before reboot). Override with `-e k3s_update_serial=2`
  3. All other hosts in parallel (`all:!pihole:!k3s`)
  4. Summary of pending packages / reboot status per host
- **Shared Tasks**: `tasks/update_host.yml` - Per-host steps imported by every play (PiKVM detection, role imports, summary fact)
- **Serial Playbook**: `pihole_update_serial.yml` - Updates Pi-hole servers one at a time with reboots
- **Inventory**: `inventory/hosts.yml` - Multi-dimensional structure shared with Linux-Setup
- **Roles Structure**: Three specialized roles for update operations:
  - `system_update`: Multi-distribution package update role (Debian, Red Hat, Arch)
  - `pihole_update`: Pi-hole component and gravity database updates
  - `pikvm_update`: PiKVM updates with read-only filesystem management

## Supported Platforms

### Distributions
- **Debian Family**: Debian, Ubuntu, Raspbian (using apt)
- **Red Hat Family**: RHEL, CentOS, Fedora, Rocky Linux (using yum/dnf)
- **Arch Family**: Arch Linux, Manjaro (using pacman)

### Architectures
- **x86_64**: Intel/AMD 64-bit systems
- **aarch64**: ARM 64-bit systems (Raspberry Pi 4, ARM servers)
- **armv7l**: ARM 32-bit systems (Raspberry Pi 3 and older)

## Common Commands

### Running the Main Playbook

```bash
# Update all systems in inventory
ansible-playbook -i inventory/hosts.yml main.yml

# Update specific groups
ansible-playbook -i inventory/hosts.yml main.yml --limit raspberry_pi
ansible-playbook -i inventory/hosts.yml main.yml --limit debian_based
ansible-playbook -i inventory/hosts.yml main.yml --limit pihole

# Update all K3s nodes
ansible-playbook -i inventory/hosts.yml main.yml --limit k3s

# Update single host
ansible-playbook -i inventory/hosts.yml main.yml --limit 10.10.2.50

# Check mode (dry run) - see what would be updated
ansible-playbook -i inventory/hosts.yml main.yml --check

# Update with automatic reboot if required
ansible-playbook -i inventory/hosts.yml main.yml -e "system_update_reboot_if_required=true"
```

### Running Serial Pi-hole Updates

```bash
# Update Pi-hole servers one at a time with reboots
ansible-playbook -i inventory/hosts.yml pihole_update_serial.yml

# This ensures at least one Pi-hole stays online during updates
```

### Validation

```bash
# Syntax validation
ansible-playbook -i inventory/hosts.yml main.yml --syntax-check

# Run ansible-lint
ansible-lint main.yml

# Lint specific role
ansible-lint roles/system_update/
ansible-lint roles/pihole_update/

# List hosts
ansible-inventory -i inventory/hosts.yml --list
```

### Targeting Specific Updates

```bash
# Only update system packages (skip Pi-hole and PiKVM)
ansible-playbook -i inventory/hosts.yml main.yml --tags system

# Only update Pi-hole (skip system packages)
ansible-playbook -i inventory/hosts.yml main.yml --tags pihole

# Only update PiKVM systems
ansible-playbook -i inventory/hosts.yml main.yml --limit pikvm

# Force gravity update on Pi-hole
ansible-playbook -i inventory/hosts.yml main.yml --limit pihole -e "pihole_update_gravity=true"
```

## Configuration

### Centralized Configuration (group_vars/all.yml)

All update behavior is controlled through centralized variables:

#### Role Enablement
```yaml
role_enabled:
  system_update: true      # Update all system packages (skips PiKVM automatically)
  pihole_update: true      # Update Pi-hole (if installed)
  pikvm_update: true       # Update PiKVM (if detected)
```

#### System Update Settings
```yaml
system_update_cache: true              # Update package cache
system_update_autoremove: true         # Remove unused packages
system_update_autoclean: true          # Clean package cache
system_update_reboot_if_required: false # Auto-reboot after updates
system_update_reboot_timeout: 600      # Reboot timeout (seconds)
system_update_upgrade_type: "safe"     # "safe" or "dist" for Debian
system_update_reboot_excluded_groups: [vps]  # Never auto-reboot these groups
system_update_min_free_mb_root: 500    # Pre-flight free space on /
system_update_min_free_mb_boot: 50     # Pre-flight free space on /boot, /boot/firmware
system_update_apt_lock_timeout: 300    # Wait for dpkg lock (unattended-upgrades)
system_update_k3s_drain: true          # Drain/uncordon k3s nodes around reboots
```

#### Pi-hole Update Settings
```yaml
pihole_update_enabled: true       # Update Pi-hole components
pihole_update_gravity: true       # Update gravity (blocklists)
pihole_update_restart_ftl: false  # Restart FTL service
pihole_update_check_status: true  # Check status after update
pihole_update_serial_force_reboot: false   # Serial playbook: reboot even if not required
pihole_update_verify_domain: google.com    # Serial playbook: domain used to verify DNS
```

#### PiKVM Update Settings
```yaml
pikvm_update_enabled: true                # Update PiKVM systems
pikvm_update_reboot_after: false          # Reboot after update
pikvm_update_reboot_timeout: 300          # Reboot timeout (seconds)
pikvm_update_timeout: 600                 # Update timeout (seconds)
pikvm_update_force_install_updater: false # Force install pikvm-os-updater
```

### Inventory Structure

The inventory uses a **multi-dimensional structure** where hosts belong to multiple groups:

#### OS Family Groups
- `debian_based` → `raspberry_pi`, `ubuntu_baremetal`, `ubuntu_vm`, `debian_baremetal`, `debian_vm`
- `redhat_based` → `centos_baremetal`, `centos_vm`, `fedora_baremetal`, `fedora_vm`
- `arch_based` → `arch_baremetal`, `arch_vm`

#### Purpose Groups
- `ntp` - NTP servers
- `pihole` - Pi-hole DNS servers
- `klipper` - 3D printer hosts
- `zigbee` - Zigbee gateways
- `pikvm` - PiKVM systems
- `k3s` → `control`, `worker` - Kubernetes nodes

#### Feature Groups
- `vm_hardware` - All virtual machines
- `uctronics` - Hosts with Uctronics OLED displays

**Note**: Inventory structure is shared with Linux-Setup playbook for consistency.

## Role Details

### system_update Role

**Purpose**: Update all system packages across multiple Linux distributions

**Features**:
- Distribution-aware package updates (apt, yum/dnf, pacman)
- Automatic package cache management
- Orphaned package removal
- Pre-flight free-space check on `/` and `/boot`
- Reboot detection: `/var/run/reboot-required` (Debian), `needs-restarting -r` (RHEL), missing `/usr/lib/modules/<running kernel>` (Arch)
- Reboot-excluded groups (`system_update_reboot_excluded_groups`)
- K3s drain before reboot / uncordon after (delegated to another control node)
- Sets facts `system_update_pending_packages`, `system_update_changed`, `system_update_reboot_needed`, `system_update_rebooted`
- Upgrade type selection (safe vs dist-upgrade)

**Files**:
- `tasks/main.yml`: Entry point; includes the per-family file
- `tasks/preflight.yml`: Disk space checks
- `tasks/debian.yml`, `tasks/redhat.yml`, `tasks/archlinux.yml`: Per-family updates
- `tasks/reboot.yml`: Reboot decision, k3s drain/uncordon
- `defaults/main.yml`: Default update behavior settings
- `meta/main.yml`: Role metadata and platform support

**Key Variables** (all prefixed with `system_update_`):
- `system_update_cache`: Update cache before upgrade
- `system_update_autoremove`: Remove unused packages
- `system_update_autoclean`: Clean package cache
- `system_update_reboot_if_required`: Auto-reboot if needed
- `system_update_upgrade_type`: "safe" or "dist" upgrade

### pihole_update Role

**Purpose**: Update Pi-hole DNS server components and blocklists

**Features**:
- Automatic Pi-hole detection (skips if not installed)
- Pi-hole component updates (`pihole -up`)
- Gravity database updates (`pihole -g`)
- Optional FTL service restart
- Status checking after updates

**Files**:
- `tasks/main.yml`: Pi-hole update and maintenance tasks
- `defaults/main.yml`: Default Pi-hole update settings
- `meta/main.yml`: Role metadata

**Key Variables** (all prefixed with `pihole_update_`):
- `pihole_update_enabled`: Enable Pi-hole updates
- `pihole_update_gravity`: Update gravity blocklists
- `pihole_update_restart_ftl`: Restart FTL service
- `pihole_update_check_status`: Check status after update

**Pi-hole Commands Used**:
- `pihole -up`: Update Pi-hole components (Core, FTL, Web)
- `pihole -g`: Update gravity database (blocklists)
- `pihole status`: Check Pi-hole service status

### pikvm_update Role

**Purpose**: Update PiKVM systems while managing read-only filesystem

**Features**:
- PiKVM detection in `tasks/update_host.yml`: host in `pikvm` group or `/usr/bin/kvmd` exists
- Read-only filesystem management (`rw` → update → `ro`)
- Installs `pikvm-os-updater` if needed
- Handles ALL system updates (not just PiKVM components)
- Optional reboot after updates
- Proper timeout handling for long-running updates

**Files**:
- `tasks/main.yml`: PiKVM update with filesystem management
- `defaults/main.yml`: Default PiKVM update settings
- `meta/main.yml`: Role metadata

**Key Variables** (all prefixed with `pikvm_update_`):
- `pikvm_update_enabled`: Enable PiKVM updates
- `pikvm_update_reboot_after`: Reboot after update
- `pikvm_update_timeout`: Update operation timeout
- `pikvm_update_force_install_updater`: Force install updater package

**PiKVM Commands Used**:
- `rw`: Make filesystem writable
- `pikvm-update`: Update ALL system components (OS + PiKVM)
- `ro`: Remount filesystem as read-only
- `pacman`: Package manager (used if updater needs installation)

**Important Notes**:
- PiKVM uses Arch Linux ARM with a read-only root filesystem
- `pikvm-update` handles ALL updates (not just PiKVM components)
- `system_update` role automatically skips PiKVM hosts
- Early detection prevents conflicts between update methods
- Requires special `ansible_remote_tmp` setting in inventory

## Quality Assurance

- ✅ **ansible-lint**: All roles pass production-level linting
- ✅ **FQCN compliance**: All modules use Fully Qualified Collection Names
- ✅ **Variable naming**: Role variables properly prefixed
- ✅ **Error handling**: Proper `changed_when` and `failed_when` conditions
- ✅ **Distribution detection**: Uses `ansible_os_family` for platform-specific tasks
- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Non-destructive detection**: Pi-hole role skips gracefully if not installed

## Update Workflow

1. **Gather Facts**: Collect system information (distribution, architecture)
2. **Display Info**: Show target system details
3. **Early PiKVM Detection**: Check if host is a PiKVM system (prevents conflicts)
4. **System Update** (skipped for PiKVM):
   - Update package cache
   - Upgrade all packages
   - Remove unused packages
   - Clean package cache
   - Check for reboot requirement (Debian/Ubuntu)
5. **Pi-hole Update** (if detected):
   - Detect if Pi-hole is installed
   - Update Pi-hole components if present
   - Update gravity database (blocklists)
   - Check service status
6. **PiKVM Update** (if detected):
   - Make filesystem writable (`rw`)
   - Install pikvm-os-updater if needed
   - Run `pikvm-update` (handles ALL updates)
   - Remount filesystem read-only (`ro`)
   - Optional reboot
7. **Display Results**: Show update completion status

## Safety Features

### Reboot Protection
- **Default**: No automatic reboots (`system_update_reboot_if_required: false`)
- **Detection**: Debian/Ubuntu, RHEL (`needs-restarting`) and Arch (kernel modules check)
- **Excluded groups**: Hosts in `system_update_reboot_excluded_groups` (default `vps`) are never auto-rebooted
- **Serial plays**: Pi-hole and K3s hosts update/reboot one at a time; K3s nodes are drained first
- **Warning**: Notifies when reboot is needed but not automatic
- **Override**: Can be enabled per-run or in configuration

### Pi-hole Safety
- **Non-destructive**: Checks for Pi-hole installation before attempting updates
- **Graceful Skip**: Skips Pi-hole updates silently if not installed
- **Optional FTL restart**: Does not restart by default to avoid DNS interruption
- **Status verification**: Checks Pi-hole status after updates
- **Serial Updates**: Use `pihole_update_serial.yml` to update servers one at a time

### PiKVM Safety
- **Early Detection**: Detects PiKVM before system_update runs
- **Exclusive Updates**: Only `pikvm-update` runs on PiKVM hosts
- **Filesystem Protection**: Automatically manages read-only/writable states
- **Graceful Remount**: `ro` runs in an `always:` block (even if the update fails) with `failed_when: false` for busy filesystems
- **Timeout**: `pikvm-update` runs async, bounded by `pikvm_update_timeout`
- **Temporary Directory**: Uses `/tmp` for Ansible operations (read-only root)

### Update Types
- **Safe Upgrade** (default): Standard package upgrades without removing packages
- **Dist Upgrade**: Full distribution upgrade (can remove/add packages)
- **PiKVM Update**: Comprehensive OS and application updates via `pikvm-update`

## Scheduling Updates

### Cron Example
```bash
# Daily updates at 2 AM
0 2 * * * cd /path/to/UpdateSystem && ansible-playbook -i inventory/hosts.yml main.yml >> /var/log/ansible-updates.log 2>&1

# Weekly Pi-hole updates on Sunday at 3 AM
0 3 * * 0 cd /path/to/UpdateSystem && ansible-playbook -i inventory/hosts.yml main.yml --limit pihole
```

### Systemd Timer Example
Create `/etc/systemd/system/ansible-updates.service`:
```ini
[Unit]
Description=Ansible System Updates
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/path/to/UpdateSystem
ExecStart=/usr/bin/ansible-playbook -i inventory/hosts.yml main.yml
```

Create `/etc/systemd/system/ansible-updates.timer`:
```ini
[Unit]
Description=Daily Ansible System Updates

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable: `systemctl enable --now ansible-updates.timer`

## Best Practices

### Before Running Updates
1. **Test on non-production systems first**
2. **Check for critical services** that may be affected
3. **Review recent package changes** if using dist-upgrade
4. **Ensure backup/snapshot** of critical systems
5. **Plan for reboots** if kernel updates are expected

### Production Recommendations
1. **Maintenance windows**: Schedule updates during low-traffic periods
2. **Staged rollouts**: Update non-critical systems first
3. **Monitoring**: Watch for update failures or service disruptions
4. **Communication**: Notify users of planned maintenance
5. **Rollback plan**: Have procedures to revert updates if needed

### Pi-hole Specific
1. **Redundancy**: Run updates on secondary Pi-hole first
2. **DNS failover**: Ensure backup DNS is configured
3. **Release notes**: Check Pi-hole blog before major updates
4. **Gravity timing**: Schedule gravity updates during off-peak hours

## Troubleshooting

### Common Issues

**Updates fail with "permission denied"**:
- Check `ansible_become_password` in `group_vars/all.yml`
- Verify sudo access for remote user
- Ensure SSH key authentication is working

**Pi-hole update skipped unexpectedly**:
- Detection checks `pihole_update_binary` (default `/usr/local/bin/pihole`)
- Verify Pi-hole installation: `ls -l /usr/local/bin/pihole`
- Review `pihole_update_enabled` setting

**PiKVM update fails with "permission denied"**:
- Verify `ansible_remote_tmp` is set in inventory for PiKVM hosts
- Should be: `ansible_remote_tmp: "/tmp/.ansible-${USER}/tmp"`
- Also set `ansible_async_dir: "/tmp/.ansible-root/async"` (pikvm-update runs async)
- Check that `pikvm-update` command exists on target

**System updates run on PiKVM (should skip)**:
- Verify early detection is enabled in main.yml
- Check `pikvm_update_is_pikvm_system` fact (host in `pikvm` group or `/usr/bin/kvmd` exists)
- Review task order - detection must happen before system_update

**Reboot not happening automatically**:
- Verify `system_update_reboot_if_required: true` is set
- Check `/var/run/reboot-required` exists on target
- Check the host is not in `system_update_reboot_excluded_groups`
- RHEL needs `needs-restarting` (dnf-utils) for detection

**K3s drain fails**:
- Drain runs `k3s kubectl` on another control node (`system_update_k3s_control_group`)
- Node name defaults to the lowercase hostname; override with `system_update_k3s_node_name`
- Disable with `system_update_k3s_drain: false`

**PiKVM filesystem busy error**:
- Normal when remounting read-only
- Error is suppressed with `failed_when: false` on `ro` command
- Filesystem will remount read-only on next reboot

### Viewing Logs
```bash
# View Ansible logs
tail -f ~/.ansible/logs/updatesystem.log

# View system package manager logs
# Debian/Ubuntu
tail -f /var/log/apt/history.log

# RHEL/CentOS/Fedora
tail -f /var/log/dnf.log

# Pi-hole
tail -f /var/log/pihole/pihole.log
```

## Security Notes

- **Credentials**: Store `ansible_become_password` in `group_vars/all.yml` (TODO: encrypt with ansible-vault)
- **SSH keys**: Use key-based authentication instead of passwords
- **Vault encryption**: Encrypt sensitive variables before production use
- **Update verification**: Always test updates in non-production first
- **Change management**: Document and track system updates

## Related Documentation

- [Ansible Package Module Docs](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/package_module.html)
- [Pi-hole Update Documentation](https://docs.pi-hole.net/main/update/)
- [Pi-hole Command Line Documentation](https://docs.pi-hole.net/core/pihole-command/)
- [PiKVM Documentation](https://docs.pikvm.org/)
- [PiKVM Update Process](https://docs.pikvm.org/)
