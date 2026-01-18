# Architecture Documentation - CLV Drift Monitoring System

## System Overview

The CLV Drift Monitoring System is a comprehensive MLOps platform that implements automated drift detection and model retraining for Customer Lifetime Value prediction models. The system follows microservices architecture with containerized components orchestrated via Docker Compose.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                  │
│  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐    │
│  │ Online_Retail    │  │  Reference      │  │   Current        │    │
│  │ CSV (Input)      │  │  Data           │  │   Data           │    │
│  └──────────────────┘  └─────────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ML Training Layer                              │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              CLV Model Training (train_clv_model.py)          │  │
│  │  • RFM Feature Engineering                                    │  │
│  │  • Random Forest Regression                                   │  │
│  │  • Model Serialization (joblib)                               │  │
│  │  • Reference Data Generation                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Drift Detection Layer                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │           Evidently Drift Detector (drift_detector.py)        │  │
│  │  • Data Drift Analysis                                        │  │
│  │  • Model Performance Drift                                    │  │
│  │  • HTML Report Generation                                     │  │
│  │  • Prometheus Metrics Export                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Orchestration Layer (Airflow)                     │
│  ┌──────────────────────┐    ┌──────────────────────────────────┐   │
│  │  Training DAG        │    │  Drift Monitoring DAG            │   │
│  │  (Weekly)            │    │  (Daily)                         │   │
│  │  • Train Model       │    │  • Check New Data                │   │
│  │  • Save Artifacts    │    │  • Detect Drift                  │   │
│  │                      │    │  • Evaluate Retraining Need      │   │
│  │                      │    │  • Trigger Retraining            │   │
│  └──────────────────────┘    └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Monitoring & Observability Layer                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│  │Prometheus│  │   Loki   │  │ Grafana  │  │   Pushgateway    │     │
│  │(Metrics) │  │  (Logs)  │  │(Visualiz)│  │  (Push Metrics)  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Data Processing Components

#### Input Data Handler
- **File**: `Online_Retail.csv`
- **Format**: CSV with retail transaction records
- **Columns**: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country
- **Volume Mount**: `/opt/airflow/Online_Retail.csv`

#### Data Storage
- **Reference Data**: `data/reference/reference_data.csv`
  - Baseline data for drift comparison
  - Generated during initial training
  - Updated on retraining
  
- **Current Data**: `data/current/*.csv`
  - New data for drift detection
  - Monitored by Airflow sensor
  
- **Models**: `models/`
  - Trained model artifacts (`.joblib`)
  - Feature scalers
  - Metadata (JSON)
  - Versioned by timestamp

### 2. Machine Learning Components

#### CLV Model Trainer (`scripts/train_clv_model.py`)

**Class**: `CLVModelTrainer`

**Key Methods**:
- `load_data()`: Load and clean retail data
- `calculate_rfm_features()`: Compute RFM metrics
- `prepare_features()`: Feature engineering and encoding
- `train_model()`: Train Random Forest regressor
- `save_model()`: Serialize model artifacts
- `save_reference_data()`: Store baseline data

**Feature Engineering**:
```python
Features = [
    'Recency',           # Days since last purchase
    'Frequency',         # Number of transactions
    'Monetary',          # Total spending
    'AvgQuantity',       # Average items per transaction
    'TotalQuantity',     # Total items purchased
    'AvgUnitPrice',      # Average price per item
    'NumOrders',         # Unique order count
    'NumProducts',       # Unique products purchased
    'Country_*'          # One-hot encoded countries
]
```

**Model**: Random Forest Regressor
```python
RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42
)
```

**Target Variable**: CLV (Customer Lifetime Value)
```python
CLV = Monetary × (Frequency / (Recency + 1)) × 365
```

### 3. Drift Detection Components

#### Drift Detector (`monitoring/drift_detector.py`)

**Class**: `DriftDetector`

**Key Methods**:
- `load_reference_data()`: Load baseline data
- `load_model()`: Load trained model artifacts
- `load_current_data()`: Process new data
- `detect_data_drift()`: Evidently data drift analysis
- `detect_model_drift()`: Model performance comparison
- `push_metrics_to_prometheus()`: Export metrics

**Evidently Reports**:

1. **Data Drift Report**:
   - `DataDriftPreset()`: Overall drift analysis
   - `DatasetDriftMetric()`: Dataset-level drift
   - `DatasetMissingValuesMetric()`: Missing value analysis
   - `DatasetCorrelationsMetric()`: Correlation changes

2. **Model Drift Report**:
   - `RegressionPreset()`: Regression metrics
   - `RegressionQualityMetric()`: Quality assessment
   - `RegressionPredictedVsActualScatter()`: Prediction scatter
   - `RegressionErrorPlot()`: Error distribution

**Drift Criteria**:
- **Data Drift**: Statistical tests on feature distributions
- **Model Drift**: R² score drop > 10%
- **Retraining Trigger**: Either drift type detected

**Prometheus Metrics**:
```python
# Counter metrics
clv_drift_detected_total{drift_type="data|model"}

# Gauge metrics
clv_drift_score{feature="dataset"}
clv_model_performance{metric="r2|mae|rmse"}
```

### 4. Orchestration Components

#### Airflow Architecture

**Database**: PostgreSQL
- Stores DAG metadata
- Task execution state
- User authentication

**Executor**: LocalExecutor
- Single machine execution
- Suitable for development/small workloads

**Components**:
1. **Webserver**: UI and API (port 8080)
2. **Scheduler**: DAG parsing and task scheduling
3. **Init**: Database initialization

#### Training DAG (`dags/train_model_dag.py`)

```python
DAG: clv_model_training
Schedule: @weekly
Tags: ['clv', 'training']

Tasks:
└── train_clv_model (PythonOperator)
    ├── Load data
    ├── Calculate features
    ├── Train model
    ├── Save artifacts
    └── XCom: Push training results
```

#### Drift Monitoring DAG (`dags/drift_monitoring_dag.py`)

```python
DAG: clv_drift_monitoring
Schedule: @daily
Tags: ['clv', 'monitoring', 'drift']

Tasks:
check_new_data (PythonOperator)
    │
    ▼
detect_drift (PythonOperator)
    │
    ▼
check_retraining_needed (BranchPythonOperator)
    │
    ├── Yes ──► log_retraining_trigger ──► trigger_retraining
    │                                          │
    │                                          ▼
    │                                    TriggerDagRunOperator
    │                                    (clv_model_training)
    │
    └── No ──► no_retraining_needed (Done)
```

**Decision Logic**:
```python
retraining_required = (
    data_drift_detected OR 
    model_drift_detected
)
```

### 5. Monitoring Components

#### Prometheus

**Configuration**: `config/prometheus.yml`

**Scrape Targets**:
- `prometheus:9090` - Self-monitoring
- `pushgateway:9091` - Drift metrics
- `airflow-webserver:8080` - Airflow metrics
- `node-exporter:9100` - System metrics
- `cadvisor:8080` - Container metrics

**Recording Rules**: `config/prometheus-rules.yml`
```yaml
- clv_data_drift_rate
- clv_model_drift_rate
- clv_model_r2_score
```

**Alert Rules**:
- `CLVDataDriftDetected`: Data drift warning
- `CLVModelDriftDetected`: Model drift critical
- `CLVModelPerformanceLow`: R² < 0.5 warning

#### Pushgateway

**Purpose**: Receive metrics from batch jobs (drift detection)
**Port**: 9091
**Protocol**: HTTP POST
**Endpoint**: `/metrics/job/<job_name>`

#### Loki

**Configuration**: `config/loki-config.yml`

**Storage**:
- Backend: Filesystem (BoltDB + Filesystem)
- Chunks: `/loki/chunks`
- Index: BoltDB Shipper

**Retention**:
- Period: 168 hours (7 days)
- Compaction: 10 minutes

**Ingestion Limits**:
- Rate: 10 MB/s
- Burst: 20 MB

#### Promtail

**Configuration**: `config/promtail-config.yml`

**Log Sources**:
- Airflow logs: `/var/log/airflow/**/*.log`

**Pipeline**:
```yaml
- regex: Extract timestamp, logger, level, message
- labels: Apply level and logger labels
- timestamp: Parse timestamp format
```

**Labels**:
- `job`: airflow
- `level`: INFO, WARNING, ERROR
- `logger`: Module/class name

#### Grafana

**Configuration**: `config/grafana-datasources.yml`

**Datasources**:
1. **Prometheus** (default)
   - URL: `http://localhost:9090` (Windows) or `http://prometheus:9090` (Docker)
   - Type: prometheus
   
2. **Loki**
   - URL: `http://localhost:3100` (Windows) or `http://loki:3100` (Docker)
   - Type: loki

**Dashboard**: `grafana/dashboards/clv-drift-dashboard.json`

**Panels**:
1. Data Drift Events (Gauge)
2. Model Drift Events (Gauge)
3. Model R² Score (Time Series)
4. Model Error Metrics (Time Series)
5. Drifted Features Count (Bar Chart)
6. Airflow Error Logs (Logs)
7. Drift Detection Logs (Logs)

#### Supporting Services

**Node Exporter**:
- System metrics (CPU, memory, disk, network)
- Port: 9100

**cAdvisor**:
- Container metrics
- Resource usage per container
- Port: 8081

## Data Flow

### Training Flow

```
1. Trigger: Airflow Scheduler (Weekly) or Manual
2. Load: Online_Retail.csv.csv
3. Process:
   a. Data cleaning (remove nulls, negatives)
   b. Feature engineering (RFM + additional)
   c. One-hot encode categorical
   d. Split train/test (80/20)
   e. Scale features (StandardScaler)
   f. Train Random Forest
   g. Evaluate (R², MAE, RMSE)
4. Save:
   a. Model → models/clv_model_latest.joblib
   b. Scaler → models/scaler_latest.joblib
   c. Features → models/features_latest.json
   d. Metadata → models/metadata_latest.json
   e. Reference → data/reference/reference_data.csv
5. XCom: Push results to Airflow
```

### Drift Detection Flow

```
1. Trigger: Airflow Scheduler (Daily) or Manual
2. Check: data/current/ for new CSV files
3. Load:
   a. Reference data (baseline)
   b. Current data (new)
   c. Trained model + scaler
4. Detect Data Drift:
   a. Compare feature distributions
   b. Statistical tests (KS test, Chi-square)
   c. Generate HTML report
   d. Count drifted features
5. Detect Model Drift:
   a. Make predictions on both datasets
   b. Calculate R² for both
   c. Compare performance drop
   d. Generate HTML report
6. Push Metrics:
   a. Send to Pushgateway
   b. Prometheus scrapes Pushgateway
7. Decision:
   IF drift_detected:
       Trigger retraining DAG
   ELSE:
       Continue monitoring
8. Save Results:
   a. JSON results → monitoring/reports/
   b. HTML reports → monitoring/reports/
```

### Monitoring Flow

```
1. Metrics Collection:
   Drift Detector → Pushgateway → Prometheus
   
2. Log Collection:
   Airflow Logs → Promtail → Loki
   
3. Visualization:
   Prometheus + Loki → Grafana Dashboards
   
4. Alerting:
   Prometheus → Alert Rules → (Future: Alertmanager)
```

## Deployment Architecture

### Container Network

**Network**: `monitoring` (bridge driver)

**Container Communication**:
```
airflow-webserver ←→ postgres
airflow-scheduler ←→ postgres
airflow-webserver ←→ pushgateway
prometheus ←→ pushgateway
prometheus ←→ airflow-webserver
prometheus ←→ node-exporter
prometheus ←→ cadvisor
promtail ←→ loki
grafana ←→ prometheus
grafana ←→ loki
```

### Volume Mounts

**Host → Container Mappings**:
```
./dags                    → /opt/airflow/dags
./logs                    → /opt/airflow/logs
./scripts                 → /opt/airflow/scripts
./monitoring              → /opt/airflow/monitoring
./models                  → /opt/airflow/models
./data                    → /opt/airflow/data
./Online_Retail.csv.csv   → /opt/airflow/Online_Retail.csv.csv
./config/prometheus.yml   → /etc/prometheus/prometheus.yml
./config/loki-config.yml  → /etc/loki/loki-config.yml
./grafana/dashboards      → /etc/grafana/provisioning/dashboards
```

**Persistent Volumes**:
- `postgres-db-volume`: Airflow metadata
- `prometheus-data`: Time series data
- `grafana-data`: Dashboards and settings
- `loki-data`: Log chunks and indexes

### Port Mappings

| Service | Internal Port | External Port | Purpose |
|---------|---------------|---------------|---------|
| Airflow Webserver | 8080 | 8080 | UI/API |
| Grafana | 3000 | 3000 | Dashboards |
| Prometheus | 9090 | 9090 | Metrics UI |
| Pushgateway | 9091 | 9091 | Push Metrics |
| Loki | 3100 | 3100 | Log Ingestion |
| Node Exporter | 9100 | 9100 | System Metrics |
| cAdvisor | 8080 | 8081 | Container Metrics |

## Security Considerations

### Current Implementation (Development)

⚠️ **Default Credentials**:
- Airflow: `airflow` / `airflow`
- Grafana: `admin` / `admin`
- PostgreSQL: `airflow` / `airflow`

⚠️ **No Authentication**:
- Prometheus (open access)
- Loki (no auth)
- Pushgateway (open push)

### Production Recommendations

1. **Authentication**:
   - Enable OAuth for Airflow
   - Use LDAP/SSO for Grafana
   - Implement API keys for Prometheus

2. **Network Security**:
   - Use internal Docker networks
   - Implement reverse proxy (Nginx/Traefik)
   - Enable TLS/SSL certificates

3. **Secrets Management**:
   - Use Docker Secrets or Vault
   - Encrypt sensitive environment variables
   - Rotate credentials regularly

4. **Access Control**:
   - Implement RBAC in Airflow
   - Set up Grafana organization roles
   - Use network policies

## Scalability Considerations

### Current Limitations

- **Single Node**: All services on one machine
- **LocalExecutor**: Limited to one Airflow worker
- **Filesystem Storage**: Not distributed

### Scaling Recommendations

1. **Airflow**:
   - Switch to CeleryExecutor or KubernetesExecutor
   - Add Redis for task queue
   - Multiple worker nodes

2. **Storage**:
   - Use S3/MinIO for model artifacts
   - Implement distributed Loki (microservices mode)
   - Cloud-based PostgreSQL (RDS)

3. **Monitoring**:
   - Prometheus federation for multiple instances
   - Thanos for long-term storage
   - Load-balanced Grafana

4. **Model Serving**:
   - Add model serving layer (MLflow, Seldon)
   - Implement A/B testing
   - Canary deployments

## Extension Points

### Adding New Features

1. **Custom Metrics**:
   - Define in `drift_detector.py`
   - Update Prometheus config
   - Add to Grafana dashboard

2. **New Drift Algorithms**:
   - Extend `DriftDetector` class
   - Integrate alternative libraries (AliBI Detect, Deepchecks)
   - Configure thresholds

3. **Additional Models**:
   - Create new training scripts
   - Add DAGs for new models
   - Separate monitoring pipelines

4. **Advanced Alerting**:
   - Configure Alertmanager
   - Set up notification channels (Slack, Email)
   - Define alert routing rules

5. **Experiment Tracking**:
   - Integrate MLflow
   - Track hyperparameters
   - Compare model versions

## Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Orchestration | Apache Airflow | 2.7.1 | Workflow management |
| ML Framework | scikit-learn | 1.3.0 | Model training |
| Drift Detection | Evidently | 0.4.10 | Drift analysis |
| Metrics | Prometheus | latest | Time series DB |
| Logging | Loki | latest | Log aggregation |
| Visualization | Grafana | latest | Dashboards |
| Database | PostgreSQL | 13 | Airflow metadata |
| Container | Docker | - | Containerization |
| Orchestrator | Docker Compose | 3.8 | Multi-container |

## Performance Metrics

### Resource Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB

**Recommended**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB

### Expected Performance

- **Model Training**: 2-5 minutes (depends on data size)
- **Drift Detection**: 1-3 minutes
- **Report Generation**: 30-60 seconds
- **Metrics Scraping**: 15 seconds interval
- **Log Ingestion**: Real-time (< 1 second latency)

---

This architecture provides a solid foundation for production-grade ML drift monitoring with clear separation of concerns and extensibility for future enhancements.
