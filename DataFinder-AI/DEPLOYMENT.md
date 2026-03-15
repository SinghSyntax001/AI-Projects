# 📦 Production Deployment Guide

Complete guide for deploying DataFinder-AI to production environments.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Platforms](#cloud-platforms)
- [Monitoring & Observability](#monitoring--observability)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Configuration

- [ ] Set `API_KEY` to a strong random value (min 32 characters)
- [ ] Update `.env` with production database URL
- [ ] Set `APP_ENV=production`
- [ ] Set `DEBUG=false`
- [ ] Configure external API keys (Groq, Kaggle, GitHub, etc.)

### Dependencies

- [ ] Run `pip install -r requirements.txt`
- [ ] Run `pip install -r requirements-dev.txt` (for testing)

### Database

- [ ] Apply migrations: `python -c "from app.migrations import apply_migrations; apply_migrations()"`
- [ ] Verify database connectivity
- [ ] Test write permissions

### LLM & APIs

- [ ] Verify Groq API key is working
- [ ] Test external data source connectivity

### Logging

- [ ] Create logs directory: `mkdir -p logs`
- [ ] Verify log directory is writable
- [ ] Configure log rotation (if using external syslog)

### Security

- [ ] Enable HTTPS (reverse proxy with TLS)
- [ ] Set up firewall rules
- [ ] Configure rate limiting (enabled by default)
- [ ] Review CORS settings

---

## Local Development

### Setup

```bash
# Clone repository
git clone <repository>
cd DataFinder-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create .env file
cp .env.example .env
# Edit .env with your values

# Apply database migrations
python -c "from app.migrations import apply_migrations; apply_migrations()"
```

### Running Locally

```bash
# Single worker (development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Multiple workers (closer to production)
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_api.py::test_search_datasets -v
```

---

## Docker Deployment

### Building Image

```bash
# Build image
docker build -t datafinder-ai:latest .

# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.11 -t datafinder-ai:3.11 .

# Tag for registry
docker tag datafinder-ai:latest myregistry.azurecr.io/datafinder-ai:latest
```

### Single Container

```bash
# Run with SQLite (development only)
docker run -p 8000:8000 \
  -e API_KEY=your-secret-key \
  -e GROQ_API_KEY=your-groq-key \
  -v $(pwd)/data:/app/data \
  datafinder-ai:latest

# Run with PostgreSQL
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+psycopg2://user:pass@postgres:5432/datafinder" \
  -e API_KEY=your-secret-key \
  -e GROQ_API_KEY=your-groq-key \
  datafinder-ai:latest
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Check health
curl http://localhost:8000/health

# Stop services
docker-compose down
```

### Scaling with Docker

```bash
# Scale API service to 3 replicas
docker-compose up -d --scale api=3

# Note: Requires load balancer in front (e.g., Nginx)
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
# Configure kubeconfig
# Ensure Docker image is accessible to cluster
```

### Deployment Manifest (`k8s/deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datafinder-api
  namespace: default
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: datafinder-api
  template:
    metadata:
      labels:
        app: datafinder-api
    spec:
      containers:
        - name: api
          image: myregistry.azurecr.io/datafinder-ai:latest
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 8000
          env:
            - name: APP_ENV
              value: "production"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: datafinder-secrets
                  key: database-url
            - name: API_KEY
              valueFrom:
                secretKeyRef:
                  name: datafinder-secrets
                  key: api-key
            - name: GROQ_API_KEY
              valueFrom:
                secretKeyRef:
                  name: datafinder-secrets
                  key: groq-api-key
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 2
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            allowPrivilegeEscalation: false
---
apiVersion: v1
kind: Service
metadata:
  name: datafinder-api
spec:
  type: LoadBalancer
  selector:
    app: datafinder-api
  ports:
    - name: http
      port: 80
      targetPort: http
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: datafinder-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: datafinder-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Deploy to Kubernetes

```bash
# Create secrets
kubectl create secret generic datafinder-secrets \
  --from-literal=database-url='postgresql://...' \
  --from-literal=api-key='...' \
  --from-literal=groq-api-key='...'

# Create ConfigMap for non-secret config
kubectl create configmap datafinder-config \
  --from-literal=app-env=production \
  --from-literal=log-level=INFO

# Apply deployment
kubectl apply -f k8s/deployment.yaml

# Check rollout status
kubectl rollout status deployment/datafinder-api

# View pods
kubectl get pods -l app=datafinder-api

# View logs
kubectl logs -f deployment/datafinder-api --all-containers=true

# Forward port for testing
kubectl port-forward svc/datafinder-api 8000:80
```

---

## Cloud Platforms

### AWS ECS (Elastic Container Service)

**Registration**:

```bash
# Create ECR repository
aws ecr create-repository --repository-name datafinder-ai --region us-east-1

# Push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag datafinder-ai:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/datafinder-ai:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/datafinder-ai:latest
```

**Task Definition**:

```json
{
  "family": "datafinder-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/datafinder-ai:latest",
      "portMappings": [{ "containerPort": 8000, "hostPort": 8000 }],
      "environment": [
        { "name": "APP_ENV", "value": "production" },
        { "name": "DEBUG", "value": "false" }
      ],
      "secrets": [
        {
          "name": "API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxx:secret:datafinder/api-key"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:xxx:secret:datafinder/db-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/datafinder-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/<project-id>/datafinder-ai

# Deploy
gcloud run deploy datafinder-api \
  --image gcr.io/<project-id>/datafinder-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars API_KEY=<value>,GROQ_API_KEY=<value> \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 100 \
  --min-instances 1 \
  --max-instances 10
```

### Azure Container Instances

```bash
# Create resource group
az group create --name datafinder --location eastus

# Push to ACR
az acr build --registry <registry-name> --image datafinder-ai:latest .

# Deploy container
az container create \
  --resource-group datafinder \
  --name datafinder-api \
  --image <registry-name>.azurecr.io/datafinder-ai:latest \
  --cpu 2 \
  --memory 2 \
  --port 8000 \
  --environment-variables API_KEY=<value> GROQ_API_KEY=<value>
```

### Render.com

```bash
# Create .render.yaml
# Deploy via Git (Render auto-rebuilds on push)
# Set environment variables in dashboard
# Configure custom domain if needed
```

---

## Monitoring & Observability

### Health Checks

```bash
# Liveness (is API running?)
curl http://localhost:8000/health

# Readiness (is API ready to serve requests?)
curl http://localhost:8000/ready

# Metrics (Prometheus format)
curl http://localhost:8000/metrics

# Circuit breaker status
curl http://localhost:8000/circuit-breaker
```

### Prometheus Configuration (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "datafinder-api"
    static_configs:
      - targets: ["localhost:8000"]
    metrics_path: "/metrics"
```

### Grafana Dashboards

1. Access Grafana: `http://localhost:3000`
2. Add Prometheus data source: `http://prometheus:9090`
3. Import dashboard JSON (provided in monitoring/)
4. Configure alerts for critical metrics

### Log Aggregation (ELK Stack)

```bash
# Logs are JSON-formatted for easy parsing
# Send to Elasticsearch:

curl -X POST "localhost:9200/datafinder-logs/_doc" \
  -H 'Content-Type: application/json' \
  -d @log-entry.json
```

### Alerting Rules

```yaml
groups:
  - name: datafinder
    rules:
      - alert: HighErrorRate
        expr: http_requests_total{status_code=~"5.."}  > 100
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: SlowResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 5
        for: 10m
        annotations:
          summary: "Slow response times detected"

      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state{state="open"} == 1
        for: 1m
        annotations:
          summary: "Circuit breaker open for {{ $labels.service }}"
```

---

## Security

### API Key Rotation

```bash
# Generate new key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update API_KEY in secrets manager
# Restart API gradually (rolling restart)
```

### HTTPS/TLS (Nginx Reverse Proxy)

```nginx
upstream datafinder {
    server api:8000;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://datafinder;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Security headers
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }

    # Redirect HTTP to HTTPS
}

server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}
```

### Database Security

- Use strong passwords (min 20 characters)
- Enable SSL for PostgreSQL connections
- Restrict database access to API servers only
- Regular backups to secure location
- Enable query logging for audit trail

### Secret Management

```bash
# .env.example (DO NOT include secrets)
# .env (local development, DO NOT commit)
# Secrets Manager (production)

# AWS Secrets Manager
aws secretsmanager create-secret --name datafinder/api-key

# HashiCorp Vault
vault kv put secret/datafinder api_key="xxx"

# Azure Key Vault
az keyvault secret set --vault-name datafinder-kv --name api-key
```

---

## Troubleshooting

### API Not Starting

```bash
# Check logs
docker logs <container-id>
kubectl logs <pod-name>

# Verify environment variables
docker inspect <container-id> | grep Env

# Check database connection
python -c "from app.database.db import engine; engine.execute('SELECT 1')"
```

### High Latency

```bash
# Check metrics
curl http://localhost:8000/metrics | grep http_request_duration

# Check circuit breaker status
curl http://localhost:8000/circuit-breaker

# Check database performance
python -c "from app.database.db import SessionLocal; print(SessionLocal().execute('SELECT NOW()'))"
```

### Memory Leaks

```bash
# Monitor memory usage
docker stats <container-id>

# Enable memory profiling
export PYTHONMALLOC=debug
# Restart container
```

### Failing External API Calls

```bash
# Check circuit breaker status
curl http://localhost:8000/circuit-breaker

# Temporarily disable circuit breaker for testing
# (not recommended in production)
```

---

## Maintenance

### Regular Tasks

- [ ] Weekly: Review logs for errors
- [ ] Daily: Monitor metrics dashboards
- [ ] Monthly: Rotate API keys
- [ ] Monthly: Security scan
- [ ] Quarterly: Database optimization
- [ ] Quarterly: Dependency updates

### Backup Strategy

```bash
# Backup FAISS index
tar -czf faiss-index-$(date +%Y%m%d).tar.gz data/datasets.faiss data/*.json

# Backup database
pg_dump <database> | gzip > database-$(date +%Y%m%d).sql.gz

# Upload to S3
aws s3 cp faiss-index-*.tar.gz s3://backups/
aws s3 cp database-*.sql.gz s3://backups/
```

---

## Performance Tuning

### Resource Allocation

```yaml
# Recommended for different scales

# Small (<10K datasets, <100 QPS)
cpu: 500m
memory: 512Mi
workers: 2

# Medium (100K datasets, 100-500 QPS)
cpu: 1000m
memory: 2Gi
workers: 4

# Large (>500K datasets, 500+ QPS)
cpu: 4000m
memory: 8Gi
workers: 8
```

### Database Connection Pool

```python
# In config.py
SQLALCHEMY_POOL_SIZE = 20  # Number of connections in pool
SQLALCHEMY_MAX_OVERFLOW = 40  # Max overflow connections
SQLALCHEMY_POOL_RECYCLE = 3600  # Recycle connections every hour
```

### Caching Strategy

```python
# Cache embeddings in Redis
REDIS_URL = "redis://localhost:6379/0"
CACHE_EMBEDDING_TTL = 86400  # 24 hours
```

---

For more help, see `TECHNICAL_REVIEW.md` for architecture details.
