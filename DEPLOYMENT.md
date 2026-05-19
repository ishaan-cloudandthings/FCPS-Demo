# Docker Deployment Guide - Production

This guide covers deploying the FCPS Procurement Portal to EC2 or any Docker-enabled environment using Docker Compose.

## Prerequisites

- Docker installed on your machine/EC2
- Docker Compose installed
- Production environment variables ready (see `.env.prod.example`)

## Quick Start

### 1. Prepare Environment Variables

```bash
cp .env.prod.example .env.prod
# Edit .env.prod with your production values
nano .env.prod
```

Required variables:
```
IDME_CLIENT_ID
IDME_CLIENT_SECRET
IDME_REDIRECT_URI
JWT_SECRET_KEY (generate: python -c "import secrets; print(secrets.token_urlsafe(48))")
ORACLE_HOST
ORACLE_PORT
ORACLE_SERVICE_NAME
ORACLE_USER
ORACLE_PASSWORD
```

### 2. Build Docker Images

```bash
docker-compose build
```

### 3. Start Services

```bash
docker-compose up -d
```

Services will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

## Deployment to EC2

### 1. SSH into EC2

```bash
ssh -i /path/to/key.pem ubuntu@your-ec2-ip
```

### 2. Clone Repository

```bash
cd /opt
git clone https://github.com/Cloud-and-Things/FCPS-Demo.git
cd FCPS-Demo
git checkout prod
```

### 3. Install Docker & Docker Compose

```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker ubuntu
# Log out and back in for group changes to take effect
```

### 4. Set Up Environment

```bash
cp .env.prod.example .env.prod
sudo nano .env.prod  # Edit with production values
```

### 5. Build and Run

```bash
docker-compose build
docker-compose up -d
```

### 6. Verify Deployment

```bash
docker-compose ps
docker-compose logs backend
docker-compose logs frontend
```

## Production Configuration

### Nginx Reverse Proxy (Optional)

For production, use Nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/HTTPS with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild images
docker-compose build --no-cache

# Pull latest code and restart
git pull origin prod
docker-compose build
docker-compose up -d

# Check service health
docker-compose ps
docker ps

# View logs
docker-compose logs -f

# Execute command in container
docker-compose exec backend python -c "..."

# Remove all containers and volumes
docker-compose down -v
```

## Troubleshooting

### Port Already in Use
```bash
# Find and stop existing container
docker ps
docker stop container_id
```

### Build Failures
```bash
# Rebuild without cache
docker-compose build --no-cache
```

### Database Connection Issues
- Verify `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_USER`, `ORACLE_PASSWORD`
- Ensure Oracle database is accessible from EC2
- Check EC2 security groups allow outbound connections

### Health Check Failures
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Manually test
docker-compose exec backend curl http://localhost:8000/health
```

## Environment-Specific Notes

- **Production:** Always use `ENVIRONMENT=prod` in docker-compose.yml
- **JWT_COOKIE_SECURE:** Set to `true` for HTTPS
- **ORACLE_HOST:** Use internal IP/DNS for security (not public)
- **IDME_REDIRECT_URI:** Must match your production domain exactly
