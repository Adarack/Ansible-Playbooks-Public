# Pre-Commit Security Checklist for Public Git

**⚠️ IMPORTANT**: Complete ALL items before pushing to public repository!

## 🔴 CRITICAL - Sensitive Data Removal

### Passwords & Credentials

- [ ] **Remove plaintext passwords from `Linux-Setup/group_vars/all.yml`**
  - Line 3: `ansible_become_password: "REDACTED"` → Replace with example
  - Line 124: `password: "REDACTED"` (MQTT) → Replace with example
  - Line 278: `web_password` (Pi-hole) → Verify is empty or example

- [ ] **Check `UpdateSystem/group_vars/all.yml` for passwords**
  - Review for any plaintext credentials

- [ ] **Check `k3s-cluster/group_vars/all.yml` for tokens/secrets**
  - K3s cluster tokens
  - API credentials

- [ ] **Check `wyoming-satellite/group_vars/all.yml` for API keys**
  - Home Assistant tokens
  - API credentials

### IP Addresses & Network Information

- [ ] **Decide on IP address strategy** (choose one):
  - **Option A**: Replace all `10.10.x.x` IPs with `192.168.1.x` examples
  - **Option B**: Leave actual IPs (if acceptable for your use case)
  - **Option C**: Create separate example inventory files with sanitized IPs

Files to review:
- `Linux-Setup/inventory/hosts.yml` - Contains `10.10.2.x` addresses
- `Linux-Setup/group_vars/all.yml` - MQTT host, NTP servers
- `UpdateSystem/inventory/hosts.yml`
- Other playbook inventories

### SSH Public Keys

- [ ] **Decide on SSH key strategy** (choose one):
  - **Option A**: Keep public keys (they're public by design - safe)
  - **Option B**: Replace with example keys
  - **Recommended**: Keep them - SSH public keys are meant to be shared

### Hostnames

- [ ] **Review hostnames for sensitive information**
  - Current examples: NTP-PI, Kube-Pi-CP01, Proxmox01, etc.
  - These are generally okay unless they reveal infrastructure details you want private

## 🟡 IMPORTANT - File Protection

### Verify .gitignore Files

- [ ] **Root `.gitignore` exists** ✅ (already present)
  - Ignores: *.retry, *.log, .vault_pass, SSH keys

- [ ] **Check each playbook has `.gitignore`**
  - [ ] `Linux-Setup/.gitignore` ✅ (already present)
  - [ ] `UpdateSystem/.gitignore`
  - [ ] `k3s-cluster/.gitignore`
  - [ ] `wyoming-satellite/.gitignore`

### Verify Example Files Exist

- [ ] **Linux-Setup example files**
  - [ ] `inventory/hosts.yml.example` ✅ (already exists)
  - [ ] `group_vars/all.yml.example` ✅ (already exists)

- [ ] **UpdateSystem example files**
  - [ ] `inventory/hosts.yml.example`
  - [ ] `group_vars/all.yml.example`

- [ ] **k3s-cluster example files**
  - [ ] `inventory/hosts.yml.example`
  - [ ] `group_vars/all.yml.example`

- [ ] **wyoming-satellite example files**
  - [ ] `inventory/hosts.yml.example`
  - [ ] `group_vars/all.yml.example`

### Git Status Verification

- [ ] **Run git status in each playbook directory**
  ```bash
  cd Linux-Setup && git status
  cd ../UpdateSystem && git status
  cd ../k3s-cluster && git status
  cd ../wyoming-satellite && git status
  ```

- [ ] **Verify NO files with actual credentials are staged**
  - `inventory/hosts.yml` should be gitignored
  - `group_vars/all.yml` should be gitignored
  - `.vault_pass` should be gitignored

## 🟢 RECOMMENDED - Documentation & Quality

### Documentation Review

- [ ] **Update README files with sanitized examples**
  - [ ] Root `README.md` ✅ (already good)
  - [ ] `Linux-Setup/README.md`
  - [ ] `UpdateSystem/README.md`
  - [ ] `k3s-cluster/README.md`
  - [ ] `wyoming-satellite/README.md`

- [ ] **Review CLAUDE.md files for sensitive info**
  - [ ] Root `CLAUDE.md`
  - [ ] Playbook-specific `CLAUDE.md` files

### Optional Security Enhancements

- [ ] **Add LICENSE file** (MIT recommended for public Ansible roles)
- [ ] **Add SECURITY.md** (security policy and vulnerability reporting)
- [ ] **Add CONTRIBUTING.md** (contribution guidelines)
- [ ] **Add CODE_OF_CONDUCT.md** (if accepting contributions)

### Testing Before Push

- [ ] **Run ansible-lint on all playbooks**
  ```bash
  cd Linux-Setup && ansible-lint main.yml
  cd ../UpdateSystem && ansible-lint main.yml
  cd ../k3s-cluster && ansible-lint main.yml
  cd ../wyoming-satellite && ansible-lint main.yml
  ```

- [ ] **Verify syntax on all playbooks**
  ```bash
  ansible-playbook -i inventory/hosts.yml.example main.yml --syntax-check
  ```

## 🔧 Quick Fix Commands

### Sanitize group_vars/all.yml

```bash
cd Linux-Setup

# Backup original (keep locally, don't commit)
cp group_vars/all.yml group_vars/all.yml.PRIVATE

# Replace with example (or manually edit)
cp group_vars/all.yml.example group_vars/all.yml

# Edit to add non-sensitive customizations
nano group_vars/all.yml
```

### Verify Git Ignore Working

```bash
cd /home/jason/Documents/ansible/ansible-wip

# Should show .example files but NOT actual config files
git status

# Should NOT show:
# - inventory/hosts.yml
# - group_vars/all.yml
# - .vault_pass
# - *.retry
# - *.log
```

### Clean Git Cache (if sensitive files were previously tracked)

```bash
cd /home/jason/Documents/ansible/ansible-wip

# Remove from git tracking (keeps local file)
git rm --cached Linux-Setup/group_vars/all.yml
git rm --cached Linux-Setup/inventory/hosts.yml
git rm --cached UpdateSystem/group_vars/all.yml
git rm --cached UpdateSystem/inventory/hosts.yml

# Commit the removal
git commit -m "Remove sensitive configuration files from tracking"
```

## ✅ Final Verification

Before `git push`:

1. **Review the diff**: `git diff` - should contain NO passwords, tokens, or private IPs
2. **Check staged files**: `git status` - verify only safe files are staged
3. **Test clone**: Clone to temp directory and verify it works with example files
4. **Double-check**: grep for common secrets

```bash
# Search for potential secrets before pushing
cd /home/jason/Documents/ansible/ansible-wip
grep -r "password.*=" --include="*.yml" --exclude="*.example" --exclude-dir=".git"
# Checks committable files for the real secrets in your local group_vars/all.yml files
./verify-security.sh
```

## 📝 Post-Commit Actions

After successful push:

- [ ] **Test fresh clone**
  ```bash
  cd /tmp
  git clone <your-repo-url>
  cd ansible-playbooks
  # Verify example files exist and are usable
  ```

- [ ] **Add repository description and topics on GitHub**
  - Topics: ansible, automation, devops, infrastructure-as-code, raspberry-pi, kubernetes, linux

- [ ] **Enable GitHub security features**
  - Dependabot alerts
  - Secret scanning (catches accidentally committed secrets)
  - Security policy

## 🆘 Emergency: Committed a Secret?

If you accidentally commit and push a secret:

1. **DO NOT just delete the file** - it's still in git history
2. **Rotate the secret immediately** (change password/key)
3. **Use git filter-branch or BFG Repo-Cleaner** to remove from history
4. **Force push** the cleaned history
5. **Notify collaborators** to re-clone

Better approach: **Avoid this entirely by following this checklist!**

---

## 📋 Quick Reference: Files That MUST Be Gitignored

```
# In every playbook directory:
inventory/hosts.yml           # Actual inventory with IPs
group_vars/all.yml           # Actual config with passwords
host_vars/                   # Host-specific sensitive data
.vault_pass                  # Vault password file
.vault_password              # Alternative vault password file
*.retry                      # Ansible retry files
*.log                        # Log files may contain sensitive output
```

## 📋 Files That SHOULD Be Committed

```
# In every playbook directory:
main.yml                     # Main playbook
ansible.cfg                  # Ansible configuration
.gitignore                   # Git ignore rules
README.md                    # User documentation
CLAUDE.md                    # Technical documentation
inventory/hosts.yml.example  # Sanitized inventory template
group_vars/all.yml.example   # Sanitized config template
roles/                       # All role files (with defaults)
templates/                   # Generic Jinja2 templates
```
