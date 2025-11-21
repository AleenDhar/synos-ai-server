# Deployment Guide

## Production Checklist

- [ ] Set strong API keys
- [ ] Use HTTPS/reverse proxy
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Use environment variables
- [ ] Enable logging
- [ ] Test error handling

## Docker Deployment

### Build Image

```bash
docker build -t deepagent-server .
```

### Run Container

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name deepagent \
  deepagent-server
```

### Docker Compose

```yaml
version: '3.8'
services:
  deepagent:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./custom_tools:/app/custom_tools
      - ./workspace:/app/workspace
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

## systemd Service

Create `/etc/systemd/system/deepagent.service`:

```ini
[Unit]
Description=DeepAgent Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/deepagent-server
EnvironmentFile=/path/to/deepagent-server/.env
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable deepagent
sudo systemctl start deepagent
sudo systemctl status deepagent
```

## Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Environment Variables

Production `.env`:

```bash
# Server
HOST=0.0.0.0
PORT=8000

# Model
MODEL=anthropic:claude-sonnet-4-20250514

# API Keys (use secrets manager in production)
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# Logging
LOG_LEVEL=INFO

# Security
ALLOWED_ORIGINS=https://your-domain.com
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/api/health
```

### Logs

```bash
# Docker
docker logs -f deepagent

# systemd
journalctl -u deepagent -f

# File
tail -f server.log
```

## Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```bash
# Instance 1
PORT=8001 python server.py

# Instance 2
PORT=8002 python server.py

# Instance 3
PORT=8003 python server.py
```

Load balancer config (nginx):
```nginx
upstream deepagent {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    location / {
        proxy_pass http://deepagent;
    }
}
```

## Security

### API Key Management

Use environment variables or secrets manager:

```bash
# AWS Secrets Manager
export ANTHROPIC_API_KEY=$(aws secretsmanager get-secret-value --secret-id anthropic-key --query SecretString --output text)

# Kubernetes Secret
kubectl create secret generic deepagent-secrets \
  --from-literal=anthropic-api-key=your-key
```

### HTTPS

Use Let's Encrypt with certbot:

```bash
sudo certbot --nginx -d your-domain.com
```

### Rate Limiting

Add to nginx config:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20;
    proxy_pass http://localhost:8000;
}
```

## Backup

### Configuration
```bash
# Backup
tar -czf backup.tar.gz .env custom_tools/ mcp_config.json

# Restore
tar -xzf backup.tar.gz
```

### Google Sheets Tokens
```bash
# Backup
cp google_sheets_tokens.json google_sheets_tokens.json.backup

# Restore
cp google_sheets_tokens.json.backup google_sheets_tokens.json
```

## Troubleshooting

### High Memory Usage
- Reduce max_steps in agent config
- Limit conversation history
- Use smaller models

### Slow Responses
- Use faster models (GPT-3.5, Gemini Flash)
- Reduce tool count
- Enable caching

### Connection Issues
- Check firewall rules
- Verify port is open
- Check reverse proxy config

## Performance Optimization

1. **Use caching** - Anthropic auto-caches prompts
2. **Limit tools** - Keep under 15 tools per agent
3. **Set max steps** - Prevent infinite loops
4. **Use streaming** - Better UX for long responses
5. **Monitor tokens** - Use LangSmith for tracking

## Updates

```bash
# Pull latest code
git pull

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart deepagent
```

## Support

- Check logs for errors
- Verify configuration
- Test health endpoint
- Review documentation
