# Node Exporter Role

Ansible role for installing and configuring [Prometheus Node Exporter](https://github.com/prometheus/node_exporter) for system metrics collection.

## Overview

This role installs the latest version of Prometheus Node Exporter on Linux systems, supporting multiple architectures (x86_64, ARM64, ARM32) and distributions (Debian, Ubuntu, RHEL, CentOS, Fedora, Arch Linux).

## Features

- ✅ **Latest Version**: Automatically installs node_exporter v1.9.1
- ✅ **Multi-Architecture**: Supports x86_64, ARM64 (aarch64), and ARM32 (armv7l)
- ✅ **Centralized Configuration**: Version and settings managed in `group_vars/all.yml`
- ✅ **Security Hardening**: Systemd service with security restrictions
- ✅ **Textfile Collector**: Support for custom metrics via textfile collector
- ✅ **Configurable Collectors**: Enable/disable specific collectors
- ✅ **Health Checks**: Automatic verification that metrics endpoint is responding

## Default Configuration

The role comes with sensible defaults in `defaults/main.yml`:

```yaml
node_exporter_port: 9100
node_exporter_textfile_dir: "/var/lib/node_exporter"
node_exporter_enable_textfile_collector: true
node_exporter_enabled_collectors: []
node_exporter_disabled_collectors: []
node_exporter_extra_args: ""
```

## Usage

### Basic Usage

Enable the role in `group_vars/all.yml`:

```yaml
role_enabled:
  node_exporter: true

software_versions:
  node_exporter: "1.9.1"
```

Then run the playbook:

```bash
ansible-playbook -i inventory/hosts.yml main.yml
```

### Custom Port

Override the default port in `group_vars/all.yml`:

```yaml
node_exporter_port: 9101
```

### Enable Additional Collectors

Enable specific collectors (disabled by default):

```yaml
node_exporter_enabled_collectors:
  - systemd          # Systemd unit metrics
  - processes        # Process metrics
  - interrupts       # Interrupt statistics
  - tcpstat          # TCP connection statistics
```

### Disable Default Collectors

Disable collectors to reduce metric cardinality:

```yaml
node_exporter_disabled_collectors:
  - arp              # ARP table metrics
  - bcache           # bcache metrics
  - bonding          # Network bonding metrics
  - conntrack        # Conntrack metrics
```

### Textfile Collector

The textfile collector is enabled by default, allowing you to expose custom metrics:

```bash
# Create custom metrics file
echo 'custom_metric{label="value"} 123' > /var/lib/node_exporter/custom.prom
```

To disable the textfile collector:

```yaml
node_exporter_enable_textfile_collector: false
```

### Additional CLI Arguments

Pass extra command-line arguments:

```yaml
node_exporter_extra_args: "--log.level=debug --log.format=json"
```

## Multi-Architecture Support

The role automatically detects the system architecture and downloads the correct binary using the `architecture_mapping` in `group_vars/all.yml`:

```yaml
architecture_mapping:
  "x86_64":
    node_exporter: "linux-amd64"
  "aarch64":
    node_exporter: "linux-arm64"
  "armv7l":
    node_exporter: "linux-armv7"
```

## Systemd Service

The role creates a hardened systemd service at `/etc/systemd/system/node_exporter.service`:

```ini
[Unit]
Description=Prometheus Node Exporter
Documentation=https://github.com/prometheus/node_exporter
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=node_exporter
Group=node_exporter
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:9100
Restart=on-failure
RestartSec=5s

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/var/lib/node_exporter

[Install]
WantedBy=multi-user.target
```

## Verification

After installation, verify node_exporter is running:

```bash
# Check service status
systemctl status node_exporter

# Test metrics endpoint
curl http://localhost:9100/metrics

# View specific metrics
curl -s http://localhost:9100/metrics | grep node_cpu
```

## Prometheus Integration

Add node_exporter targets to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets:
          - 'server1:9100'
          - 'server2:9100'
          - 'server3:9100'
```

## Default Collectors

Node exporter includes many collectors enabled by default:

**Enabled by Default:**
- `cpu` - CPU statistics
- `diskstats` - Disk I/O statistics
- `filesystem` - Filesystem statistics
- `loadavg` - Load average
- `meminfo` - Memory statistics
- `netdev` - Network device statistics
- `netstat` - Network statistics
- `stat` - Various system statistics
- `time` - System time
- `uname` - System information
- `vmstat` - Virtual memory statistics

**Disabled by Default** (require explicit enabling):
- `systemd` - Systemd unit metrics
- `processes` - Process statistics
- `interrupts` - Interrupt statistics
- `tcpstat` - TCP connection statistics
- `supervisord` - Supervisord process metrics

See the [official documentation](https://github.com/prometheus/node_exporter#collectors) for a complete list.

## Troubleshooting

### Service won't start

Check systemd journal:
```bash
journalctl -u node_exporter -f
```

### Metrics endpoint unreachable

Verify port and firewall:
```bash
# Check if listening
ss -tulpn | grep 9100

# Check firewall (if enabled)
sudo ufw allow 9100/tcp
```

### Textfile collector not working

Ensure directory permissions:
```bash
sudo chown node_exporter:node_exporter /var/lib/node_exporter
sudo chmod 755 /var/lib/node_exporter
```

## Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `node_exporter_port` | `9100` | Port for metrics endpoint |
| `node_exporter_userid` | `node_exporter` | System user for service |
| `node_exporter_groupid` | `node_exporter` | System group for service |
| `node_exporter_textfile_dir` | `/var/lib/node_exporter` | Directory for textfile collector |
| `node_exporter_enable_textfile_collector` | `true` | Enable textfile collector |
| `node_exporter_enabled_collectors` | `[]` | List of collectors to enable |
| `node_exporter_disabled_collectors` | `[]` | List of collectors to disable |
| `node_exporter_extra_args` | `""` | Additional CLI arguments |

## Requirements

- Ansible 2.10 or higher
- Target system: Linux (Debian, Ubuntu, RHEL, CentOS, Fedora, Arch)
- Architecture: x86_64, aarch64, or armv7l
- Internet connection for downloading binaries

## Dependencies

None. This is a standalone role.

## License

MIT

## Author

Part of the Linux-Setup Ansible playbook collection.

## See Also

- [Prometheus Node Exporter Documentation](https://github.com/prometheus/node_exporter)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Available Collectors](https://github.com/prometheus/node_exporter#collectors)
