# CLV Drift Monitoring System

A comprehensive machine learning operations (MLOps) system for detecting drift in Customer Lifetime Value (CLV) prediction models and automatically triggering retraining when drift is detected.

## Overview

This project implements an end-to-end drift monitoring pipeline for CLV models using:

- **Evidently**: Data and model drift detection
- **Apache Airflow**: Workflow orchestration and automated retraining
- **Prometheus**: Metrics collection and monitoring
- **Loki**: Log aggregation
- **Grafana**: Metrics and log visualization

## Features

✅ **Customer Lifetime Value (CLV) Prediction**
- RFM (Recency, Frequency, Monetary) feature engineering
- Random Forest regression model
- Comprehensive customer behavior analysis

✅ **Drift Detection**
- Data drift monitoring using Evidently
- Model performance drift detection
- Automated HTML reports generation
- Configurable drift thresholds

✅ **Automated Retraining**
- Airflow DAGs for orchestration
- Automatic model retraining when drift is detected
- Model versioning and metadata tracking

✅ **Monitoring & Observability**
- Real-time metrics in Prometheus
- Centralized logging with Loki
- Pre-built Grafana dashboards
- Container metrics with cAdvisor

## Architecture

```
┌─────────────────────┐
│  Online_Retail.csv  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  CLV Model Training │ ◄── Airflow DAG (Weekly)
│   - Feature Eng.    │
│   - Model Training  │
│   - Reference Data  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Trained Model     │
│   Reference Data    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Drift Detection    │ ◄── Airflow DAG (Daily)
│   - Evidently       │
│   - Data Drift      │
│   - Model Drift     │
└──────────┬──────────┘
           │
           ├─── No Drift ──► Continue Monitoring
           │
           └─── Drift Detected ──► Trigger Retraining
                                    │
                                    ▼
                            ┌───────────────┐
                            │   Retrain     │
                            │   Model       │
                            └───────────────┘
           
┌─────────────────────────────────────────┐
│          Monitoring Stack               │
│  ┌──────────┐  ┌──────────┐             │
│  │Prometheus│  │   Loki   │             │
│  └────┬─────┘  └────┬─────┘             │
│       │             │                   │
│       └─────────┬───┘                   │
│                 ▼                       │
│          ┌──────────┐                   │
│          │ Grafana  │                   │
│          └──────────┘                   │
└─────────────────────────────────────────┘
```

## Project Structure

```
drift_monitoring/
├── Online_Retail.csv           # Input retail transaction data
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Multi-service orchestration
│
├── scripts/
│   └── train_clv_model.py     # CLV model training script
│
├── monitoring/
│   └── drift_detector.py      # Drift detection using Evidently
│
├── dags/
│   ├── train_model_dag.py     # Airflow DAG for training
│   └── drift_monitoring_dag.py # Airflow DAG for drift detection
│
├── config/
│   ├── prometheus.yml          # Prometheus configuration
│   ├── prometheus-rules.yml    # Prometheus alerting rules
│   ├── loki-config.yml        # Loki configuration
│   ├── promtail-config.yml    # Promtail log shipper config
│   └── grafana-datasources.yml # Grafana datasource config
│
├── grafana/
│   └── dashboards/
│       ├── dashboard-provider.yml
│       └── clv-drift-dashboard.json
│
├── models/                     # Saved models and metadata
├── data/
│   ├── reference/             # Reference data for drift detection
│   └── current/               # Current data for comparison
│
└── logs/                       # Airflow logs
```

## Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available for containers
- Python 3.10+ (if running locally)

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

### 1. Start All Services

```bash
# Set Airflow UID (Linux/Mac)
echo -e "AIRFLOW_UID=$(id -u)" > .env

# For Windows, create .env file manually:
# AIRFLOW_UID=50000

# Start all services
docker-compose up -d
```

### 2. Access Web Interfaces

- **Airflow**: http://localhost:8080 (airflow/airflow)
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

### 3. Train Initial Model

```bash
# Trigger the training DAG via Airflow UI or CLI
docker-compose exec airflow-webserver airflow dags trigger clv_model_training
```

### 4. Monitor Drift

The drift monitoring DAG runs daily automatically. View results in:
- Grafana Dashboard: "CLV Drift Monitoring Dashboard"
- Airflow UI: Task logs and execution history
- Reports: `monitoring/reports/` directory

## Key Components

### CLV Model Training (`scripts/train_clv_model.py`)

- Loads and preprocesses retail transaction data
- Calculates RFM features (Recency, Frequency, Monetary)
- Engineers additional customer behavior features
- Trains Random Forest regression model
- Saves model, scaler, and reference data

### Drift Detection (`monitoring/drift_detector.py`)

- Compares current data with reference data
- Uses Evidently for:
  - Data drift detection (feature distributions)
  - Model performance drift (R² score degradation)
- Generates HTML reports
- Pushes metrics to Prometheus

### Airflow DAGs

**Training DAG** (`train_model_dag.py`):
- Schedule: Weekly
- Tasks: Train CLV model, save artifacts

**Drift Monitoring DAG** (`drift_monitoring_dag.py`):
- Schedule: Daily
- Tasks:
  1. Check for new data
  2. Run drift detection
  3. Evaluate retraining need
  4. Trigger retraining if drift detected

## Monitoring Metrics

### Prometheus Metrics

- `clv_drift_detected_total{drift_type}`: Counter of drift events
- `clv_drift_score{feature}`: Number of drifted features
- `clv_model_performance{metric}`: Model performance (R², MAE, RMSE)

### Grafana Dashboard Panels

1. Data Drift Events (Gauge)
2. Model Drift Events (Gauge)
3. Model R² Score Over Time (Time Series)
4. Model Error Metrics (MAE, RMSE)
5. Drifted Features Count
6. Airflow Error Logs
7. Drift Detection Logs

## Configuration

### Drift Detection Thresholds

Edit `monitoring/drift_detector.py`:

```python
# R² drop threshold for model drift
r2_drop_threshold = 0.1  # 10% performance drop
```

### Alert Rules

Edit `config/prometheus-rules.yml` to customize alerting thresholds.

### DAG Schedules

Edit DAG files to change execution frequency:

```python
schedule_interval='@weekly'  # or '@daily', '@hourly', etc.
```

## Data Pipeline

### Input Data Format

The `Online_Retail.csv.csv` file should contain:

- `InvoiceNo`: Transaction identifier
- `StockCode`: Product code
- `Description`: Product description
- `Quantity`: Number of items
- `InvoiceDate`: Transaction timestamp (format: DD-MM-YYYY HH:MM)
- `UnitPrice`: Price per unit
- `CustomerID`: Customer identifier
- `Country`: Customer country

### Feature Engineering

The system automatically calculates:

- **Recency**: Days since last purchase
- **Frequency**: Number of transactions
- **Monetary**: Total spending
- **AvgQuantity**: Average items per transaction
- **TotalQuantity**: Total items purchased
- **AvgUnitPrice**: Average price per item
- **NumOrders**: Unique order count
- **NumProducts**: Unique products purchased
- **Country**: One-hot encoded country features

### CLV Calculation

```
CLV = Monetary × (Frequency / (Recency + 1)) × 365
```

## Troubleshooting

### Airflow Not Starting

```bash
# Check logs
docker-compose logs airflow-scheduler

# Reinitialize database
docker-compose down -v
docker-compose up -d
```

### Prometheus Not Scraping Metrics

```bash
# Check Prometheus targets
# Visit http://localhost:9090/targets

# Verify pushgateway is running
docker-compose ps pushgateway
```

### Grafana Dashboard Not Loading

```bash
# Check datasources
# Grafana UI → Configuration → Data Sources

# Verify Prometheus and Loki connections
docker-compose logs grafana
```

### Memory Issues

```bash
# Reduce resource usage in docker-compose.yml
# Or increase Docker memory limit in Docker Desktop settings
```

## Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Train model locally
python scripts/train_clv_model.py Online_Retail.csv.csv

# Run drift detection
python monitoring/drift_detector.py Online_Retail.csv.csv
```

### Adding New Features

1. Update `train_clv_model.py` with new feature engineering
2. Retrain model to generate new reference data
3. Update drift detection to include new features
4. Adjust Grafana dashboard to visualize new metrics

## Best Practices

✅ **Regular Model Training**: Schedule weekly retraining to keep model fresh

✅ **Monitor Drift Daily**: Daily drift checks catch issues early

✅ **Review Reports**: Examine Evidently HTML reports for detailed insights

✅ **Set Up Alerts**: Configure Prometheus alerts for critical drift events

✅ **Backup Models**: Version control model artifacts and metadata

✅ **Log Everything**: Use Loki for centralized log analysis

## Performance Optimization

- **Data Sampling**: For large datasets, sample data for drift detection
- **Feature Selection**: Monitor only critical features to reduce computation
- **Batch Processing**: Process data in batches for memory efficiency
- **Caching**: Cache reference data to avoid repeated loading

## Security Considerations

⚠️ **Default Passwords**: Change default passwords in production:
- Airflow: `airflow/airflow`
- Grafana: `admin/admin`
- PostgreSQL: `airflow/airflow`

⚠️ **Network Security**: Use proper network isolation in production

⚠️ **Data Privacy**: Ensure compliance with data protection regulations

## Contributing

Contributions welcome! Areas for improvement:

- Additional drift detection algorithms
- More sophisticated retraining strategies
- Enhanced alerting mechanisms
- Integration with MLflow for experiment tracking
- Support for other ML frameworks

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- Open an issue in the repository
- Review the [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Check [QUICKSTART.md](QUICKSTART.md) for setup help

## Acknowledgments

- **Evidently**: Drift detection framework
- **Apache Airflow**: Workflow orchestration
- **Prometheus/Grafana**: Monitoring stack
- **Loki**: Log aggregation

---

**Note**: This is a demonstration project. For production use, implement proper security, scalability, and monitoring practices.
