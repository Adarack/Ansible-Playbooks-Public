# Security Policy

## Supported Versions

This repository contains multiple Ansible playbook projects. Security updates are provided for the latest version of each playbook.

| Project | Status |
| ------- | ------ |
| Linux-Setup | ✅ Actively maintained |
| UpdateSystem | ✅ Actively maintained |
| k3s-cluster | ✅ Actively maintained |
| wyoming-satellite | ✅ Actively maintained |

## Reporting a Vulnerability

### Where to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities through one of the following methods:

1. **GitHub Security Advisories** (Preferred)
   - Go to the "Security" tab
   - Click "Report a vulnerability"
   - Fill out the advisory form

2. **Direct Contact**
   - Open a draft GitHub issue with title "SECURITY: [Brief Description]"
   - We will convert it to a private security advisory

### What to Include

Please include the following information in your report:

- **Description**: Clear description of the vulnerability
- **Impact**: What an attacker could do by exploiting this
- **Affected Playbooks/Roles**: Which parts of the codebase are affected
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Suggested Fix**: If you have ideas on how to fix it (optional)
- **Severity Assessment**: Your assessment of the severity (Critical/High/Medium/Low)

### Example Security Issues

Examples of security issues we want to know about:

- Hardcoded credentials or secrets
- Command injection vulnerabilities
- Privilege escalation issues
- Unsafe file permissions in deployed configurations
- Missing input validation that could lead to security issues
- Insecure default configurations

### What We Do

When you report a security vulnerability:

1. **Acknowledgment**: We will acknowledge receipt within 48 hours
2. **Investigation**: We will investigate and determine severity
3. **Fix Development**: We will develop a fix in a private fork
4. **Coordinated Disclosure**: We will coordinate disclosure timing with you
5. **Release**: We will release the fix and publish a security advisory
6. **Credit**: We will credit you in the advisory (unless you prefer to remain anonymous)

## Security Best Practices for Users

### Before Using These Playbooks

1. **Review the Code**
   - Read playbooks before running them
   - Understand what each role does
   - Review defaults and templates

2. **Use Ansible Vault**
   - Never commit plaintext passwords
   - Encrypt all sensitive variables
   - Use strong vault passwords

3. **Secure Your Control Node**
   - Keep Ansible updated
   - Protect SSH private keys
   - Use key-based authentication

4. **Test in Non-Production First**
   - Always test playbooks in a safe environment
   - Use `--check` mode (dry run) first
   - Verify changes before applying to production

### Protecting Sensitive Data

Each playbook includes:

- **`.gitignore`** files to prevent committing sensitive data
- **`.example`** template files for configuration
- **Documentation** on using ansible-vault

**Never commit these files:**
- `inventory/hosts.yml` (use `hosts.yml.example` instead)
- `group_vars/all.yml` (use `all.yml.example` instead)
- `.vault_pass` or similar vault password files
- Any files containing passwords, API keys, or tokens

### Recommended Security Configuration

When deploying with these playbooks:

1. **SSH Security**
   - Disable password authentication
   - Use SSH keys only
   - Disable root login
   - Change default SSH port (optional)

2. **Firewall Configuration**
   - Enable UFW/firewalld
   - Only open required ports
   - Use fail2ban for brute force protection

3. **Updates**
   - Enable automatic security updates
   - Regularly run UpdateSystem playbook
   - Monitor security advisories for installed software

4. **Monitoring**
   - Deploy monitoring (Prometheus/Grafana/Node Exporter)
   - Review logs regularly
   - Set up alerts for suspicious activity

## Common Vulnerabilities and Mitigations

### 1. Hardcoded Credentials

**Risk**: Credentials committed to git history

**Mitigation**:
- Use `.example` files with placeholder values
- Encrypt sensitive variables with ansible-vault
- Follow PRE_COMMIT_CHECKLIST.md before pushing

### 2. Privilege Escalation

**Risk**: Playbooks running with excessive privileges

**Mitigation**:
- Use `become: true` only when necessary
- Specify `become_user` when not root
- Review sudoers configurations

### 3. Insecure File Permissions

**Risk**: Configuration files with overly permissive permissions

**Mitigation**:
- Templates specify appropriate `mode` (0600 for secrets, 0644 for configs)
- Review deployed file permissions
- Use `ansible.builtin.file` module to enforce permissions

### 4. Command Injection

**Risk**: User input in shell commands without validation

**Mitigation**:
- Use Ansible modules instead of shell/command when possible
- Validate and sanitize variables
- Use `ansible.builtin.command` with `args` instead of shell interpolation

### 5. Outdated Dependencies

**Risk**: Using vulnerable versions of software

**Mitigation**:
- Pin software versions in `group_vars/all.yml`
- Regularly review and update versions
- Subscribe to security advisories for used software

## Security Scanning

This repository uses:

- **ansible-lint**: Catches common Ansible security issues
- **yamllint**: Ensures YAML syntax doesn't hide issues
- **Manual Review**: All contributions are reviewed for security

## Updates and Advisories

Security advisories will be published in:

- GitHub Security Advisories tab
- Release notes for affected playbooks
- README.md updates with mitigation steps

## Scope

This security policy covers:

- ✅ Security vulnerabilities in playbooks and roles
- ✅ Insecure default configurations
- ✅ Issues with example code or documentation
- ✅ Dependency vulnerabilities (when applicable)

This security policy does NOT cover:

- ❌ Issues with third-party software installed by playbooks (report to upstream)
- ❌ User-specific misconfigurations
- ❌ General Ansible framework bugs (report to Ansible project)
- ❌ Issues only affecting `.example` files (these are templates, not executed)

## Additional Resources

- [Ansible Security Best Practices](https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html#tip-for-variables-and-vaults)
- [Ansible Vault Documentation](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [OWASP Ansible Security](https://cheatsheetseries.owasp.org/cheatsheets/Infrastructure_as_Code_Security_Cheat_Sheet.html)

## Questions?

If you have questions about this security policy or general security questions (not reporting a vulnerability), please:

- Open a Discussion in the GitHub Discussions tab
- Tag it with the "security" label
- We'll respond publicly so others can benefit

---

**Remember**: Security is a shared responsibility. Review code before running it, follow best practices, and keep systems updated.
