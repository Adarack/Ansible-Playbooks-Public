# RPi Exporter Role

Ansible role for installing and configuring [Raspberry Pi Exporter](https://github.com/lukasmalkmus/rpi_exporter) for Raspberry Pi hardware metrics collection.

## Overview

This role installs the Raspberry Pi Exporter on ARM-based Raspberry Pi systems, providing detailed hardware metrics including temperature, voltage, clock speeds, and system information to Prometheus.

## Features

- ✅ **Latest Version**: Automatically installs rpi_exporter v0.8.0
- ✅ **ARM Architecture Support**: Supports ARM64 (aarch64) and ARM32 (armv7l)
- ✅ **x86_64 Skip Logic**: Gracefully skips installation on non-ARM systems
- ✅ **Centralized Configuration**: Version and settings managed in `group_vars/all.yml`
- ✅ **Security Hardening**: Systemd service with security restrictions
- ✅ **GPU Temperature**: Automatic video group access for GPU metrics
- ✅ **Health Checks**: Automatic verification that metrics endpoint is responding

## Supported Platforms

### ✅ Supported (ARM-based Raspberry Pi)
- Raspberry Pi 4 (ARM64 / aarch64)
- Raspberry Pi 3 (ARM32 / armv7l)
- Raspberry Pi 2 (ARM32 / armv7l)
- Raspberry Pi Zero 2 W (ARM64 / aarch64)
- Raspberry Pi 5 (ARM64 / aarch64)

### ❌ Not Supported
- x86_64 systems (Intel/AMD processors)
- Non-Raspberry Pi ARM boards (may work but untested)

The role will automatically skip installation on non-ARM architectures.

## Default Configuration

The role comes with sensible defaults in `defaults/main.yml`:

```yaml
rpi_exporter_port: 9243
rpi_exporter_video_group_access: true  # Required for GPU temperature
rpi_exporter_extra_args: ""
```

## Usage

### Basic Usage

Enable the role in `group_vars/all.yml`:

```yaml
role_enabled:
  rpi_exporter: true

software_versions:
  rpi_exporter: "0.8.0"
```

Then run the playbook:

```bash
ansible-playbook -i inventory/hosts.yml main.yml --limit raspberry_pi
```

### Custom Port

Override the default port in `group_vars/all.yml`:

```yaml
rpi_exporter_port: 9244
```

### Disable GPU Temperature Monitoring

If you don't need GPU metrics or want to remove video group access:

```yaml
rpi_exporter_video_group_access: false
```

**Note**: Without video group access, GPU temperature metrics will not be available.

### Additional CLI Arguments

Pass extra command-line arguments:

```yaml
rpi_exporter_extra_args: "--log.level=debug --log.format=json"
```

## Multi-Architecture Support

The role automatically detects the system architecture and:
- **ARM64/ARM32**: Downloads and installs the appropriate binary
- **x86_64**: Displays skip message and gracefully exits

Architecture mapping in `group_vars/all.yml`:

```yaml
architecture_mapping:
  "x86_64":
    rpi_exporter: "NOT_AVAILABLE"  # Skipped on x86_64
  "aarch64":
    rpi_exporter: "linux-arm64"    # Raspberry Pi 4, Zero 2W, Pi 5
  "armv7l":
    rpi_exporter: "linux-armv7"    # Raspberry Pi 2, 3
```

## Systemd Service

The role creates a hardened systemd service at `/etc/systemd/system/rpi_exporter.service`:

```ini
[Unit]
Description=Prometheus Raspberry Pi Exporter
Documentation=https://github.com/lukasmalkmus/rpi_exporter
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=rpi_exporter
Group=rpi_exporter
SupplementaryGroups=video
ExecStart=/usr/local/bin/rpi_exporter --web.listen-address=:9243
Restart=on-failure
RestartSec=5s
TimeoutStopSec=20s
SendSIGKILL=no

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

## Metrics Provided

RPi Exporter provides detailed Raspberry Pi hardware metrics:

### CPU Metrics
- **rpi_cpu_clock_hertz** - CPU clock frequency
- **rpi_cpu_temperature_celsius** - CPU temperature

### GPU Metrics (requires video group)
- **rpi_gpu_clock_hertz** - GPU clock frequency
- **rpi_gpu_temperature_celsius** - GPU temperature
- **rpi_gpu_memory_bytes** - GPU memory allocation

### Voltage Metrics
- **rpi_voltage_volts{circuit="core"}** - Core voltage
- **rpi_voltage_volts{circuit="sdram_c"}** - SDRAM controller voltage
- **rpi_voltage_volts{circuit="sdram_i"}** - SDRAM I/O voltage
- **rpi_voltage_volts{circuit="sdram_p"}** - SDRAM physical voltage

### System Information
- **rpi_info** - Raspberry Pi model, firmware, revision
- **rpi_up** - Exporter health (always 1)

### Throttle/Under-Voltage Detection
- **rpi_throttled** - Current throttle state
- **rpi_throttled_since** - Historical throttle events

## Verification

After installation, verify rpi_exporter is running:

```bash
# Check service status
systemctl status rpi_exporter

# Test metrics endpoint
curl http://localhost:9243/metrics

# View specific metrics
curl -s http://localhost:9243/metrics | grep rpi_cpu_temperature
curl -s http://localhost:9243/metrics | grep rpi_throttled
```

## Prometheus Integration

Add RPi Exporter targets to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'raspberry_pi'
    static_configs:
      - targets:
          - 'rpi1:9243'
          - 'rpi2:9243'
          - 'rpi3:9243'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
```

## Grafana Dashboards

Use these community Grafana dashboards for visualization:

- **Raspberry Pi Monitoring** - Dashboard ID: 10578
- **RPi Exporter Full** - Dashboard ID: 13729

Or create custom panels:

```promql
# CPU Temperature
rpi_cpu_temperature_celsius

# Throttle Detection
rpi_throttled > 0

# CPU Clock Speed
rpi_cpu_clock_hertz / 1000000
```

## Understanding Throttle States

The `rpi_throttled` metric is a bitmask indicating various throttle conditions:

| Bit | Value | Meaning |
|-----|-------|---------|
| 0 | 1 | Under-voltage detected |
| 1 | 2 | ARM frequency capped |
| 2 | 4 | Currently throttled |
| 3 | 8 | Soft temperature limit active |
| 16 | 65536 | Under-voltage has occurred since boot |
| 17 | 131072 | ARM frequency capping has occurred |
| 18 | 262144 | Throttling has occurred |
| 19 | 524288 | Soft temperature limit has occurred |

Alert if `rpi_throttled > 0` to detect power or thermal issues.

## Troubleshooting

### Service won't start

Check systemd journal:
```bash
journalctl -u rpi_exporter -f
```

### No GPU metrics

Ensure user is in video group:
```bash
groups rpi_exporter
# Should show: rpi_exporter video
```

Verify video group access is enabled:
```yaml
rpi_exporter_video_group_access: true
```

### Metrics endpoint unreachable

Verify port and firewall:
```bash
# Check if listening
ss -tulpn | grep 9243

# Check firewall (if enabled)
sudo ufw allow 9243/tcp
```

### Role skips on x86_64

This is expected behavior. RPi Exporter only works on Raspberry Pi (ARM architecture):

```
TASK [Display RPi Exporter skip message for x86_64]
ok: [server] => {
    "msg": "Skipping RPi Exporter installation - not available for x86_64 architecture (ARM only)"
}
```

Use `node_exporter` instead for x86_64 systems.

## Alerting Examples

Example Prometheus alerts for Raspberry Pi monitoring:

```yaml
groups:
  - name: raspberry_pi_alerts
    rules:
      - alert: RaspberryPiHighTemperature
        expr: rpi_cpu_temperature_celsius > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Raspberry Pi {{ $labels.instance }} CPU temperature is high"
          description: "CPU temperature is {{ $value }}°C"

      - alert: RaspberryPiThrottled
        expr: rpi_throttled > 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Raspberry Pi {{ $labels.instance }} is throttled"
          description: "Throttle state: {{ $value }} (check power supply or cooling)"

      - alert: RaspberryPiUnderVoltage
        expr: (rpi_throttled & 1) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Raspberry Pi {{ $labels.instance }} under-voltage detected"
          description: "Power supply may be insufficient (use official 5V 3A adapter)"
```

## Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `rpi_exporter_port` | `9243` | Port for metrics endpoint |
| `rpi_exporter_userid` | `rpi_exporter` | System user for service |
| `rpi_exporter_groupid` | `rpi_exporter` | System group for service |
| `rpi_exporter_video_group_access` | `true` | Add user to video group for GPU metrics |
| `rpi_exporter_extra_args` | `""` | Additional CLI arguments |

## Requirements

- Ansible 2.10 or higher
- Target system: **Raspberry Pi** (ARM architecture only)
- Architecture: aarch64 or armv7l
- Internet connection for downloading binaries

## Dependencies

None. This is a standalone role.

## Performance Notes

RPi Exporter is very lightweight:
- **Memory**: ~5-10 MB
- **CPU**: Negligible (<1%)
- **Scrape Interval**: Recommended 15-30 seconds

## Common Use Cases

### 1. Temperature Monitoring
Monitor CPU/GPU temperature to prevent thermal throttling:
```promql
avg_over_time(rpi_cpu_temperature_celsius[5m]) > 75
```

### 2. Power Supply Issues
Detect under-voltage from inadequate power supplies:
```promql
rpi_throttled & 1
```

### 3. Performance Monitoring
Track clock speeds for performance analysis:
```promql
rpi_cpu_clock_hertz / 1000000  # MHz
```

### 4. Fleet Management
Monitor entire Raspberry Pi fleet from single Prometheus instance.

## License

MIT

## Author

Part of the Linux-Setup Ansible playbook collection.

## See Also

- [RPi Exporter Documentation](https://github.com/lukasmalkmus/rpi_exporter)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Raspberry Pi vcgencmd](https://www.raspberrypi.org/documentation/computers/os.html#vcgencmd)
- [Understanding Throttle States](https://github.com/raspberrypi/documentation/blob/develop/documentation/asciidoc/computers/os/using-gpio.adoc)
