# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This Ansible playbook automates the setup of Wyoming Satellite voice assistants on Raspberry Pi devices with:
- **ReSpeaker 2-Mics Pi HAT v1/v2** (optional): Hardware drivers and LED control for Seeed ReSpeaker HAT
- **Wyoming Satellite**: Rhasspy's voice assistant satellite for Home Assistant
- **Snapcast Client**: Multi-room audio streaming
- **PulseAudio Ducking**: Automatic volume reduction when voice assistant is active

The playbook integrates these components to create a voice-controlled multi-room audio system with intelligent volume ducking.

## Architecture

- **Main Playbook**: `main.yml` - Orchestrates Wyoming Satellite setup with audio features
- **Inventory**: `inventory/hosts.yml` - Defines Wyoming Satellite hosts (Raspberry Pi devices)
- **Roles Structure**: Four specialized roles:
  - `respeaker_2mic_hat`: ReSpeaker 2-Mics Pi HAT driver (supports v1 and v2 with auto-detection)
  - `wyoming_satellite`: Wyoming Satellite installation and configuration
  - `snapcast_client`: Snapcast client for multi-room audio
  - `pulseaudio_ducking`: PulseAudio event scripts for volume ducking

## Supported Platforms

### Hardware
- **Raspberry Pi 3/4/5** (primary target)
- **x86_64 systems** (with appropriate audio hardware)
- **ARM-based devices** with audio capabilities

### Software
- **Debian/Ubuntu**: Raspberry Pi OS, Ubuntu
- **Audio Hardware**: USB microphones, HAT microphones (ReSpeaker, etc.)

### Required Components (External)
- **Home Assistant** with Wyoming integration
- **Snapcast Server** (for multi-room audio)

## Common Commands

### Running the Playbook

```bash
# Setup Wyoming Satellite on all hosts
ansible-playbook -i inventory/hosts.yml main.yml

# Setup specific satellite
ansible-playbook -i inventory/hosts.yml main.yml --limit 10.10.2.50

# Check mode (dry run)
ansible-playbook -i inventory/hosts.yml main.yml --check

# Only install Wyoming Satellite (skip Snapcast)
ansible-playbook -i inventory/hosts.yml main.yml -e "role_enabled={wyoming_satellite: true, snapcast_client: false, pulseaudio_ducking: false}"
```

### Validation

```bash
# Syntax check
ansible-playbook -i inventory/hosts.yml main.yml --syntax-check

# ansible-lint
ansible-lint main.yml

# Lint specific role
ansible-lint roles/wyoming_satellite/
ansible-lint roles/snapcast_client/
ansible-lint roles/pulseaudio_ducking/
```

### Service Management

```bash
# Check Wyoming Satellite status
ansible wyoming_satellites -i inventory/hosts.yml -m shell -a "systemctl status wyoming-satellite" -b

# Check Snapcast client status
ansible wyoming_satellites -i inventory/hosts.yml -m shell -a "systemctl status snapclient" -b

# View Wyoming Satellite logs
ansible wyoming_satellites -i inventory/hosts.yml -m shell -a "journalctl -u wyoming-satellite -n 50" -b

# Restart services
ansible wyoming_satellites -i inventory/hosts.yml -m systemd -a "name=wyoming-satellite state=restarted" -b
```

### Audio Device Discovery

```bash
# List audio devices on remote host
ansible wyoming_satellites -i inventory/hosts.yml -m shell -a "aplay -L"
ansible wyoming_satellites -i inventory/hosts.yml -m shell -a "arecord -L"

# List PulseAudio devices
ansible wyoming_satellites -i inventory/hosts.yml -m shell -a "pactl list short sinks"
ansible wyoming_satellites -i inventory/hosts.yml -m shell -a "pactl list short sources"
```

## Configuration

### Centralized Configuration (group_vars/all.yml)

All behavior is controlled through centralized variables organized by role:

#### Wyoming Satellite Settings

```yaml
# Installation
wyoming_satellite_install_dir: "/opt/wyoming-satellite"
wyoming_satellite_user: "wyoming"

# Repository
wyoming_satellite_repo_url: "https://github.com/rhasspy/wyoming-satellite.git"

# Features
wyoming_satellite_install_vad: true      # Voice Activity Detection
wyoming_satellite_install_noise: true   # Audio enhancement

# Connection (change to your Home Assistant IP)
wyoming_satellite_server_host: "127.0.0.1"
wyoming_satellite_server_port: 10300

# Audio devices (adjust for your hardware)
wyoming_satellite_mic_device: "plughw:CARD=seeed2micvoicec,DEV=0"
wyoming_satellite_snd_device: "plughw:CARD=seeed2micvoicec,DEV=0"

# Wake word
wyoming_satellite_wake_word: "ok_nabu"  # ok_nabu, hey_jarvis, hey_mycroft, alexa

# Audio enhancement
wyoming_satellite_noise_suppression: 2  # 0-4
wyoming_satellite_auto_gain: 15         # 0-31
```

#### Snapcast Client Settings

```yaml
# Server (change to your Snapcast server IP)
snapcast_client_server_host: "127.0.0.1"
snapcast_client_server_port: 1704

# Client
snapcast_client_host_id: "{{ ansible_hostname }}"
snapcast_client_use_pulseaudio: true  # Required for ducking

# Raspberry Pi audio
snapcast_client_rpi_audio_output: 1  # 1=3.5mm, 2=HDMI, 0=auto
```

#### PulseAudio Ducking Settings

```yaml
# Volume levels (0-100)
pulseaudio_ducking_volume: 20          # Ducked volume (20%)
pulseaudio_ducking_normal_volume: 100  # Normal volume (100%)
```

## Role Details

### wyoming_satellite Role

**Purpose**: Install and configure Wyoming Satellite voice assistant

**Key Features**:
- Clones Wyoming Satellite from GitHub
- Creates dedicated user (`wyoming`)
- Installs optional VAD and noise reduction
- Configures systemd service
- Sets up event command hooks

**Files**:
- `tasks/main.yml`: Installation and service setup
- `templates/wyoming-satellite.service.j2`: Systemd service template
- `defaults/main.yml`: Default configuration
- `meta/main.yml`: Role metadata

**Key Variables** (prefixed with `wyoming_satellite_`):
- `wyoming_satellite_server_host`: Home Assistant IP
- `wyoming_satellite_mic_device`: Microphone ALSA device
- `wyoming_satellite_wake_word`: Wake word to use
- `wyoming_satellite_install_vad`: Enable Voice Activity Detection
- `wyoming_satellite_event_dir`: Directory for event hooks (ducking)

### snapcast_client Role

**Purpose**: Install Snapcast client for multi-room audio streaming

**Key Features**:
- Adds Snapcast official repository
- Installs Snapcast client package
- Configures client connection to server
- Sets up PulseAudio integration
- Configures Raspberry Pi audio output

**Files**:
- `tasks/main.yml`: Installation and configuration
- `templates/snapclient.j2`: Client configuration template
- `defaults/main.yml`: Default settings
- `handlers/main.yml`: Service restart handlers

**Key Variables** (prefixed with `snapcast_client_`):
- `snapcast_client_server_host`: Snapcast server IP
- `snapcast_client_use_pulseaudio`: Enable PulseAudio (required for ducking)
- `snapcast_client_rpi_audio_output`: Raspberry Pi output selection

### respeaker_2mic_hat Role

**Purpose**: Install ReSpeaker 2-Mics Pi HAT v1 drivers and LED control

**Key Features**:
- Installs Seeed voice card drivers (HinTak fork for latest kernel support)
- Configures I2S audio interface in boot config (non-destructive)
- Sets up APA102 LED control service for visual feedback
- Automatic reboot after driver installation
- Idempotent - safe to run multiple times

**Files**:
- `tasks/main.yml`: Main driver installation workflow
- `tasks/configure_boot.yml`: I2S boot configuration (uses lineinfile, not destructive)
- `tasks/led_service.yml`: LED control service setup
- `templates/led_control.py.j2`: Python LED driver for Wyoming events
- `templates/respeaker-led.service.j2`: Systemd service for LEDs
- `defaults/main.yml`: Default configuration
- `handlers/main.yml`: Reboot and service restart handlers

**Key Variables** (prefixed with `respeaker_2mic_hat_`):
- `respeaker_2mic_hat_driver_repo`: Driver repository URL (HinTak fork)
- `respeaker_2mic_hat_enable_led_service`: Enable LED visual feedback
- `respeaker_2mic_hat_configure_boot`: Enable I2S in boot config
- `respeaker_2mic_hat_reboot_after_install`: Reboot after installation

**Important Notes**:
- **Disabled by default** - Set `role_enabled.respeaker_2mic_hat: true` in group_vars
- Supports **both v1 and v2 hardware** - driver auto-detects which version you have
- Uses non-destructive boot config (lineinfile, not template overwrite)
- Requires reboot for kernel module to load
- Device name: `seeed2micvoicec` (same for both v1 and v2)

### pulseaudio_ducking Role

**Purpose**: Configure automatic volume ducking when voice assistant is active

**Key Features**:
- Creates event scripts for Wyoming Satellite hooks
- Lowers volume when wake word detected
- Lowers volume when assistant is speaking
- Restores volume after interaction
- Supports Snapcast audio streams

**Files**:
- `tasks/main.yml`: Event script installation
- `templates/*.sh.j2`: Event hook scripts
  - `detect.sh`: Duck on wake word detection
  - `streaming_started.sh`: Duck when assistant speaks
  - `streaming_stopped.sh`: Restore volume
  - `played.sh`: Restore after playback
- `defaults/main.yml`: Ducking settings

**Event Scripts**:
Wyoming Satellite calls these scripts during voice interactions:
1. **detect** → Duck volume when wake word heard
2. **detection** → Keep ducked during voice command
3. **streaming_started** → Duck when assistant responds
4. **synthesize** → Keep ducked during speech synthesis
5. **played** → Restore volume after assistant finishes

**Key Variables** (prefixed with `pulseaudio_ducking_`):
- `pulseaudio_ducking_volume`: Ducked volume level (default: 20%)
- `pulseaudio_ducking_normal_volume`: Fallback volume if original cannot be restored (default: 100%)

**Volume Restoration**:
- Scripts now **save and restore original volume** before ducking
- If music was at 75%, it returns to 75% (not 100%)
- State stored in `/run/user/UID/wyoming-volume-state`
- Fallback to `pulseaudio_ducking_normal_volume` only if state file is lost

## Integration Flow

### 1. Wyoming Satellite Setup
```
Raspberry Pi → Wyoming Satellite → Home Assistant
                    ↓
            Event Hooks (ducking scripts)
```

### 2. Audio Ducking Flow
```
Wake Word Detected
    ↓
detect.sh → Duck Snapcast volume to 20%
    ↓
User speaks command
    ↓
streaming_started.sh → Keep volume ducked
    ↓
Assistant responds
    ↓
played.sh → Restore volume to original level (saved state)
```

### 3. Multi-Room Audio
```
Music Source → Snapcast Server → Network → Snapcast Client (on Pi)
                                              ↓
                                         PulseAudio
                                              ↓
                                         Speaker Output
                                              ↑
                                      (Volume controlled by ducking)
```

## Setup Workflow

### Prerequisites
1. **Home Assistant** configured with Wyoming integration
2. **Snapcast Server** running and accessible
3. **Raspberry Pi** with microphone/speaker hardware
4. **Network connectivity** between components

### Installation Steps

1. **Configure Inventory**
```yaml
# inventory/hosts.yml
wyoming_satellites:
  hosts:
    10.10.2.50:  # Your Raspberry Pi IP
```

2. **Configure Settings**
```yaml
# group_vars/all.yml
wyoming_satellite_server_host: "192.168.1.10"  # Home Assistant IP
snapcast_client_server_host: "192.168.1.11"    # Snapcast server IP
wyoming_satellite_mic_device: "plughw:CARD=seeed2micvoicec,DEV=0"
```

3. **Run Playbook**
```bash
ansible-playbook -i inventory/hosts.yml main.yml
```

4. **Verify Services**
```bash
# On the Raspberry Pi:
systemctl status wyoming-satellite
systemctl status snapclient
pactl list short sink-inputs  # Check audio streams
```

5. **Test Voice Assistant**
- Say wake word: "ok nabu"
- Verify music volume ducks
- Give voice command
- Verify volume restores after response

## Audio Device Configuration

### Finding Audio Devices

On the target Raspberry Pi:
```bash
# List all playback devices
aplay -L

# List all recording devices
arecord -L

# Test microphone
arecord -D <device> -f S16_LE -r 16000 test.wav

# Test speaker
aplay -D <device> test.wav
```

### Common Device Names

**ReSpeaker 2-Mic HAT**:
```yaml
wyoming_satellite_mic_device: "plughw:CARD=seeed2micvoicec,DEV=0"
wyoming_satellite_snd_device: "plughw:CARD=seeed2micvoicec,DEV=0"
```

**ReSpeaker 4-Mic HAT**:
```yaml
wyoming_satellite_mic_device: "plughw:CARD=seeed4micvoicec,DEV=0"
wyoming_satellite_snd_device: "plughw:CARD=seeed4micvoicec,DEV=0"
```

**USB Microphone**:
```yaml
wyoming_satellite_mic_device: "plughw:CARD=Device,DEV=0"
```

**Raspberry Pi Built-in**:
```yaml
wyoming_satellite_snd_device: "plughw:CARD=Headphones,DEV=0"
```

## Quality Assurance

- ✅ **ansible-lint**: All roles pass production-level linting
- ✅ **FQCN compliance**: All modules use Fully Qualified Collection Names
- ✅ **Variable naming**: Role variables properly prefixed
- ✅ **Error handling**: Proper error handling and changed_when conditions
- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Service management**: Systemd integration with proper dependencies

## Troubleshooting

### Wyoming Satellite Issues

**Service won't start**:
```bash
# Check logs
journalctl -u wyoming-satellite -n 100 -f

# Verify Python environment
/opt/wyoming-satellite/.venv/bin/python --version

# Test manually
cd /opt/wyoming-satellite
script/run --help
```

**Audio device not found**:
```bash
# List devices
arecord -L
aplay -L

# Update group_vars/all.yml with correct device names
```

**Can't connect to Home Assistant**:
```bash
# Test connectivity
telnet <homeassistant_ip> 10300

# Check firewall
sudo ufw status

# Verify Home Assistant Wyoming integration is configured
```

### Snapcast Issues

**Client not connecting**:
```bash
# Check status
systemctl status snapclient

# Verify server connectivity
telnet <snapcast_server_ip> 1704

# Check configuration
cat /etc/default/snapclient
```

**No audio output**:
```bash
# Test PulseAudio
pactl list short sinks
pactl list short sink-inputs

# Check Snapcast sink
pactl list sinks | grep snapcast

# Verify Raspberry Pi audio output
amixer cset numid=3 1  # Force 3.5mm jack
```

### Ducking Issues

**Volume not ducking**:
```bash
# Check event scripts exist
ls -la /opt/wyoming-satellite/events/

# Test event script manually
/opt/wyoming-satellite/events/detect.sh

# Check PulseAudio sink inputs
pactl list short sink-inputs | grep snapcast

# Verify Wyoming Satellite event command enabled
grep event-dir /etc/systemd/system/wyoming-satellite.service
```

**Volume stuck at low level**:
```bash
# Manually restore
pactl set-sink-input-volume <sink-id> 100%

# Or restart snapclient
systemctl restart snapclient
```

## Security Notes

- **Credentials**: Store `ansible_become_password` encrypted with ansible-vault
- **SSH keys**: Use key-based authentication
- **Network security**: Wyoming and Snapcast traffic is unencrypted (use VPN/firewall)
- **User permissions**: Wyoming user has limited privileges
- **Audio group**: Wyoming user added to audio and pulse-access groups

## Advanced Configuration

### Multiple Snapcast Servers

To use different Snapcast servers per host:
```yaml
# host_vars/satellite1.yml
snapcast_client_server_host: "192.168.1.10"

# host_vars/satellite2.yml
snapcast_client_server_host: "192.168.1.11"
```

### Custom Wake Words

Available wake words:
- `ok_nabu` (default)
- `hey_jarvis`
- `hey_mycroft`
- `alexa`

### Disabling Components

```yaml
# Disable ducking but keep Snapcast
role_enabled:
  wyoming_satellite: true
  snapcast_client: true
  pulseaudio_ducking: false
```

## ReSpeaker 2-Mics Pi HAT Setup

### Hardware Auto-Detection

**Good news!** You don't need to know which version you have. The HinTak seeed-voicecard driver automatically detects whether you have v1 or v2 hardware and installs the correct drivers.

### Enabling the Role

The ReSpeaker role is **disabled by default** to avoid running on systems without the hardware.

```yaml
# group_vars/all.yml
role_enabled:
  respeaker_2mic_hat: true  # Enable for ReSpeaker (auto-detects v1 or v2)
```

### Hardware Installation

1. **Mount the HAT** onto Raspberry Pi GPIO header (ensure proper alignment)
2. **Power off** Raspberry Pi before installation
3. **Run the playbook** - it will install drivers and reboot automatically

### Driver Installation Process

The role performs these steps:
1. Installs required packages (git, python3-pip, audio libraries)
2. Clones HinTak/seeed-voicecard repository (maintained fork supporting both v1 and v2)
3. Runs driver installation script (auto-detects hardware version)
4. Configures I2S in `/boot/firmware/config.txt` (non-destructive)
5. Sets up LED control service
6. Reboots system

**Note**: The installation script automatically detects whether you have v1 or v2 hardware and installs the appropriate drivers.

### Post-Installation Verification

```bash
# Check audio devices (after reboot)
arecord -l  # Should show "seeed-2mic-voicecard"
aplay -l

# Check ALSA mixer
alsamixer  # Select "seeed-2mic-voicecard"

# Test microphone
arecord -D plughw:CARD=seeed2micvoicec,DEV=0 -f S16_LE -r 16000 test.wav
aplay test.wav

# Check LED service
systemctl status respeaker-led.service
```

### Device Configuration

After ReSpeaker installation, update Wyoming Satellite to use the hardware:

```yaml
# group_vars/all.yml
wyoming_satellite_mic_device: "plughw:CARD=seeed2micvoicec,DEV=0"
wyoming_satellite_snd_device: "plughw:CARD=seeed2micvoicec,DEV=0"
```

### LED Visual Feedback

The role includes APA102 LED control service:
- **3 RGB LEDs** on the HAT
- Controlled via SPI interface
- Service: `respeaker-led.service`
- Script: `/opt/respeaker-leds/led_control.py`

The LED script is currently a placeholder - it can be enhanced to integrate with Wyoming Satellite events for visual feedback during wake word detection and voice interactions.

### Troubleshooting

**Driver not loading after reboot:**
```bash
# Check kernel module
lsmod | grep snd_soc_seeed

# Check boot config
grep i2s /boot/firmware/config.txt

# Reinstall drivers
cd /tmp/seeed-voicecard
sudo ./install.sh
sudo reboot
```

**Audio device not appearing:**
```bash
# Check if I2S is enabled
dtparam i2s

# Manually load module
sudo modprobe snd_soc_seeed_voicecard

# Check dmesg for errors
dmesg | grep -i seeed
```

**LEDs not working:**
```bash
# Check SPI is enabled
ls -l /dev/spidev*

# Check LED service
journalctl -u respeaker-led.service -n 50

# Test SPI manually
sudo python3 -c "import spidev; print('SPI OK')"
```

## Related Documentation

- [Wyoming Satellite GitHub](https://github.com/rhasspy/wyoming-satellite)
- [Snapcast Documentation](https://github.com/badaix/snapcast)
- [PulseAudio Documentation](https://www.freedesktop.org/wiki/Software/PulseAudio/)
- [Home Assistant Wyoming Integration](https://www.home-assistant.io/integrations/wyoming/)
- [ReSpeaker 2-Mics Pi HAT v1 Wiki](https://wiki.seeedstudio.com/ReSpeaker_2_Mics_Pi_HAT_Raspberry/)
- [ReSpeaker 2-Mics Pi HAT v2 Wiki](https://wiki.seeedstudio.com/respeaker_2_mics_pi_hat_raspberry_v2/)
- [HinTak Seeed-Voicecard Repository](https://github.com/HinTak/seeed-voicecard)
