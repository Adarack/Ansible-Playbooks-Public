# K3s Cluster Deployment - Ansible Playbook

Automated deployment of K3s Kubernetes clusters on Linux systems and Raspberry Pi.

## What It Does

Deploys production-ready K3s Kubernetes clusters with:
- **Multi-node support**: 1 server + N worker agents
- **Cross-platform**: x86_64, ARM64, ARM32 architectures
- **Auto-configuration**: Prerequisites, networking, firewall
- **Raspberry Pi optimized**: Cgroups, storage recommendations

## Quick Start

```bash
# 1. Configure inventory
vim inventory/hosts.yml

# 2. Configure cluster settings
vim group_vars/all.yml

# 3. Deploy cluster
ansible-playbook -i inventory/hosts.yml main.yml
```

## Requirements

### Hardware Minimums
- **Server (control plane)**: 2 CPU cores, 2 GB RAM
- **Agent (worker node)**: 1 CPU core, 512 MB RAM
- **Storage**: SSD recommended (especially for servers)

### Supported Systems
- Debian/Ubuntu/Raspberry Pi OS
- RHEL/CentOS/Fedora/Rocky Linux
- x86_64, ARM64 (aarch64), ARM32 (armv7l)

## Key Configuration

Edit `inventory/hosts.yml`:
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
        10.10.2.223:  # Worker 3
```

Edit `group_vars/all.yml`:
```yaml
# K3s version
k3s_server_version: "latest"

# Disable built-in components (optional)
k3s_server_disable_components:
  - "traefik"      # Use custom ingress
  - "servicelb"    # Use MetalLB

# Network configuration
k3s_server_cluster_cidr: "10.42.0.0/16"
k3s_server_service_cidr: "10.43.0.0/16"
```

## What Gets Installed

### Prerequisites (All Nodes)
- Swap disabled
- Cgroups enabled (Raspberry Pi)
- Kernel modules loaded (br_netfilter, overlay)
- Networking configured (sysctl)
- Firewall ports opened
- Required packages installed

### Server (Control Plane)
- K3s server service
- Kubernetes API server (port 6443)
- Embedded etcd database
- Kubeconfig at `~/.kube/config`
- Node token for agents

### Agents (Worker Nodes)
- K3s agent service
- Kubelet (connects to server)
- Container runtime
- CNI networking (Flannel)

## Verification

After deployment:

```bash
# SSH to server node
ssh user@k3s-server

# Check cluster status
kubectl get nodes
kubectl get pods -A

# View cluster info
kubectl cluster-info
```

Expected output:
```
NAME            STATUS   ROLES                  AGE   VERSION
k3s-server      Ready    control-plane,master   5m    v1.28.5+k3s1
k3s-worker-01   Ready    <none>                 3m    v1.28.5+k3s1
k3s-worker-02   Ready    <none>                 3m    v1.28.5+k3s1
```

## Common Tasks

### Deploy Workloads

```bash
# Create deployment
kubectl create deployment nginx --image=nginx

# Expose as service
kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Check deployment
kubectl get pods
kubectl get services
```

### Add New Worker Node

```bash
# 1. Add to inventory under k3s_agents
vim inventory/hosts.yml

# 2. Run playbook for new node only
ansible-playbook -i inventory/hosts.yml main.yml --limit new-worker-ip
```

### Remove Worker Node

```bash
# Drain and delete
kubectl drain <node-name> --ignore-daemonsets
kubectl delete node <node-name>

# On the node
sudo systemctl stop k3s-agent
sudo rm -rf /var/lib/rancher/k3s
```

### Upgrade Cluster

```bash
# 1. Update version in group_vars/all.yml
k3s_server_version: "v1.29.0+k3s1"

# 2. Re-run playbook
ansible-playbook -i inventory/hosts.yml main.yml
```

## Cluster Architectures

### Single Node (Development)
- 1 server (also runs workloads)
- Minimum: 2 CPU, 2 GB RAM
- Perfect for testing

### Small Cluster (Home Lab)
- 1 server + 2-3 agents
- Server: 2 CPU, 2 GB RAM
- Agents: 1 CPU, 512 MB RAM each
- Good for learning

### Production Cluster
- 3 servers (HA) + 3+ agents
- Servers: 4 CPU, 8 GB RAM each
- Agents: 2+ CPU, 2+ GB RAM each
- Embedded etcd for HA

## Raspberry Pi Support

### Model Recommendations
- **Pi 3**: Agent only, lightweight workloads
- **Pi 4 (4GB+)**: Server or agent
- **Pi 5**: Excellent for servers

### Important Notes
- **Cgroups**: Automatically enabled (reboot required)
- **Storage**: Use SSD for servers (not SD card)
- **Cooling**: Recommended for sustained loads
- **Power**: Use official power supply

## Network Ports

The playbook automatically opens required ports:

### Server
- 6443/tcp - Kubernetes API
- 10250/tcp - Kubelet metrics
- 8472/udp - Flannel VXLAN
- 51820-51821/udp - Flannel WireGuard

### Agents
- 10250/tcp - Kubelet metrics
- 8472/udp - Flannel VXLAN
- 51820-51821/udp - Flannel WireGuard

## Post-Installation

### Access Cluster Remotely

```bash
# Copy kubeconfig from server
scp user@k3s-server:~/.kube/config ~/.kube/k3s-config

# Update server IP
sed -i 's/127.0.0.1/<actual-server-ip>/g' ~/.kube/k3s-config

# Use it
export KUBECONFIG=~/.kube/k3s-config
kubectl get nodes
```

### Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

### Recommended Add-ons

**MetalLB** (LoadBalancer for bare metal):
```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml
```

**Longhorn** (Distributed storage):
```bash
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.5.3/deploy/longhorn.yaml
```

**Cert-Manager** (Automatic TLS):
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
```

## Troubleshooting

### Swap is still enabled
```bash
sudo swapoff -a
sudo sed -i '/swap/d' /etc/fstab
```

### Cgroups not enabled (Raspberry Pi)
```bash
# Playbook should configure this, but if needed:
sudo nano /boot/firmware/cmdline.txt
# Add: cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory
sudo reboot
```

### Agent won't join cluster
```bash
# Check connectivity
telnet <server-ip> 6443

# Check token on server
sudo cat /var/lib/rancher/k3s/server/node-token

# Check agent logs
sudo journalctl -u k3s-agent -n 50
```

### Nodes in NotReady state
```bash
kubectl get nodes
kubectl describe node <node-name>
kubectl get pods -n kube-system
```

## Project Structure

```
k3s-cluster/
├── main.yml                    # Main playbook
├── ansible.cfg                 # Ansible configuration
├── inventory/hosts.yml         # Cluster nodes
├── group_vars/all.yml          # Cluster configuration
└── roles/
    ├── k3s_prereq/             # Prerequisites
    ├── k3s_server/             # Control plane
    └── k3s_agent/              # Worker nodes
```

## Documentation

See [CLAUDE.md](CLAUDE.md) for comprehensive documentation including:
- Detailed architecture
- All configuration options
- Advanced cluster setups
- Complete troubleshooting guide
- High availability configuration

## Safety Features

✅ Idempotent - safe to run multiple times
✅ ansible-lint production compliance
✅ Validates requirements before installation
✅ Auto-configures system prerequisites
✅ Secure token handling (not logged)
✅ Proper kubeconfig permissions

## Support

For K3s issues, see:
- [K3s Documentation](https://docs.k3s.io/)
- [K3s GitHub](https://github.com/k3s-io/k3s)
- [K3s Community](https://rancher.com/community)
