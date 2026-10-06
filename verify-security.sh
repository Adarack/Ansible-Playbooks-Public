#!/bin/bash
# Security Verification Script
# Run this before committing to ensure no sensitive data is exposed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo "🔒 Ansible Playbooks Security Verification"
echo "=========================================="
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" == "OK" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" == "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${RED}✗${NC} $message"
        ERRORS=$((ERRORS + 1))
    fi
}

# Check that real secrets from local (gitignored) config files don't appear in
# any file git would commit. Secrets are read at runtime so they are never
# written into this script.
echo "🔍 Checking for real secrets in committable files..."
SECRETS=$(grep -hE '^\s*[A-Za-z0-9_]*(password|passwd|token|secret)[A-Za-z0-9_]*:\s*\S' \
    */group_vars/all.yml 2>/dev/null \
    | grep -v '\$ANSIBLE_VAULT' \
    | sed -E 's/^[^:]*:\s*//; s/\s+#.*$//; s/^["'"'"']//; s/["'"'"']$//' \
    | grep -vE '^(CHANGE_ME|!vault.*|\{\{.*|)$' \
    | awk 'length($0) >= 6' | sort -u || true)
LEAKED=""
if [ -n "$SECRETS" ]; then
    while IFS= read -r f; do
        [ -f "$f" ] || continue
        if grep -qF -f <(printf '%s\n' "$SECRETS") -- "$f"; then
            LEAKED="$LEAKED $f"
        fi
    done < <({ git ls-files; git ls-files --others --exclude-standard; } | sort -u)
fi
if [ -n "$LEAKED" ]; then
    print_status "ERROR" "Real secret values found in committable files:$LEAKED"
else
    print_status "OK" "No real secret values found in committable files"
fi

# Check for common password patterns
echo ""
echo "🔍 Checking for password patterns in YAML files..."
FOUND_PASSWORDS=$(grep -r "password:\s*[\"'].*[\"']" . --include="*.yml" --exclude-dir=.git --exclude="*.example" | grep -v "TODO: " | grep -v "your_password" | grep -v "YOUR_" | grep -v "example" || true)
if [ -n "$FOUND_PASSWORDS" ]; then
    print_status "WARN" "Found potential passwords in YAML files:"
    echo "$FOUND_PASSWORDS"
else
    print_status "OK" "No suspicious password patterns in YAML files"
fi

# Check for .vault_pass files
echo ""
echo "🔍 Checking for vault password files..."
if find . -name ".vault_pass" -o -name ".vault_password" -o -name "vault_pass.txt" 2>/dev/null | grep -q .; then
    print_status "ERROR" "Found vault password files! These should be gitignored."
else
    print_status "OK" "No vault password files found in repository"
fi

# Check that sensitive files are gitignored
echo ""
echo "🔍 Checking git tracking status..."
PLAYBOOKS=("Linux-Setup" "UpdateSystem" "k3s-cluster" "wyoming-satellite")

for playbook in "${PLAYBOOKS[@]}"; do
    if [ -d "$playbook" ]; then
        # Check if actual config files are tracked
        if git ls-files --error-unmatch "$playbook/group_vars/all.yml" >/dev/null 2>&1; then
            print_status "ERROR" "$playbook/group_vars/all.yml is tracked by git!"
        else
            print_status "OK" "$playbook/group_vars/all.yml is not tracked"
        fi

        if git ls-files --error-unmatch "$playbook/inventory/hosts.yml" >/dev/null 2>&1; then
            print_status "ERROR" "$playbook/inventory/hosts.yml is tracked by git!"
        else
            print_status "OK" "$playbook/inventory/hosts.yml is not tracked"
        fi
    fi
done

# Check that example files exist
echo ""
echo "🔍 Checking for example template files..."
for playbook in "${PLAYBOOKS[@]}"; do
    if [ -d "$playbook" ]; then
        if [ -f "$playbook/group_vars/all.yml.example" ]; then
            print_status "OK" "$playbook has all.yml.example"
        else
            print_status "WARN" "$playbook missing all.yml.example"
        fi

        if [ -f "$playbook/inventory/hosts.yml.example" ]; then
            print_status "OK" "$playbook has hosts.yml.example"
        else
            print_status "WARN" "$playbook missing hosts.yml.example"
        fi
    fi
done

# Check for SSH private keys
echo ""
echo "🔍 Checking for SSH private keys..."
if find . -name "id_rsa" -o -name "id_ed25519" -o -name "*.pem" -o -name "*.key" | grep -v "\.git" | grep -q .; then
    print_status "ERROR" "Found SSH private keys in repository!"
else
    print_status "OK" "No SSH private keys found"
fi

# Check git status for staged files
echo ""
echo "🔍 Checking git status for potentially sensitive staged files..."
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)
if echo "$STAGED_FILES" | grep -qE '(^|/)group_vars/all\.yml$|(^|/)inventory/hosts\.yml$|\.vault_pass'; then
    print_status "ERROR" "Sensitive files are staged for commit!"
    echo "$STAGED_FILES" | grep -E '(^|/)group_vars/all\.yml$|(^|/)inventory/hosts\.yml$|\.vault_pass'
else
    print_status "OK" "No sensitive files staged for commit"
fi

# Check for IP addresses in staged files (warning only)
echo ""
echo "🔍 Checking for private IP addresses in changes..."
if git diff --cached | grep -E "10\.(10|0)\.[0-9]{1,3}\.[0-9]{1,3}" >/dev/null 2>&1; then
    print_status "WARN" "Found private IP addresses (10.x.x.x) in staged changes"
    echo "  This may be okay if these are example IPs. Review carefully."
fi

# Summary
echo ""
echo "=========================================="
echo "📊 Summary"
echo "=========================================="
echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ FAILED: Please fix errors before committing!${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  WARNINGS: Review warnings before committing.${NC}"
    echo "Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo -e "${GREEN}✅ Security check passed!${NC}"
echo ""
echo "Additional manual checks recommended:"
echo "  - Review: git diff --cached"
echo "  - Verify: PRE_COMMIT_CHECKLIST.md"
echo "  - Double-check: No real passwords or tokens in changes"
echo ""
exit 0
