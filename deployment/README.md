# Deployment Files

This directory contains all files needed for deploying the Obstruction Server on a virtual machine.

## Quick Start

```bash
# Clone repository on your VM
git clone https://github.com/upskiller-xyz/server_obstruction.git
cd server_obstruction/deployment

# Run automated deployment
sudo bash deploy.sh
```

## Files Included

| File | Description |
|------|-------------|
| `deploy.sh` | Automated deployment script for VM setup |
| `obstruction-server.service` | Systemd service file for automatic startup |
| `nginx-obstruction-server.conf` | Nginx reverse proxy configuration |
| `.env.production` | Production environment configuration template |
| `VM_DEPLOYMENT.md` | Comprehensive deployment documentation |

## Deployment Options

### 1. Automated Deployment (Recommended)

```bash
# Basic deployment
sudo bash deploy.sh --skip-nginx

# With nginx reverse proxy
sudo bash deploy.sh

# With custom domain and SSL
sudo bash deploy.sh --domain your-domain.com

# Custom port
sudo bash deploy.sh --port 8082
```

### 2. Manual Deployment

Follow the step-by-step instructions in [VM_DEPLOYMENT.md](VM_DEPLOYMENT.md).

## Prerequisites

- Ubuntu 20.04+ or Debian 11+
- Python 3.11+
- Root/sudo access
- Minimum 2GB RAM

## File Locations After Deployment

| Item | Path |
|------|------|
| Application | `/opt/obstruction-server` |
| Virtual Environment | `/opt/obstruction-server/venv` |
| Configuration | `/opt/obstruction-server/.env` |
| Systemd Service | `/etc/systemd/system/obstruction-server.service` |
| Nginx Config | `/etc/nginx/sites-available/obstruction-server` |
| Application Logs | `/var/log/obstruction-server/` |
| Nginx Logs | `/var/log/nginx/obstruction-server-*.log` |

## Service Management

```bash
# Start/stop/restart service
sudo systemctl start obstruction-server
sudo systemctl stop obstruction-server
sudo systemctl restart obstruction-server

# View logs
sudo journalctl -u obstruction-server -f

# Check status
sudo systemctl status obstruction-server
```

## Testing Deployment

```bash
# Health check
curl http://localhost:8081/

# Expected response:
# {"status": "ready", "timestamp": "2025-01-01T00:00:00Z"}
```

## Documentation

For detailed documentation, see:
- **[VM_DEPLOYMENT.md](VM_DEPLOYMENT.md)** - Complete deployment guide
- **[../README.md](../README.md)** - Project overview and API documentation
- **[../docs/api.md](../docs/api.md)** - API reference

## Support

- Report issues: https://github.com/upskiller-xyz/server_obstruction/issues
- Documentation: https://github.com/upskiller-xyz/server_obstruction

## License

See [LICENSE](../docs/LICENSE) in the main repository.
