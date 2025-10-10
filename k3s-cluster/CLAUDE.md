# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This Ansible playbook automates the deployment of K3s Kubernetes clusters on Linux systems, including Raspberry Pi devices. K3s is a lightweight, certified Kubernetes distribution designed for resource-constrained environments and edge computing.

The playbook supports:
- **Multi-node clusters**: 1 server + N agents
- **Mixed architectures**: x86_64, ARM64 (aarch64), ARM32 (armv7l)
- **Multiple distributions**: Debian, Ubuntu, RHEL, CentOS, Fedora
- **High availability**: Multiple server nodes with embedded etcd

## Architecture

- **Main Playbook**: `main.yml` - Orchestrates cluster deployment in stages
- **Inventory**: `inventory/hosts.yml` - Defines server and agent nodes
- **Roles Structure**: Three specialized roles:
  - `k3s_prereq`: System prerequisites (swap, cgroups, firewall, kernel modules)
  - `k3s_server`: K3s server (control plane) installation
  - `k3s_agent`: K3s agent (worker node) installation

## Supported Platforms

### Hardware
- **x86_64**: Intel/AMD 64-bit servers and workstations
- **ARM64 (aarch64)**: Raspberry Pi 4/5, ARM servers
- **ARM32 (armv7l)**: Raspberry Pi 3

### Minimum Requirements
- **Server**: 2 CPU cores, 2 GB RAM
- **Agent**: 1 CPU core, 512 MB RAM
- **Storage**: SSD recommended (especially for servers)

### Operating Systems
- **Debian Family**: Debian, Ubuntu, Raspberry Pi OS
- **Red Hat Family**: RHEL, CentOS, Fedora, Rocky Linux

## Common Commands

### Running the Playbook

```bash
# Deploy complete cluster (server + agents)
ansible-playbook -i inventory/hosts.yml main.yml

# Deploy only server
ansible-playbook -i inventory/hosts.yml main.yml --limit k3s_server

# Deploy only agents
ansible-playbook -i inventory/hosts.yml main.yml --limit k3s_agents

# Check mode (dry run)
ansible-playbook -i inventory/hosts.yml main.yml --check

# Deploy specific nodes
ansible-playbook -i inventory/hosts.yml main.yml --limit 10.10.2.220,10.10.2.221
```

### Validation

```bash
# Syntax check
ansible-playbook -i inventory/hosts.yml main.yml --syntax-check

# ansible-lint
ansible-lint main.yml

# Lint specific role
ansible-lint roles/k3s_server/
```

### Cluster Management

```bash
# Check cluster status from server
ssh user@k3s-server
kubectl get nodes
kubectl get pods -A

# Get node details
kubectl describe nodes

# View cluster info
kubectl cluster-info

# Check K3s service status
systemctl status k3s          # On server
systemctl status k3s-agent    # On agents
```

### Cluster Operations

```bash
# Add new agent nodes
# 1. Add to inventory under k3s_agents
# 2. Run playbook targeting new nodes
ansible-playbook -i inventory/hosts.yml main.yml --limit new-agent-hostname

# Remove agent node
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
kubectl delete node <node-name>
# Then on the agent: systemctl stop k3s-agent && rm -rf /var/lib/rancher/k3s

# Upgrade cluster
# 1. Set new version in group_vars/all.yml
# 2. Re-run playbook (upgrades in place)
ansible-playbook -i inventory/hosts.yml main.yml
```

## Configuration

### Centralized Configuration (group_vars/all.yml)

All cluster behavior controlled through centralized variables:

#### Prerequisites Settings

```yaml
k3s_prereq_disable_swap: true              # Required for K8s
k3s_prereq_configure_firewall: true        # Auto-configure ports
k3s_prereq_enable_cgroups_rpi: true        # Required for Raspberry Pi
```

#### Server (Control Plane) Settings

```yaml
# Version
k3s_server_version: "latest"  # or "v1.28.5+k3s1"

# Disable built-in components
k3s_server_disable_components:
  - "traefik"        # If using custom ingress
  - "servicelb"      # If using MetalLB

# Network configuration
k3s_server_cluster_cidr: "10.42.0.0/16"    # Pod network
k3s_server_service_cidr: "10.43.0.0/16"    # Service network

# Flannel backend
k3s_server_flannel_backend: "vxlan"        # vxlan, wireguard-native, none

# TLS SANs (for API server certificate)
k3s_server_tls_san:
  - "k3s.example.com"
  - "192.168.1.100"
```

#### Agent (Worker Node) Settings

```yaml
# Server URL (auto-set from inventory)
k3s_agent_server_url: "https://{{ groups['k3s_server'][0] }}:6443"

# Node labels
k3s_agent_node_labels:
  - "node-type=worker"
  - "environment=production"

# Node taints
k3s_agent_node_taints:
  - "dedicated=gpu:NoSchedule"
```

### Inventory Configuration

```yaml
k3s_cluster:
  children:
    k3s_server:
      hosts:
        10.10.2.220:  # Control plane
    k3s_agents:
      hosts:
        10.10.2.221:  # Worker 1
        10.10.2.222:  # Worker 2
```

## Role Details

### k3s_prereq Role

**Purpose**: Prepare systems for K3s installation

**Key Features**:
- Disables swap (required by Kubernetes)
- Enables cgroups on Raspberry Pi
- Loads required kernel modules (br_netfilter, overlay)
- Configures sysctl settings for networking
- Opens firewall ports (if firewalld active)
- Installs prerequisites (curl, iptables, etc.)

**Files**:
- `tasks/main.yml`: Prerequisite configuration
- `defaults/main.yml`: Default settings
- `meta/main.yml`: Role metadata

**Key Variables** (prefixed with `k3s_prereq_`):
- `k3s_prereq_disable_swap`: Disable swap
- `k3s_prereq_enable_cgroups_rpi`: Enable cgroups on Raspberry Pi
- `k3s_prereq_configure_firewall`: Auto-configure firewall

**Firewall Ports Opened**:
- Server: 6443/tcp, 10250/tcp, 2379-2380/tcp, 8472/udp, 51820-51821/udp
- Agent: 10250/tcp, 8472/udp, 51820-51821/udp

### k3s_server Role

**Purpose**: Install and configure K3s server (control plane)

**Key Features**:
- Downloads and installs K3s using official installer
- Configures cluster networking (CIDRs, DNS)
- Disables optional components (Traefik, ServiceLB, etc.)
- Retrieves node token for agents
- Copies kubeconfig to ansible user
- Waits for API server to be ready

**Files**:
- `tasks/main.yml`: Server installation
- `defaults/main.yml`: Default configuration
- `meta/main.yml`: Role metadata

**Key Variables** (prefixed with `k3s_server_`):
- `k3s_server_version`: K3s version to install
- `k3s_server_disable_components`: Components to disable
- `k3s_server_cluster_cidr`: Pod network CIDR
- `k3s_server_flannel_backend`: Network backend (vxlan/wireguard)

**Important Outputs**:
- Node token stored in `hostvars['localhost']['k3s_cluster_token']`
- Kubeconfig copied to `~/.kube/config` on server
- API server accessible at `https://<server-ip>:6443`

### k3s_agent Role

**Purpose**: Install and configure K3s agents (worker nodes)

**Key Features**:
- Retrieves token from server
- Joins cluster via K3S_URL and K3S_TOKEN
- Applies node labels and taints
- Waits for kubelet to start
- Validates connection to server

**Files**:
- `tasks/main.yml`: Agent installation
- `defaults/main.yml`: Default configuration
- `meta/main.yml`: Role metadata

**Key Variables** (prefixed with `k3s_agent_`):
- `k3s_agent_server_url`: K3s server API URL
- `k3s_agent_node_labels`: Labels for the node
- `k3s_agent_node_taints`: Taints for the node

**Security Note**: Token is not logged (using `no_log: true`)

## Deployment Workflow

### 1. Prerequisites Phase
```
All Nodes → k3s_prereq role
  - Disable swap
  - Enable cgroups (Raspberry Pi)
  - Load kernel modules
  - Configure networking (sysctl)
  - Open firewall ports
```

### 2. Server Installation Phase
```
Server Node → k3s_server role
  - Install K3s server
  - Start K3s service
  - Wait for API server
  - Retrieve node token
  - Copy kubeconfig
```

### 3. Agent Installation Phase
```
Agent Nodes → k3s_agent role
  - Get token from server
  - Install K3s agent
  - Join cluster
  - Apply labels/taints
  - Wait for kubelet
```

### 4. Verification Phase
```
Server Node → Verify all nodes ready
  - kubectl get nodes
  - Display cluster status
```

## Cluster Architectures

### Single Node (Development)
```yaml
k3s_server:
  hosts:
    k3s-dev:
k3s_agents:
  hosts: {}
```
- 1 server node (runs workloads too)
- No separate agents
- Minimum: 2 CPU, 2 GB RAM

### Small Cluster (Home Lab)
```yaml
k3s_server:
  hosts:
    k3s-server:
k3s_agents:
  hosts:
    k3s-worker-01:
    k3s-worker-02:
    k3s-worker-03:
```
- 1 server + 3 agents
- Server: 2 CPU, 2 GB RAM
- Agents: 1 CPU, 512 MB RAM each
- Good for learning and testing

### Production Cluster (HA)
```yaml
k3s_server:
  hosts:
    k3s-server-01:
    k3s-server-02:
    k3s-server-03:
k3s_agents:
  hosts:
    k3s-worker-01:
    # ... more workers
```
- 3 servers (HA with embedded etcd)
- 3+ agents
- Servers: 4 CPU, 8 GB RAM each
- Agents: 2+ CPU, 2+ GB RAM each

## Raspberry Pi Specific

### Cgroups Configuration

K3s requires cgroups to be enabled on Raspberry Pi. The playbook automatically:
1. Detects Raspberry Pi OS (checks for `/boot/cmdline.txt` or `/boot/firmware/cmdline.txt`)
2. Adds cgroup parameters to kernel command line
3. Notifies if reboot required

**Manual reboot may be needed** after first run on Raspberry Pi.

### Storage Recommendations

- **SD Card**: OK for agents, avoid for servers
- **USB SSD**: Recommended for servers (etcd database)
- **Boot from SSD**: Best performance

### Model Recommendations

| Model | Role | RAM | Notes |
|-------|------|-----|-------|
| Pi 3 | Agent only | 1 GB | Limited, lightweight workloads |
| Pi 4 (2GB) | Agent | 2 GB | Good for workers |
| Pi 4 (4GB+) | Server or Agent | 4-8 GB | Recommended for servers |
| Pi 5 | Server or Agent | 4-8 GB | Best performance |

## Network Configuration

### Required Ports

**Server Nodes:**
- `6443/tcp` - Kubernetes API server (all nodes + external access)
- `10250/tcp` - Kubelet metrics
- `2379-2380/tcp` - etcd (HA mode only)
- `8472/udp` - Flannel VXLAN
- `51820-51821/udp` - Flannel WireGuard

**Agent Nodes:**
- `10250/tcp` - Kubelet metrics
- `8472/udp` - Flannel VXLAN
- `51820-51821/udp` - Flannel WireGuard

### Flannel Backends

**VXLAN** (default):
- Overlay network using UDP port 8472
- Works in most environments
- Good performance

**WireGuard**:
- Modern encrypted VPN
- Better security
- Requires WireGuard kernel module
- Ports: 51820-51821/udp

**None**:
- Disable Flannel CNI
- Use custom CNI (Calico, Cilium, etc.)

## Quality Assurance

- ✅ **ansible-lint**: Production-level compliance
- ✅ **FQCN compliance**: All modules use fully qualified names
- ✅ **Variable naming**: Role variables properly prefixed
- ✅ **Error handling**: Proper validation and error messages
- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Security**: Token not logged, kubeconfig permissions set

## Troubleshooting

### Prerequisites Issues

**Swap still enabled**:
```bash
# Check swap
swapon --show
free -h

# Manually disable
sudo swapoff -a
sudo sed -i '/swap/d' /etc/fstab
```

**Cgroups not enabled (Raspberry Pi)**:
```bash
# Check cgroups
cat /proc/cgroups

# Verify cmdline.txt
cat /boot/firmware/cmdline.txt  # or /boot/cmdline.txt

# Reboot required after modification
sudo reboot
```

**Firewall blocking**:
```bash
# Check firewall status
sudo firewall-cmd --list-all  # firewalld
sudo ufw status              # ufw

# Manually open K3s port
sudo firewall-cmd --permanent --add-port=6443/tcp
sudo firewall-cmd --reload
```

### Server Installation Issues

**API server not starting**:
```bash
# Check K3s service
sudo systemctl status k3s
sudo journalctl -u k3s -n 100

# Check logs
sudo cat /var/log/syslog | grep k3s

# Verify installation
curl -sfL https://get.k3s.io | sh -s - server --dry-run
```

**Token not found**:
```bash
# Check token file
sudo cat /var/lib/rancher/k3s/server/node-token

# Regenerate if needed (stops cluster!)
sudo systemctl stop k3s
sudo rm -rf /var/lib/rancher/k3s/server
ansible-playbook -i inventory/hosts.yml main.yml --limit k3s_server
```

### Agent Join Issues

**Cannot connect to server**:
```bash
# Test connectivity
telnet <server-ip> 6443
curl -k https://<server-ip>:6443

# Check K3S_URL
sudo systemctl cat k3s-agent | grep K3S_URL

# Verify token
sudo systemctl cat k3s-agent | grep K3S_TOKEN
```

**Node not appearing in cluster**:
```bash
# On server
kubectl get nodes

# On agent
sudo systemctl status k3s-agent
sudo journalctl -u k3s-agent -n 50

# Check kubelet config
sudo cat /var/lib/rancher/k3s/agent/kubelet.kubeconfig
```

### Cluster Issues

**Nodes in NotReady state**:
```bash
kubectl get nodes
kubectl describe node <node-name>

# Check kubelet
sudo systemctl status kubelet

# Check CNI
kubectl get pods -n kube-system
```

**Pods not scheduling**:
```bash
kubectl get pods -A
kubectl describe pod <pod-name>

# Check node taints
kubectl describe nodes | grep Taints

# Remove taint if needed
kubectl taint nodes <node-name> <taint-key>-
```

## Advanced Configuration

### Disable Built-in Components

```yaml
k3s_server_disable_components:
  - "traefik"        # Use Nginx/Istio instead
  - "servicelb"      # Use MetalLB instead
  - "local-storage"  # Use Longhorn/Rook instead
  - "metrics-server" # If using custom metrics
```

### Custom Network Configuration

```yaml
# Larger cluster - more pods
k3s_server_cluster_cidr: "10.42.0.0/8"   # Allows ~16M pods

# Dual-stack IPv4/IPv6
k3s_server_extra_args: "--cluster-cidr=10.42.0.0/16,2001:cafe:42::/56"
```

### Node Labels and Taints

```yaml
# GPU node
k3s_agent_node_labels:
  - "gpu=nvidia"
  - "gpu-type=rtx3090"
k3s_agent_node_taints:
  - "nvidia.com/gpu:NoSchedule"

# Storage node
k3s_agent_node_labels:
  - "storage=local"
k3s_agent_node_taints:
  - "storage=true:NoExecute"
```

### High Availability

For HA clusters with 3+ servers:
1. Deploy all servers in `k3s_server` group
2. K3s will automatically use embedded etcd
3. First server becomes initial leader
4. Subsequent servers join cluster

```yaml
k3s_server:
  hosts:
    k3s-server-01:
    k3s-server-02:
    k3s-server-03:
```

## Post-Installation

### Install Kubectl Locally

```bash
# Copy kubeconfig from server
scp user@k3s-server:~/.kube/config ~/.kube/k3s-config

# Update server IP
sed -i 's/127.0.0.1/<server-ip>/g' ~/.kube/k3s-config

# Use kubeconfig
export KUBECONFIG=~/.kube/k3s-config
kubectl get nodes
```

### Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Recommended Add-ons

**MetalLB** (Load Balancer):
```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml
```

**Longhorn** (Distributed Storage):
```bash
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.5.3/deploy/longhorn.yaml
```

**Cert-Manager** (TLS Certificates):
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
```

## Security Notes

- **Credentials**: Encrypt `ansible_become_password` with ansible-vault
- **Kubeconfig**: Protected with 0600 permissions
- **Node Token**: Not logged in playbook output
- **API Access**: Restrict 6443/tcp to trusted networks
- **RBAC**: Configure Role-Based Access Control for cluster
- **Network Policies**: Implement network segmentation

## Related Documentation

- [K3s Documentation](https://docs.k3s.io/)
- [K3s Requirements](https://docs.k3s.io/installation/requirements)
- [K3s Networking](https://docs.k3s.io/networking)
- [K3s Advanced Configuration](https://docs.k3s.io/installation/configuration)
