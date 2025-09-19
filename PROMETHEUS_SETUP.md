# NLPForge Prometheus Monitoring Setup Guide

This guide shows you how to monitor your NLPForge API using Prometheus and Grafana.

## 🎯 Unified Monitoring Endpoint

**All monitoring functionality has been consolidated into a single endpoint with intelligent content negotiation.** This provides the best of both worlds - one endpoint that serves multiple formats based on the client's needs.

### Single Unified Endpoint: `/api/v1/health/`

**Content Negotiation Based on Accept Header:**

```bash
# JSON Format (Default) - For applications and dashboards
GET /api/v1/health/
Accept: application/json

# Prometheus Format - For metrics scraping
GET /api/v1/health/
Accept: text/plain
```

**What this means:**
- **Same URL** for both JSON health data and Prometheus metrics
- **Automatic format detection** based on what the client requests
- **Prometheus scrapers automatically get text format**
- **Browsers and applications automatically get JSON format**
- **No need for separate `/metrics` endpoints**

### Simple Health Check
```bash
GET /api/v1/health/simple
```
Returns basic status for load balancers and uptime monitoring.

## 📊 Unified Prometheus Metrics

**All metrics are now served from `/api/v1/health/`** with automatic content negotiation. When Prometheus scrapes this endpoint, it automatically gets the metrics format. This single endpoint provides comprehensive monitoring data:

### System Health Metrics
- `nlpforge_system_health_status` - Overall system health (1=healthy, 0=unhealthy)
- `nlpforge_database_health_status` - Database health status
- `nlpforge_rule_engine_health_status` - Rule Engine health status
- `nlpforge_up` - Application availability (1=up, 0=down)

### Performance Metrics
- `nlpforge_database_response_time_ms` - Database response time
- `nlpforge_rule_engine_response_time_ms` - Rule Engine response time

### Rule Engine Metrics
- `nlpforge_rule_engine_functions_total` - Number of available functions
- `nlpforge_rule_engine_patterns_total` - Number of active patterns
- `nlpforge_rule_engine_parses_total` - Total parse operations (counter)
- `nlpforge_rule_engine_config_issues_total` - Configuration issues

### System Resource Metrics
- `nlpforge_memory_usage_percent` - Memory usage percentage
- `nlpforge_memory_available_mb` - Available memory in MB
- `nlpforge_memory_total_mb` - Total memory in MB
- `nlpforge_cpu_usage_percent` - CPU usage percentage
- `nlpforge_process_id` - Current process ID

### Application Info
- `nlpforge_info` - Application metadata with version labels

## 🚀 Quick Setup

### Step 1: Test the Unified Endpoint

```bash
# Test Prometheus format (content negotiation)
curl -H "Accept: text/plain" http://localhost:8000/api/v1/health/

# Test JSON format (default)
curl http://localhost:8000/api/v1/health/
# or explicitly:
curl -H "Accept: application/json" http://localhost:8000/api/v1/health/

# Test with Python - Prometheus format
python -c "import requests; print(requests.get('http://localhost:8000/api/v1/health/', headers={'Accept': 'text/plain'}).text)"

# Test with Python - JSON format  
python -c "import requests; print(requests.get('http://localhost:8000/api/v1/health/').json())"
```

### Step 2: Install Prometheus

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.windows-amd64.zip

# Extract and use the provided prometheus-config.yml
prometheus.exe --config.file=prometheus-config.yml
```

### Step 3: Configure Prometheus

Use the provided `prometheus-config.yml` file which is already configured to scrape:
- Your NLPForge API at `localhost:8000/api/v1/health/` (unified endpoint)
- Every 10 seconds with 5 second timeout
- **Automatic content negotiation**: Prometheus automatically gets metrics format from the same endpoint

### Step 4: Install Grafana (Optional)

```bash
# Download Grafana
# Import the provided grafana-dashboard.json for ready-to-use dashboards
```

## 📈 Sample Queries

### Prometheus Queries
```promql
# Check if application is up
nlpforge_up

# Database response time over time
rate(nlpforge_database_response_time_ms[5m])

# Rule Engine performance
nlpforge_rule_engine_functions_total

# Memory usage alert (>80%)
nlpforge_memory_usage_percent > 80

# System health status
nlpforge_system_health_status{component="overall"}
```

### Alerting Rules Example
```yaml
groups:
- name: nlpforge_alerts
  rules:
  - alert: NLPForgeDown
    expr: nlpforge_up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "NLPForge API is down"
      
  - alert: HighMemoryUsage
    expr: nlpforge_memory_usage_percent > 85
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
      
  - alert: DatabaseSlow
    expr: nlpforge_database_response_time_ms > 1000
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "Database response time is slow"
```

## 🔧 Integration Examples

### Docker Compose with Monitoring Stack
```yaml
version: '3.8'
services:
  nlpforge-api:
    build: .
    ports:
      - "8000:8000"
    
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus-config.yml:/etc/prometheus/prometheus.yml
    
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Kubernetes ServiceMonitor
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: nlpforge-api
spec:
  selector:
    matchLabels:
      app: nlpforge-api
  endpoints:
  - port: http
    path: /api/v1/health/metrics
    interval: 30s
```

## 🎛️ Status Levels

The metrics use these numeric values for status:
- `1.0` = healthy
- `0.75` = warning  
- `0.5` = degraded
- `0.25` = critical
- `0.0` = unhealthy

## 🔍 Troubleshooting

### Check if the unified endpoint is working:
```bash
# Test Prometheus format (content negotiation)
curl -v -H "Accept: text/plain" http://localhost:8000/api/v1/health/

# Test JSON format (default)
curl -v http://localhost:8000/api/v1/health/
```

### Verify Prometheus is scraping:
1. Go to http://localhost:9090/targets
2. Look for your nlpforge-api target
3. Status should be "UP"

### Common Issues:
- **Metrics not appearing**: Check if the API is running and accessible at `/api/v1/health/`
- **Prometheus can't scrape**: Verify the unified `/api/v1/health/` endpoint is accessible
- **Wrong data format**: The same endpoint returns different formats based on Accept header
- **Content negotiation not working**: Ensure your client sends proper Accept headers (`text/plain` for Prometheus, `application/json` for JSON)

## 📊 Dashboard Examples

The **consolidated health endpoint** provides all data needed for comprehensive dashboards showing:
- System uptime and availability
- Response time trends  
- Resource utilization over time
- Rule Engine performance metrics
- Database health and response times
- Alert status and history

**Migration Note**: All monitoring functionality is now unified into `/api/v1/health/` with intelligent content negotiation - no separate endpoints needed!

Use the provided Grafana dashboard JSON as a starting point for your monitoring setup.