# Wyoming Satellite Setup - Ansible Playbook

Automated setup of Wyoming Satellite voice assistants with multi-room audio and intelligent volume ducking.

## What It Does

- **Wyoming Satellite**: Rhasspy voice assistant for Home Assistant
- **Snapcast Client**: Multi-room audio streaming
- **PulseAudio Ducking**: Auto-lower music when voice assistant is active

## Quick Start

```bash
# 1. Configure inventory with your Raspberry Pi IP addresses
vim inventory/hosts.yml

# 2. Configure settings (Home Assistant IP, Snapcast server, audio devices)
vim group_vars/all.yml

# 3. Run playbook
ansible-playbook -i inventory/hosts.yml main.yml
```

## Requirements

### Hardware
- Raspberry Pi 3/4/5
- Microphone (USB or HAT like ReSpeaker)
- Speaker/headphone jack or HDMI audio

### External Services
- **Home Assistant** with Wyoming integration configured
- **Snapcast Server** for multi-room audio

## Key Configuration

Edit `group_vars/all.yml`:

```yaml
# Home Assistant connection
wyoming_satellite_server_host: "192.168.1.10"  # Your HA IP

# Snapcast server
snapcast_client_server_host: "192.168.1.11"    # Your Snapcast IP

# Audio devices (use arecord -L and aplay -L to find yours)
wyoming_satellite_mic_device: "plughw:CARD=seeed2micvoicec,DEV=0"
wyoming_satellite_snd_device: "plughw:CARD=seeed2micvoicec,DEV=0"

# Wake word
wyoming_satellite_wake_word: "ok_nabu"

# Ducking volumes
pulseaudio_ducking_volume: 20          # Volume when assistant active (20%)
pulseaudio_ducking_normal_volume: 100  # Normal music volume (100%)
```

## How Ducking Works

1. Music plays via Snapcast at normal volume (100%)
2. You say wake word "ok nabu"
3. Music volume automatically drops to 20%
4. You give voice command
5. Assistant responds (volume stays at 20%)
6. After response finishes, music returns to 100%

## Finding Audio Devices

On your Raspberry Pi:
```bash
# List microphones
arecord -L

# List speakers
aplay -L

# Test microphone
arecord -D <device> -f S16_LE -r 16000 test.wav

# Test speaker
aplay test.wav
```

Common devices:
- **ReSpeaker 2-Mic HAT**: `plughw:CARD=seeed2micvoicec,DEV=0`
- **ReSpeaker 4-Mic HAT**: `plughw:CARD=seeed4micvoicec,DEV=0`
- **USB Microphone**: `plughw:CARD=Device,DEV=0`

## Verification

After running the playbook:

```bash
# Check services
ssh pi@<raspberry-pi-ip>
systemctl status wyoming-satellite
systemctl status snapclient

# View logs
journalctl -u wyoming-satellite -f

# Test wake word
# Say "ok nabu" and watch logs for detection
```

## Supported Platforms

- ✅ Raspberry Pi OS (Debian-based)
- ✅ Ubuntu on Raspberry Pi
- ✅ Debian on ARM/x86_64

## Project Structure

```
wyoming-satellite/
├── main.yml                       # Main playbook
├── inventory/hosts.yml            # Target hosts
├── group_vars/all.yml             # Configuration
└── roles/
    ├── wyoming_satellite/         # Voice assistant installation
    ├── snapcast_client/           # Multi-room audio client
    └── pulseaudio_ducking/        # Volume ducking scripts
```

## Documentation

See [CLAUDE.md](CLAUDE.md) for comprehensive documentation including:
- Detailed architecture
- All configuration options
- Troubleshooting guide
- Advanced usage

## Safety Features

✅ Idempotent - safe to run multiple times
✅ ansible-lint production compliance
✅ Dedicated user with limited privileges
✅ Service auto-restart on failure
✅ Graceful error handling

## Common Issues

**Wake word not detected**: Check microphone device configuration
**No audio ducking**: Verify Snapcast is using PulseAudio
**Can't connect to Home Assistant**: Check firewall and Wyoming integration
**No music playback**: Verify Snapcast server IP and port

See [CLAUDE.md](CLAUDE.md) troubleshooting section for detailed solutions.
