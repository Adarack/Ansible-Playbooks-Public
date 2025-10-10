# Security Setup Guide

This guide explains how to set up sensitive configuration files for this Ansible project.

## ⚠️ IMPORTANT SECURITY NOTICE

**NEVER commit sensitive information to version control!**

- Real IP addresses
- SSH private/public keys
- Passwords (encrypted or plaintext)
- Usernames
- Hostnames
- MQTT credentials

## Required Setup Steps

### 1. Create Actual Configuration Files

Copy the example files and customize with your real values:

```bash
# Copy group variables
cp group_vars/all.yml.example group_vars/all.yml

# Copy inventory
cp inventory/hosts.yml.example inventory/hosts.yml

# Customize with your actual values
vim group_vars/all.yml
vim inventory/hosts.yml
```

### 2. Configure Ansible Vault (Recommended)

Encrypt sensitive passwords using Ansible Vault:

```bash
# Create vault password file (add to .gitignore)
echo "your_vault_password" > .vault_pass

# Encrypt the sudo password
echo 'your_actual_sudo_password' | ansible-vault encrypt_string --vault-password-file .vault_pass --stdin-name 'ansible_become_password'

# Encrypt MQTT password
echo 'your_mqtt_password' | ansible-vault encrypt_string --vault-password-file .vault_pass --stdin-name 'password'
```

Replace the plaintext passwords in `group_vars/all.yml` with the encrypted versions.

### 3. SSH Key Setup

```bash
# Generate SSH keys for each user type
ssh-keygen -t ed25519 -f ~/.ssh/pi_key -C "pi@raspberry-infrastructure"
ssh-keygen -t ed25519 -f ~/.ssh/jason_key -C "jason@raspberry-infrastructure"

# Copy public keys to group_vars/all.yml users_list
cat ~/.ssh/pi_key.pub
cat ~/.ssh/jason_key.pub
```

### 4. Inventory Configuration

Update `inventory/hosts.yml` with your actual:
- IP addresses
- Hostnames/comments
- User mappings
- SSH key paths

## File Structure

```
├── .gitignore                    # Protects sensitive files
├── group_vars/
│   ├── all.yml.example          # Template (safe to commit)
│   └── all.yml                  # Real config (ignored by git)
├── inventory/
│   ├── hosts.yml.example        # Template (safe to commit)
│   ├── hosts_improved.yml.example # Advanced template
│   └── hosts.yml                # Real inventory (ignored by git)
└── .vault_pass                  # Vault password (ignored by git)
```

## Verification

Before committing changes:

```bash
# Check what would be committed
git status

# Verify no sensitive files are staged
git diff --cached

# Ensure .gitignore is working
git check-ignore group_vars/all.yml inventory/hosts.yml
```

## Running Playbooks with Vault

```bash
# Using vault password file
ansible-playbook -i inventory/hosts.yml main.yml --vault-password-file .vault_pass

# Using prompt for vault password
ansible-playbook -i inventory/hosts.yml main.yml --ask-vault-pass
```

## Environment-Specific Configurations

For multiple environments, create separate files:

```bash
# Development
group_vars/dev.yml
inventory/dev_hosts.yml

# Production
group_vars/prod.yml
inventory/prod_hosts.yml

# Staging
group_vars/staging.yml
inventory/staging_hosts.yml
```

## Recovery Instructions

If you accidentally commit sensitive data:

1. **Immediately change all exposed credentials**
2. **Remove from git history**:
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch group_vars/all.yml' --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push to remote** (if applicable)
4. **Notify team members** to re-clone the repository

## Ansible Vault Commands Reference

```bash
# Create encrypted file
ansible-vault create secret.yml

# Edit encrypted file
ansible-vault edit group_vars/all.yml

# View encrypted file
ansible-vault view group_vars/all.yml

# Encrypt existing file
ansible-vault encrypt group_vars/all.yml

# Decrypt file
ansible-vault decrypt group_vars/all.yml

# Change vault password
ansible-vault rekey group_vars/all.yml
```