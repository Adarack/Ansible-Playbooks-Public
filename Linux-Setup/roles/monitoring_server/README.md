# Monitoring Server Role

Ansible role for deploying a complete monitoring stack with [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/) for metrics collection and visualization.

## Overview

This role installs and configures a full monitoring server that automatically discovers and scrapes metrics from all hosts in your Ansible inventory. It provides both time-series data collection (Prometheus) and visualization (Grafana) in a single deployment.

## Features

- ✅ **Latest Versions**: Prometheus 2.44.0 and Grafana 9.5.2
- ✅ **Auto-Discovery**: Automatically generates scrape configs from inventory
- ✅ **Multi-Architecture**: Supports x86_64, ARM64 (aarch64), ARM32 (armv7l)
- ✅ **Centralized Configuration**: All settings in `group_vars/all.yml`
- ✅ **Security Hardening**: Systemd service with security restrictions
- ✅ **Config Validation**: Automatic validation with `promtool`
- ✅ **Health Checks**: Verifies both services are accessible
- ✅ **Multi-Distribution**: Debian, Ubuntu, Raspbian support

## Components Installed

### Prometheus (Port 9090)
- Time-series database for metrics
- Automatic service discovery from inventory
- Built-in alerting engine
- PromQL query language
- Data retention management

### Grafana (Port 3000)
- Visualization and dashboarding
- Multi-user support
- Alerting and notifications
- Plugin ecosystem
- Default login: `admin/admin`

## Default Configuration

The role comes with sensible defaults in `defaults/main.yml`:

```yaml
monitoring_server_prometheus_port: 9090
monitoring_server_grafana_port: 3000
monitoring_server_prometheus_retention_time: "2d"  # From services.data_retention
```

## Usage

### Basic Usage

Enable the role in `group_vars/all.yml`:

```yaml
role_enabled:
  monitoring_server: true

software_versions:
  prometheus: "2.44.0"
  grafana: "9.5.2"
```

Add a monitoring server to your inventory (`inventory/hosts.yml`):

```yaml
monitoring_servers:
  hosts:
    10.10.2.50:   # Your monitoring server
```

Then run the playbook:

```bash
ansible-playbook -i inventory/hosts.yml main.yml --limit monitoring_servers
```

## Automatic Scrape Configuration

The role **automatically generates** Prometheus scrape targets from your inventory. No manual configuration needed!

### Auto-Discovered Targets

**Node Exporter** (all hosts with `role_enabled.node_exporter: true`):
```yaml
- job_name: 'node'
  static_configs:
    - targets:
        - '10.10.2.9:9100'    # host-01
        - '10.10.2.18:9100'   # host-02
        - '10.10.2.50:9100'   # host-03
        # ... all hosts from inventory
```

**RPi Exporter** (Raspberry Pi hosts with `role_enabled.rpi_exporter: true`):
```yaml
- job_name: 'raspberry_pi'
  static_configs:
    - targets:
        - '10.10.2.9:9243'    # rpi-01
        - '10.10.2.18:9243'   # rpi-02
        # ... all Raspberry Pi hosts
```

**Grafana** (monitoring servers):
```yaml
- job_name: 'grafana'
  static_configs:
    - targets:
        - '10.10.2.50:3000'   # Grafana metrics
```

### How It Works

The `prometheus.conf.j2` template uses Jinja2 loops to iterate through inventory groups:

```jinja2
{% for host in groups['all'] %}
{% if hostvars[host].role_enabled.node_exporter | default(false) %}
  - '{{ host }}:{{ hostvars[host].node_exporter_port | default(9100) }}'
{% endif %}
{% endfor %}
```

**This means**:
- ✅ Add a host to inventory → automatically scraped
- ✅ Remove a host → automatically removed from scraping
- ✅ No manual Prometheus configuration needed
- ✅ Always in sync with your infrastructure

## Multi-Architecture Support

The role automatically detects architecture and downloads the correct binaries using `architecture_mapping` in `group_vars/all.yml`:

```yaml
architecture_mapping:
  "x86_64":
    prometheus: "linux-amd64"
    grafana: "amd64"
  "aarch64":
    prometheus: "linux-arm64"
    grafana: "arm64"
  "armv7l":
    prometheus: "linux-armv7"
    grafana: "armhf"
```

## Systemd Services

### Prometheus Service

```ini
[Unit]
Description=Prometheus Monitoring Server
Documentation=https://prometheus.io/docs/
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/data/prometheus \
  --storage.tsdb.retention.time=2d \
  --web.listen-address=0.0.0.0:9090

Restart=on-failure
RestartSec=5s

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/data/prometheus

[Install]
WantedBy=multi-user.target
```

### Grafana Service

Grafana uses the official systemd service from the .deb package with default configuration.

## Verification

After installation:

```bash
# Check services
ssh user@monitoring-server "systemctl status prometheus grafana-server"

# Access web interfaces
http://monitoring-server:9090   # Prometheus
http://monitoring-server:3000   # Grafana

# View Prometheus targets
http://monitoring-server:9090/targets

# View Prometheus config
http://monitoring-server:9090/config
```

## Grafana Setup

### First Login

1. Navigate to `http://monitoring-server:3000`
2. Login with `admin/admin`
3. Change the password when prompted

### Add Prometheus Data Source

1. Go to **Configuration → Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Set URL to `http://localhost:9090`
5. Click **Save & Test**

### Import Dashboards

Import community dashboards for instant visualization:

**Node Exporter Full** (Dashboard ID: 1860):
- Complete system metrics
- CPU, memory, disk, network
- Works on all Linux systems

**Raspberry Pi Monitoring** (Dashboard ID: 10578):
- Combines node_exporter + rpi_exporter
- Temperature, voltage, throttling
- Raspberry Pi specific metrics

**Prometheus Stats** (Dashboard ID: 2):
- Monitor Prometheus itself
- Scrape duration, target health
- Storage and performance

### Create Custom Dashboard

```promql
# CPU Usage
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory Usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk Space
(1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes)) * 100

# RPi Temperature
rpi_cpu_temperature_celsius
```

## Prometheus Configuration

### Generated Config Location

- **File**: `/etc/prometheus/prometheus.yml`
- **Auto-generated**: From `templates/prometheus.conf.j2`
- **Validated**: With `promtool check config` before deployment

### Global Settings

```yaml
global:
  scrape_interval: 15s      # How often to scrape targets
  evaluation_interval: 15s  # How often to evaluate rules
  scrape_timeout: 10s       # How long until timeout
  external_labels:
    monitor: 'homelab'
    prometheus_server: 'monitoring-server'
```

### Data Retention

Configured in `group_vars/all.yml`:

```yaml
services:
  data_retention: "2d"  # Keep 2 days of data
```

To change retention:
- Modify `services.data_retention` in `group_vars/all.yml`
- Re-run playbook to update Prometheus

### Storage Location

- **Path**: `/data/prometheus/`
- **Owner**: `prometheus:prometheus`
- **Retention**: Configurable (default: 2 days)

## Alerting (Advanced)

### Add Alert Rules

Create alert rules file:

```bash
ssh user@monitoring-server
sudo nano /etc/prometheus/alerts.yml
```

Example alerts:

```yaml
groups:
  - name: system_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value }}%"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}%"

      - alert: DiskSpaceLow
        expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk usage is {{ $value }}%"

      - alert: RaspberryPiThrottled
        expr: rpi_throttled > 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Raspberry Pi {{ $labels.instance }} is throttled"
          description: "Check power supply and cooling"
```

Update Prometheus config to load alerts:

```yaml
rule_files:
  - "/etc/prometheus/alerts.yml"
```

## Troubleshooting

### Prometheus won't start

Check logs:
```bash
journalctl -u prometheus -f
```

Validate config:
```bash
/usr/local/bin/promtool check config /etc/prometheus/prometheus.yml
```

### Targets show as DOWN

Check firewall on target hosts:
```bash
# Allow node_exporter
sudo ufw allow 9100/tcp

# Allow rpi_exporter
sudo ufw allow 9243/tcp
```

Verify exporter is running:
```bash
systemctl status node_exporter
curl http://localhost:9100/metrics
```

### Grafana can't connect to Prometheus

Check Prometheus is accessible:
```bash
curl http://localhost:9090/api/v1/targets
```

Verify Grafana can resolve localhost:
```bash
docker exec grafana ping localhost
# OR for systemd
sudo -u grafana curl http://localhost:9090
```

### No data in Grafana

1. Check Prometheus is scraping:
   - Go to `http://monitoring-server:9090/targets`
   - Verify targets are UP

2. Check time range in Grafana:
   - Ensure time range includes recent data
   - Default retention is 2 days

3. Verify query:
   - Test query in Prometheus first
   - Then copy to Grafana

## Performance Tuning

### For Large Deployments (50+ hosts)

Increase scrape interval:
```yaml
global:
  scrape_interval: 30s  # Reduce scrape frequency
```

Increase storage:
```yaml
services:
  data_retention: "7d"  # Keep more history
```

### Resource Requirements

**Minimum** (< 10 hosts):
- CPU: 1 core
- RAM: 1 GB
- Disk: 10 GB

**Recommended** (10-50 hosts):
- CPU: 2 cores
- RAM: 2 GB
- Disk: 20 GB

**Large** (50+ hosts):
- CPU: 4 cores
- RAM: 4 GB
- Disk: 50 GB

## Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `monitoring_server_userid` | `prometheus` | System user for Prometheus |
| `monitoring_server_groupid` | `prometheus` | System group for Prometheus |
| `monitoring_server_prometheus_port` | `9090` | Prometheus web UI port |
| `monitoring_server_grafana_port` | `3000` | Grafana web UI port |
| `monitoring_server_prometheus_retention_time` | `{{ services.data_retention }}` | Data retention period |

## Requirements

- Ansible 2.10 or higher
- Target system: Linux (Debian/Ubuntu/Raspbian)
- Architecture: x86_64, aarch64, or armv7l
- Internet connection for downloading binaries
- Hosts to monitor must have exporters installed (`node_exporter`, `rpi_exporter`)

## Dependencies

None. This is a standalone role, but it's designed to work with:
- `node_exporter` role (system metrics)
- `rpi_exporter` role (Raspberry Pi metrics)

## Security Considerations

1. **Change Default Password**: Grafana default is `admin/admin`
2. **Firewall Rules**: Restrict access to ports 9090 and 3000
3. **HTTPS**: Consider adding reverse proxy (nginx/traefik) with SSL
4. **Authentication**: Configure Grafana auth (LDAP, OAuth, etc.)
5. **Network Segmentation**: Keep monitoring on management network

## Common Use Cases

### 1. Homelab Monitoring
Monitor your home server infrastructure:
- Raspberry Pi clusters
- NAS devices
- Media servers
- IoT devices

### 2. Production Monitoring
Enterprise-grade monitoring:
- Web servers
- Databases
- Kubernetes clusters
- Microservices

### 3. IoT Fleet Management
Monitor distributed IoT devices:
- Edge computing nodes
- Sensors and gateways
- Remote installations

## License

MIT

## Author

Part of the Linux-Setup Ansible playbook collection.

## See Also

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Node Exporter Role](../node_exporter/README.md)
- [RPi Exporter Role](../rpi_exporter/README.md)
