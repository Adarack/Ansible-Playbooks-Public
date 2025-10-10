# Prepare for Public Git - Action Summary

**Status**: Your repository is almost ready for public release! ✅

## 📋 What's Already Done

✅ **Root-level files created**:
- `README.md` - Comprehensive repository documentation
- `CLAUDE.md` - AI assistance guidelines
- `.gitignore` - Repository-wide ignore patterns
- `LICENSE` - MIT License
- `SECURITY.md` - Security policy and vulnerability reporting
- `PRE_COMMIT_CHECKLIST.md` - Detailed security checklist
- `verify-security.sh` - Automated security verification script

✅ **All playbooks have**:
- `.gitignore` files (protect sensitive data)
- `group_vars/all.yml.example` (safe template files)
- `inventory/hosts.yml.example` (safe template files)

## ⚠️ CRITICAL: What You MUST Do Before Pushing

### 1. Remove Plaintext Passwords

**Linux-Setup/group_vars/all.yml contains:**
- Line 3: `ansible_become_password: "REDACTED"`
- Line 124: `password: "REDACTED"` (MQTT)

**Action Required:**
```bash
cd /home/jason/Documents/ansible/ansible-wip/Linux-Setup

# Backup your actual config (keep locally)
cp group_vars/all.yml group_vars/all.yml.PRIVATE

# Replace with example template
cp group_vars/all.yml.example group_vars/all.yml

# Manually add back any NON-SENSITIVE customizations from .PRIVATE file
# Do NOT copy passwords - use placeholders like "YOUR_PASSWORD_HERE"
```

### 2. Check Other Playbooks

**Verify no passwords in:**
- `UpdateSystem/group_vars/all.yml`
- `k3s-cluster/group_vars/all.yml`
- `wyoming-satellite/group_vars/all.yml`

```bash
cd /home/jason/Documents/ansible/ansible-wip

# Search for potential passwords
grep -r "password.*=" UpdateSystem/group_vars/all.yml k3s-cluster/group_vars/all.yml wyoming-satellite/group_vars/all.yml | grep -v "YOUR_" | grep -v "example"
```

### 3. Decide on IP Address Strategy

Your files contain `10.10.2.x` IP addresses.

**Options:**
- **A**: Leave them (okay if you don't mind exposing your network scheme)
- **B**: Replace with example IPs (`192.168.1.x` or use `example.com`)
- **C**: Document that users should use the `.example` files

**Recommendation**: Keep IP addresses in `.example` files as examples, but your actual `hosts.yml` should be gitignored anyway.

### 4. SSH Public Keys

Your `all.yml` contains SSH public keys. **This is safe** - public keys are meant to be public. No action needed unless you want to use example keys instead.

## 🚀 Step-by-Step: Publishing to Git

### Step 1: Initialize Git Repository (if not already done)

```bash
cd /home/jason/Documents/ansible/ansible-wip

# Initialize git if needed
git init

# Set up remote (replace with your GitHub repo URL)
git remote add origin https://github.com/YOUR_USERNAME/ansible-playbooks.git
```

### Step 2: Run Security Verification

```bash
cd /home/jason/Documents/ansible/ansible-wip

# Run automated security check
./verify-security.sh
```

This will check for:
- Hardcoded passwords
- Vault password files
- SSH private keys
- Accidentally tracked sensitive files

### Step 3: Review Changes

```bash
# See what will be committed
git status

# Review the diff
git diff

# CRITICAL: Verify NO passwords or tokens appear in the diff!
```

### Step 4: Stage and Commit

```bash
cd /home/jason/Documents/ansible/ansible-wip

# Add all files (gitignore will protect sensitive ones)
git add .

# Verify only safe files are staged
git status

# Should NOT see:
# - group_vars/all.yml (without .example)
# - inventory/hosts.yml (without .example)
# - .vault_pass or similar

# Commit
git commit -m "Initial commit: Ansible playbooks collection

- Linux-Setup: Multi-platform Linux system configuration
- UpdateSystem: System package updates and maintenance
- k3s-cluster: K3s Kubernetes cluster deployment
- wyoming-satellite: Wyoming Satellite voice assistant setup

Includes comprehensive documentation and security best practices."
```

### Step 5: Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

### Step 6: Configure GitHub Repository

After pushing, on GitHub:

1. **Add Description**: "Production-ready Ansible playbooks for Linux setup, K3s clusters, updates, and voice assistants"

2. **Add Topics**:
   - ansible
   - automation
   - devops
   - infrastructure-as-code
   - raspberry-pi
   - kubernetes
   - linux
   - homelab

3. **Enable Security Features**:
   - Settings → Security → Enable "Dependabot alerts"
   - Settings → Security → Enable "Secret scanning"

4. **Create README Badge** (optional):
   - Add ansible-lint badge
   - Add license badge

## 🔒 Security Checklist Summary

Before pushing, verify:

- [ ] No plaintext passwords in any `group_vars/all.yml` (use `.example` files)
- [ ] No `.vault_pass` or similar files in repository
- [ ] No SSH private keys (`.pem`, `id_rsa`, etc.)
- [ ] Actual config files are gitignored (`all.yml`, `hosts.yml`)
- [ ] Example files exist and have placeholder values
- [ ] `./verify-security.sh` passes without errors
- [ ] `git status` shows no sensitive files staged
- [ ] `git diff --cached` contains no passwords/tokens
- [ ] Reviewed `PRE_COMMIT_CHECKLIST.md`

## 📝 After Publishing

### Update Your Local Environment

After publishing, your local environment should use actual config files:

```bash
# Linux-Setup example
cd Linux-Setup

# Restore your actual config (from backup or recreate)
cp group_vars/all.yml.PRIVATE group_vars/all.yml  # If you made a backup
# OR
cp group_vars/all.yml.example group_vars/all.yml  # Then edit with real values

# Verify it's gitignored
git status  # Should NOT show all.yml
```

### For New Users Cloning Your Repo

They will need to:

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/ansible-playbooks.git
cd ansible-playbooks/Linux-Setup

# Copy example files
cp group_vars/all.yml.example group_vars/all.yml
cp inventory/hosts.yml.example inventory/hosts.yml

# Edit with their own values
nano group_vars/all.yml
nano inventory/hosts.yml

# Run playbook
ansible-playbook -i inventory/hosts.yml main.yml
```

## 🆘 Emergency: Accidentally Committed a Secret

If you commit and push a password:

1. **Immediately rotate the password** (change it everywhere)
2. **Do NOT just delete the file** - it's still in git history
3. **Use BFG Repo-Cleaner or git filter-branch**:
   ```bash
   # Install BFG Repo-Cleaner
   brew install bfg  # or download from https://rtyley.github.io/bfg-repo-cleaner/

   # Remove passwords from all history
   bfg --replace-text passwords.txt  # Create passwords.txt with passwords to remove

   # Force push cleaned history
   git push --force
   ```
4. **Notify anyone who cloned the repo** to re-clone

## 📚 Quick Reference Commands

```bash
# Verify security before committing
./verify-security.sh

# Check what will be committed
git status
git diff --cached

# Search for potential secrets
grep -r "password" . --include="*.yml" --exclude="*.example" | grep -v "TODO"

# Verify gitignore working
git check-ignore -v group_vars/all.yml inventory/hosts.yml

# Test clone in temp directory
cd /tmp
git clone /home/jason/Documents/ansible/ansible-wip test-clone
cd test-clone
# Verify example files exist and no passwords present
```

## ✅ Final Pre-Push Checklist

Right before `git push`, verify:

1. [ ] Ran `./verify-security.sh` - **PASSED**
2. [ ] Checked `git diff --cached` - **NO SECRETS**
3. [ ] Verified `.gitignore` working - **YES**
4. [ ] Reviewed `PRE_COMMIT_CHECKLIST.md` - **COMPLETE**
5. [ ] Test clone works - **YES**
6. [ ] Passwords rotated if any were exposed - **N/A or DONE**

---

## 🎯 TL;DR - Quick Start

If you just want the minimum steps:

```bash
cd /home/jason/Documents/ansible/ansible-wip

# 1. Replace actual configs with examples (CRITICAL!)
cd Linux-Setup
cp group_vars/all.yml group_vars/all.yml.PRIVATE
cp group_vars/all.yml.example group_vars/all.yml
cd ..

# 2. Run security check
./verify-security.sh

# 3. Commit and push
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/ansible-playbooks.git
git push -u origin main
```

**Then** restore your local config:
```bash
cd Linux-Setup
cp group_vars/all.yml.PRIVATE group_vars/all.yml
```

---

**Questions?** Review:
- `PRE_COMMIT_CHECKLIST.md` - Detailed checklist
- `SECURITY.md` - Security policy
- `README.md` - Repository overview

**Ready to push?** Run `./verify-security.sh` one last time!
