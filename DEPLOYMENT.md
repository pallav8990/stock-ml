# Stock-ML Deployment Guide

This guide covers deployment options for the Stock-ML pipeline in production infrastructure.

## Quick Start

### Local Development
```bash
# Clone and setup
git clone <your-repo>
cd stock-ml
./setup.sh

# Start API server
uvicorn app.serve:app --host 0.0.0.0 --port 8000

# Start scheduler (in separate terminal)
python pipeline/scheduler.py
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t stock-ml .
docker run -p 8000:8000 -v $(pwd)/data:/app/data stock-ml
```

## Infrastructure Requirements

### Minimum Resources
- **CPU**: 1-2 vCPU
- **RAM**: 2-4 GB
- **Storage**: 10 GB (for data and models)
- **Network**: Outbound HTTPS access for NSE/RSS data

### Recommended Production
- **CPU**: 2-4 vCPU  
- **RAM**: 4-8 GB
- **Storage**: 50+ GB SSD
- **Network**: Load balancer, firewall rules

## Environment Configuration

### Required Files
- `conf/schedule.yaml` - Pipeline timing (IST timezone)
- `conf/news_sources.yaml` - RSS feed URLs

### Data Persistence
The `data/` directory contains:
- `universe.parquet` - NSE stock universe
- `prices_daily.parquet` - Daily price data
- `news_daily.parquet` - Sentiment-scored news
- `features_daily.parquet` - Technical indicators + news features
- `predictions_daily.parquet` - Next-day return predictions
- `eval_explain_daily.parquet` - SHAP explanations
- `model.joblib` - Trained LightGBM model

**Important**: Mount `data/` as persistent volume in containerized deployments.

## Deployment Options

### 1. Cloud VM (Recommended)
```bash
# Example: AWS EC2, GCP Compute Engine, Azure VM
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Deploy
git clone <your-repo>
cd stock-ml
docker-compose up -d
```

### 2. Kubernetes
```yaml
# stock-ml-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stock-ml
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stock-ml
  template:
    metadata:
      labels:
        app: stock-ml
    spec:
      containers:
      - name: stock-ml
        image: stock-ml:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: data-storage
          mountPath: /app/data
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: stock-ml-data
```

### 3. Serverless (API Only)
For serverless deployment (AWS Lambda, Google Cloud Run), the scheduler component needs separate handling:
- Deploy API as serverless function
- Use cloud scheduler (CloudWatch Events, Cloud Scheduler) for pipeline automation
- Store data in cloud storage (S3, GCS) instead of local files

## Pipeline Automation

### Scheduler Configuration
Edit `conf/schedule.yaml`:
```yaml
collect_hour: 9    # Data collection time (IST)
collect_minute: 0
train_hour: 9      # Model training time
train_minute: 10
predict_hour: 9    # Prediction time  
predict_minute: 15
evaluate_hour: 9   # Evaluation time (next day)
evaluate_minute: 0
```

### Manual Pipeline Run
```bash
# Full pipeline (use for backfilling or testing)
python pipeline/build_universe.py
python pipeline/collect_prices_nse.py  
python pipeline/collect_news.py
python pipeline/build_features.py
python pipeline/train_model.py
python pipeline/predict.py
python pipeline/evaluate_and_explain.py
```

## API Endpoints

- `GET /` - Health check
- `GET /predict_today` - Latest predictions
- `GET /explain_gap` - SHAP explanations for prediction gaps
- `GET /accuracy_by_stock?window=60` - Performance metrics

## Monitoring and Logging

### Health Checks
```bash
curl http://localhost:8000/
# Expected: {"status":"ok","message":"Stock ML (analysis-only)..."}
```

### Log Monitoring
- Pipeline logs: Check container/process logs for data collection issues
- API logs: Monitor FastAPI access and error logs
- Model performance: Use `/accuracy_by_stock` endpoint

### Key Metrics
- Data freshness: Check latest date in predictions
- Model accuracy: Monitor MAPE and directional accuracy
- System health: API response times and error rates

## Security Considerations

### Network Security
- Restrict API access to authorized clients only
- Use HTTPS in production (reverse proxy/load balancer)
- Firewall rules: Allow outbound HTTPS for data collection

### Data Security
- No sensitive financial data stored (only public market data)
- Regular backups of model and historical data
- Rotate API keys if using external data services

### Compliance
**Disclaimer**: This system is for analysis only, not investment advice. Ensure compliance with:
- Market data usage terms
- Regional financial regulations
- Data privacy requirements

## Troubleshooting

### Common Issues

**NSE SSL Errors**: 
- Mock data fallback is implemented
- Real deployment may need SSL certificate updates

**Memory Issues**:
- Increase container memory limits
- Optimize feature engineering for large datasets

**Timezone Issues**:
- Scheduler uses IST (`Asia/Kolkata`)
- Ensure system timezone is configured correctly

**API Errors**:
- Check data file permissions in `/app/data/`
- Verify all pipeline steps completed successfully

## Scaling Considerations

### Horizontal Scaling
- API server: Multiple replicas behind load balancer
- Pipeline: Single instance (data consistency)
- Database: Consider PostgreSQL/MongoDB for multi-instance deployments

### Performance Optimization
- Cache model predictions for repeated requests  
- Batch process multiple stocks together
- Use Redis for session/temporary data storage

## Backup and Disaster Recovery

### Data Backup
```bash
# Backup critical data files
tar -czf stock-ml-backup-$(date +%Y%m%d).tar.gz data/
```

### Recovery Process
1. Restore data files from backup
2. Run pipeline to catch up missing days
3. Verify API functionality and predictions

For production deployments, consider automated daily backups and offsite storage.