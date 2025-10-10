# Ansible Playbooks Collection

A collection of production-ready Ansible playbook projects for infrastructure automation and configuration management. Each playbook is self-contained with its own inventory, roles, and documentation.

## 📋 Available Playbooks

| Playbook | Description | Primary Use Case |
|----------|-------------|------------------|
| [**Linux-Setup**](./Linux-Setup/) | Multi-platform Linux system configuration | Initial setup of new Linux systems with users, Docker, monitoring |
| [**k3s-cluster**](./k3s-cluster/) | K3s Kubernetes cluster deployment | Deploy lightweight Kubernetes clusters on Raspberry Pi and servers |
| [**UpdateSystem**](./UpdateSystem/) | System package updates and maintenance | Automated updates for Debian, RHEL, Arch systems and Pi-hole |
| [**wyoming-satellite**](./wyoming-satellite/) | Wyoming Satellite voice assistant setup | Deploy voice assistants for Home Assistant with multi-room audio |

## 🚀 Quick Start

### Prerequisites

- **Ansible**: Version 2.10 or higher
- **SSH access**: To target hosts with key-based authentication
- **Python 3**: On both control node and managed hosts

### Installation

```bash
# Install Ansible (Ubuntu/Debian)
sudo apt update
sudo apt install ansible

# Install Ansible (macOS)
brew install ansible

# Verify installation
ansible --version
```

### Using a Playbook

Each playbook is self-contained. Navigate to the playbook directory and follow its README:

```bash
# Example: Linux-Setup
cd Linux-Setup/

# 1. Copy example files and customize
cp inventory/hosts.yml.example inventory/hosts.yml
cp group_vars/all.yml.example group_vars/all.yml

# 2. Edit with your hosts and credentials
nano inventory/hosts.yml
nano group_vars/all.yml

# 3. Run the playbook
ansible-playbook -i inventory/hosts.yml main.yml
```

## 📁 Repository Structure

```
ansible-wip/
├── README.md                    # This file
├── CLAUDE.md                    # AI assistance guidelines
├── .gitignore                   # Repository-wide git ignore
│
├── Linux-Setup/                 # Linux system configuration
│   ├── README.md               # Playbook-specific documentation
│   ├── CLAUDE.md               # Technical details for AI
│   ├── main.yml                # Main playbook
│   ├── ansible.cfg             # Ansible configuration
│   ├── .gitignore              # Sensitive file protection
│   ├── inventory/
│   │   ├── hosts.yml.example   # Example inventory (safe to commit)
│   │   └── hosts.yml           # Your actual inventory (gitignored)
│   ├── group_vars/
│   │   ├── all.yml.example     # Example configuration (safe to commit)
│   │   └── all.yml             # Your actual config (gitignored)
│   └── roles/                  # Ansible roles
│
├── k3s-cluster/                 # K3s Kubernetes deployment
│   ├── README.md
│   ├── CLAUDE.md
│   ├── main.yml
│   └── ...
│
├── UpdateSystem/                # System updates automation
│   ├── README.md
│   ├── CLAUDE.md
│   ├── main.yml
│   └── ...
│
└── wyoming-satellite/           # Voice assistant setup
    ├── README.md
    ├── CLAUDE.md
    ├── main.yml
    └── ...
```

## 🔒 Security

### Protecting Sensitive Data

Each playbook includes:
- **`.gitignore`**: Prevents committing sensitive files
- **`.example` files**: Sanitized templates for `inventory/hosts.yml` and `group_vars/all.yml`
- **Vault support**: Ready for `ansible-vault` encryption

### Before Committing to Git

1. ✅ Never commit `inventory/hosts.yml` or `group_vars/all.yml` directly
2. ✅ Always use `.example` files as templates
3. ✅ Encrypt sensitive variables with `ansible-vault`
4. ✅ Review `.gitignore` in each playbook directory

### Using Ansible Vault

```bash
# Encrypt sensitive variables
echo 'your_password' | ansible-vault encrypt_string --stdin-name 'ansible_become_password'

# Edit encrypted file
ansible-vault edit group_vars/all.yml

# Run playbook with vault
ansible-playbook -i inventory/hosts.yml main.yml --ask-vault-pass
```

## 🎯 Common Tasks

### Check Playbook Syntax

```bash
cd <playbook-directory>
ansible-playbook -i inventory/hosts.yml main.yml --syntax-check
```

### Dry Run (Check Mode)

```bash
ansible-playbook -i inventory/hosts.yml main.yml --check
```

### Run ansible-lint

```bash
ansible-lint main.yml
```

### Target Specific Hosts

```bash
# Target specific group
ansible-playbook -i inventory/hosts.yml main.yml --limit groupname

# Target specific host
ansible-playbook -i inventory/hosts.yml main.yml --limit 10.10.2.50
```

## 🏗️ Architecture & Standards

All playbooks follow consistent standards:

### ✅ Quality Assurance
- **ansible-lint** compliant (production profile)
- **FQCN** (Fully Qualified Collection Names) for all modules
- **Proper error handling** with `failed_when` instead of `ignore_errors`
- **Idempotent** operations (safe to run multiple times)

### ✅ Configuration Management
- **Centralized configuration** in `group_vars/all.yml`
- **Role-based architecture** with clear separation of concerns
- **Variable naming conventions** (role-prefixed variables)
- **DRY principle** (generic, reusable templates)

### ✅ Multi-Platform Support
- **Architectures**: x86_64, ARM64 (aarch64), ARM32 (armv7l)
- **Distributions**: Debian, Ubuntu, RHEL, CentOS, Fedora, Arch Linux
- **Automatic detection** of platform and architecture

## 📚 Documentation

Each playbook includes comprehensive documentation:

- **README.md**: User-facing documentation with quick start guide
- **CLAUDE.md**: Technical documentation for AI assistance and developers
- **Inline comments**: Detailed explanations in playbooks and roles

## 🤝 Contributing

### Adding a New Playbook

1. Create directory structure:
   ```bash
   mkdir NewPlaybook
   cd NewPlaybook
   mkdir -p inventory group_vars roles templates
   ```

2. Copy template files:
   ```bash
   cp ../Linux-Setup/ansible.cfg .
   cp ../Linux-Setup/.gitignore .
   cp ../Linux-Setup/inventory/hosts.yml.example inventory/
   cp ../Linux-Setup/group_vars/all.yml.example group_vars/
   ```

3. Create `main.yml`, `README.md`, and `CLAUDE.md`

4. Customize for your use case

See [CLAUDE.md](./CLAUDE.md) for detailed guidelines.

## 🛠️ Supported Platforms

### Operating Systems
- Debian 10+
- Ubuntu 20.04+
- Raspberry Pi OS (Raspbian)
- RHEL 8+
- CentOS 8+
- Fedora 35+
- Rocky Linux 8+
- Arch Linux

### Architectures
- x86_64 (Intel/AMD 64-bit)
- aarch64 (ARM 64-bit - Raspberry Pi 4/5)
- armv7l (ARM 32-bit - Raspberry Pi 3)

## 📖 Additional Resources

- [Ansible Documentation](https://docs.ansible.com/)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html)
- [Ansible Vault Guide](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [YAML Syntax](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html)

## 📝 License

Each playbook may have its own licensing. Refer to individual playbook directories for details.

## ⚠️ Disclaimer

These playbooks are provided as-is. Always test in a non-production environment before deploying to production systems. Review and understand what each playbook does before running it.

---

**Repository Maintainer**: For questions or issues, refer to individual playbook documentation or CLAUDE.md files.
