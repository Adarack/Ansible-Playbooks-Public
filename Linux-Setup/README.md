# Linux-Setup Ansible Playbook

Multi-platform Linux system configuration playbook for setting up new systems with essential software, monitoring tools, and user accounts. Supports x86_64, ARM64, and ARM32 architectures across Debian, RHEL, and Arch-based distributions.

## 📋 Overview

This playbook automates the initial setup and configuration of Linux systems, including:

- ✅ **System updates** and essential packages
- ✅ **Docker & Docker Compose** installation
- ✅ **User management** with SSH keys and sudo access
- ✅ **Monitoring** (Prometheus, Grafana, Node Exporter, Raspberry Pi Exporter)
- ✅ **SSH configuration** hardening
- ✅ **Timezone and NTP** configuration
- ✅ **Pi-hole** DNS ad blocker (optional)
- ✅ **Oh My Zsh** shell customization (optional)

## 🚀 Quick Start

### Prerequisites

- **Ansible** 2.10 or higher installed on control node
- **SSH access** to target hosts with key-based authentication
- **Sudo privileges** on target hosts
- **Python 3** on target hosts

### Installation Steps

1. **Clone or navigate to this playbook**:
   ```bash
   cd Linux-Setup/
   ```

2. **Copy example files and customize**:
   ```bash
   # Copy inventory template
   cp inventory/hosts.yml.example inventory/hosts.yml

   # Copy configuration template
   cp group_vars/all.yml.example group_vars/all.yml
   ```

3. **Edit inventory with your hosts**:
   ```bash
   nano inventory/hosts.yml
   ```

   Example:
   ```yaml
   newlinux:
     hosts:
       10.10.2.50:  # Your Raspberry Pi or server
       10.10.2.51:  # Another host
     vars:
       ansible_user: "pi"
       ansible_ssh_private_key_file: "~/.ssh/pi_key"
   ```

4. **Edit configuration**:
   ```bash
   nano group_vars/all.yml
   ```

   Update:
   - `ansible_become_password` - Sudo password
   - `users_list` - Users to create/configure
   - `mqtt_config` - MQTT broker settings (if using monitoring)
   - `role_enabled` - Enable/disable specific roles

5. **Run the playbook**:
   ```bash
   ansible-playbook -i inventory/hosts.yml main.yml
   ```

## 📦 Included Roles

### Core Roles

| Role | Description | Platforms |
|------|-------------|-----------|
| **common-pkg** | System updates and essential packages | All |
| **docker** | Docker and Docker Compose installation | All |
| **timezone** | NTP and timezone configuration | All |
| **users** | User creation with SSH keys and sudo | All |
| **sshd_conf** | SSH daemon hardening | All |

### Monitoring Roles

| Role | Description | Platforms |
|------|-------------|-----------|
| **node_exporter** | System metrics exporter for Prometheus | All |
| **rpi_exporter** | Raspberry Pi hardware metrics | ARM only |
| **rpi_reporter** | MQTT-based system reporting | ARM (primary) |
| **monitoring_server** | Prometheus & Grafana stack | All |

### Optional Roles

| Role | Description | Platforms |
|------|-------------|-----------|
| **pihole** | Network-wide DNS ad blocker | All |
| **aaronmyatt.ohmyzsh_plbk** | Oh My Zsh shell customization | All |

## ⚙️ Configuration

### Role Enablement

Control which roles execute in `group_vars/all.yml`:

```yaml
role_enabled:
  common_pkg: true
  docker: true
  timezone: true
  users: true
  sshd_conf: true
  node_exporter: true
  rpi_exporter: true   # Only runs on Raspberry Pi
  rpi_reporter: true
  monitoring_server: false  # Enable on monitoring server only
  pihole: false
  ohmyzsh: false
```

### User Management

Define users in `group_vars/all.yml`:

```yaml
users_list:
  - name: your_username
    groups: "sudo,docker"
    ssh_public_key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB... your_username@hostname"
    sudo_access: true

  - name: developer
    ssh_public_key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB... dev@hostname"
    # No sudo access
```

### MQTT Configuration

For `rpi_reporter` and monitoring roles:

```yaml
mqtt_config:
  host: "10.10.2.32"
  port: 1883
  username: "mqtt_user"
  password: "your_password"  # TODO: Use ansible-vault
  discovery_prefix: "homeassistant"
  base_topic: "home/nodes"
```

### Software Versions

Centralized version management:

```yaml
software_versions:
  prometheus: "2.44.0"
  grafana: "9.5.2"
  node_exporter: "1.9.1"
  rpi_exporter: "0.8.0"
```

## 🎯 Common Use Cases

### Configure New Raspberry Pi

```bash
# 1. Add Pi to inventory
echo "10.10.2.50:" >> inventory/hosts.yml

# 2. Run playbook
ansible-playbook -i inventory/hosts.yml main.yml --limit 10.10.2.50
```

### Install Only Docker

```bash
ansible-playbook -i inventory/hosts.yml main.yml --tags docker
```

### Setup Monitoring Server

```bash
# 1. Enable monitoring_server role in group_vars/all.yml
# 2. Run on specific host
ansible-playbook -i inventory/hosts.yml main.yml --limit monitoring-server
```

### Add New User to Existing Systems

```bash
# 1. Add user to users_list in group_vars/all.yml
# 2. Run users role only
ansible-playbook -i inventory/hosts.yml main.yml --tags users
```

## 🖥️ Supported Platforms

### Architectures
- **x86_64**: Intel/AMD 64-bit servers and workstations
- **aarch64**: ARM 64-bit (Raspberry Pi 4/5, ARM servers)
- **armv7l**: ARM 32-bit (Raspberry Pi 3 and older)

### Operating Systems
- Debian 10+
- Ubuntu 20.04+
- Raspberry Pi OS (Raspbian)
- RHEL 8+, CentOS 8+, Rocky Linux 8+
- Fedora 35+
- Arch Linux, Manjaro

## 🔐 Security

### Ansible Vault

Encrypt sensitive variables:

```bash
# Encrypt password
echo 'your_password' | ansible-vault encrypt_string --stdin-name 'ansible_become_password'

# Edit encrypted file
ansible-vault edit group_vars/all.yml

# Run with vault
ansible-playbook -i inventory/hosts.yml main.yml --ask-vault-pass
```

### SSH Configuration

The `sshd_conf` role hardens SSH by:
- Disabling root login
- Disabling password authentication
- Restricting authentication methods
- Configuring allowed users

## 🧪 Testing

### Syntax Check

```bash
ansible-playbook -i inventory/hosts.yml main.yml --syntax-check
```

### Dry Run (Check Mode)

```bash
ansible-playbook -i inventory/hosts.yml main.yml --check
```

### Lint

```bash
ansible-lint main.yml
ansible-lint roles/docker/
```

### List Hosts

```bash
ansible-inventory -i inventory/hosts.yml --list
```

## 📊 Monitoring Setup

### Prometheus + Grafana Stack

1. **Enable on monitoring server**:
   ```yaml
   # group_vars/all.yml or host_vars/monitoring-server.yml
   role_enabled:
     monitoring_server: true
   ```

2. **Enable exporters on all hosts**:
   ```yaml
   role_enabled:
     node_exporter: true
     rpi_exporter: true  # Raspberry Pi only
   ```

3. **Access dashboards**:
   - Prometheus: `http://<monitoring-server>:9090`
   - Grafana: `http://<monitoring-server>:3000`

## 🐛 Troubleshooting

### Connection Issues

```bash
# Test SSH connectivity
ansible newlinux -i inventory/hosts.yml -m ping

# Test with different user
ansible newlinux -i inventory/hosts.yml -m ping -u pi
```

### Permission Denied

```bash
# Verify sudo password
ansible-playbook -i inventory/hosts.yml main.yml --ask-become-pass
```

### Role Not Running

Check role enablement:
```bash
# Verify role is enabled
grep "role_enabled" group_vars/all.yml
```

### Platform Detection

Check detected platform:
```bash
ansible newlinux -i inventory/hosts.yml -m setup -a "filter=ansible_os_family"
ansible newlinux -i inventory/hosts.yml -m setup -a "filter=ansible_architecture"
```

## 📁 Directory Structure

```
Linux-Setup/
├── README.md                    # This file
├── CLAUDE.md                    # Technical documentation
├── main.yml                     # Main playbook
├── ansible.cfg                  # Ansible configuration
├── .gitignore                   # Sensitive file protection
├── inventory/
│   ├── hosts.yml.example       # Example inventory
│   └── hosts.yml               # Your inventory (gitignored)
├── group_vars/
│   ├── all.yml.example         # Example config
│   └── all.yml                 # Your config (gitignored)
├── roles/                       # Ansible roles
│   ├── common-pkg/
│   ├── docker/
│   ├── timezone/
│   ├── users/
│   ├── sshd_conf/
│   ├── node_exporter/
│   ├── rpi_exporter/
│   ├── rpi_reporter/
│   ├── monitoring_server/
│   └── pihole/
└── templates/                   # Shared templates
```

## 🔄 Updating

### Update Playbook

```bash
# Pull latest changes
git pull

# Review changelog
cat CHANGELOG.md
```

### Update Software Versions

Edit `group_vars/all.yml`:
```yaml
software_versions:
  prometheus: "2.50.0"  # Update version
  grafana: "10.0.0"     # Update version
```

Then re-run playbook:
```bash
ansible-playbook -i inventory/hosts.yml main.yml
```

## 📖 Additional Documentation

- **[CLAUDE.md](./CLAUDE.md)**: Technical details, architecture, and AI assistance guidelines
- **[Ansible Docs](https://docs.ansible.com/)**: Official Ansible documentation
- **[Docker Install Guide](https://docs.docker.com/engine/install/)**: Docker installation reference

## 💡 Tips

- **Start small**: Test on one host before deploying to many
- **Use tags**: Run specific roles with `--tags` flag
- **Check mode**: Always dry-run with `--check` first
- **Limit hosts**: Use `--limit` for targeted deployments
- **Version control**: Track changes to `group_vars/all.yml` (encrypted)

## 📝 License

See repository root for licensing information.

## ⚠️ Disclaimer

Test in a non-production environment first. Review roles and configuration before deploying to production systems.
