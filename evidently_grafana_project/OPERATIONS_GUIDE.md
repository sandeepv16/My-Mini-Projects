# Drift Monitoring - Operations Guide

## Project Structure

### Required Files (Production)

```
drift_monitoring/
├── dags/
│   ├── drift_monitoring_dag.py    (Main drift detection workflow)
│   └── train_model_dag.py         (Model training workflow)
├── monitoring/
│   ├── drift_detector.py          (Drift detection logic)
│   └── __init__.py
├── scripts/
│   ├── train_clv_model.py         (Model training script)
│   └── __init__.py
├── config/
│   ├── init-metadata-db.sql
│   ├── init-mysql-db.sql
│   └── airflow.cfg
├── docker-compose.yml             (Service orchestration)
├── requirements.txt               (Python dependencies)
└── data/
    ├── reference/                 (Reference dataset)
    └── current/                   (Current dataset)
```

### Utility/Documentation Files (Optional but Useful)

- `validate_metrics.py` - Verify metrics instrumentation
- `QUICKSTART.md` - Setup and execution guide
- `ARCHITECTURE.md` - System design overview
- `METRICS_QUICK_REFERENCE.md` - Metrics documentation

---

## Normal Operation

### Prerequisites

```bash
# Windows PowerShell
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 1.29+
```

### 1. Start All Services

```bash
cd drift_monitoring
docker-compose up -d
```

**Expected Output:**
```
[+] Running 8/8
  ✓ postgres (healthy)
  ✓ mysql (healthy)
  ✓ airflow-webserver
  ✓ airflow-scheduler
  ✓ prometheus
  ✓ pushgateway
  ✓ grafana
  ✓ loki
  ✓ promtail
```

**Verify all services:**
```bash
docker-compose ps
```

### 2. Access Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8080 | airflow / airflow |
| Prometheus | http://localhost:9090 | (no auth) |
| Grafana | http://localhost:3000 | admin / admin |
| Pushgateway | http://localhost:9091 | (metrics endpoint) |

### 3. Train Initial Model

**Option A: Via Airflow DAG (Recommended)**

1. Open Airflow UI: http://localhost:8080
2. Navigate to DAGs
3. Find `train_clv_model` DAG
4. Click **Trigger DAG** (or use API):

```bash
curl -X POST http://localhost:8080/api/v1/dags/train_clv_model/dagRuns \
  -H "Content-Type: application/json" \
  -d '{"conf":{}}' \
  -u airflow:airflow
```

5. Wait 2-3 minutes for completion
6. Verify model files created:

```bash
docker exec drift_monitoring-airflow-webserver-1 ls -la /opt/airflow/models/
```

**Option B: Direct Command**

```bash
docker exec drift_monitoring-airflow-webserver-1 \
  python /opt/airflow/scripts/train_clv_model.py
```

**Expected Output:**
- Model files in `/opt/airflow/models/`:
  - `clv_model.pkl`
  - `scaler.pkl`

### 4. Enable Drift Detection Monitoring

1. Open Airflow UI: http://localhost:8080
2. Find `clv_drift_monitoring` DAG
3. Enable it (toggle in DAG list)
4. It will run on schedule (every 6 hours by default)

**Or trigger manually:**

```bash
curl -X POST http://localhost:8080/api/v1/dags/clv_drift_monitoring/dagRuns \
  -H "Content-Type: application/json" \
  -d '{"conf":{}}' \
  -u airflow:airflow
```

### 5. Monitor Metrics

**In Prometheus:**
```bash
# Access http://localhost:9090
# Query examples:
clv_drift_score
clv_drifted_columns_count
clv_drift_detected_total
clv_model_performance
```

**Check metric push:**
```bash
curl http://localhost:9091/metrics | grep clv_
```

**In Grafana:**
1. Open http://localhost:3000
2. Navigate to Dashboards
3. Select "CLV Drift Dashboard"
4. View metrics visualization

### 6. View Logs

**Airflow logs:**
```bash
docker-compose logs airflow-webserver -f --tail=100
docker-compose logs airflow-scheduler -f --tail=100
```

**Prometheus targets status:**
```
http://localhost:9090/targets
```

---

## Generating Drift Data

### Scenario: Simulate Data Drift and Model Drift

Use the included **create_drift_raw_data.py** script to generate synthetic drift data:

```bash
docker exec drift_monitoring-airflow-webserver-1 \
  python /opt/airflow/create_drift_raw_data.py
```

**What it does:**
1. Reads original reference data (Online_Retail.csv)
2. Creates synthetic drift by:
   - **Data Drift**: Multiplies quantities and prices (1.5-3x increase)
   - **Model Drift**: Adds 10% extreme outliers (nonsensical values)
3. Saves as `current_data.csv` for drift detection

**Expected Output:**
```
Raw data shape: (541909, 8)
Columns: ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country']

CREATING DATA DRIFT
Quantity: Increased by 1.5-3x (mean 9.55 → 4,557.25)
UnitPrice: Increased by 1.3-2.5x (mean 4.61 → 5,032.60)

CREATING MODEL DRIFT
Adding outliers to 54190 rows (10.0%)
Quantity: Added extreme outliers (-9999 or 99999)
UnitPrice: Added extreme outliers (0.01-100000)

✅ Drift data saved to /opt/airflow/data/current/current_data.csv
Rows: 541909, Columns: 8
```

### After Drift Generation

1. **Trigger drift detection:**

```bash
curl -X POST http://localhost:8080/api/v1/dags/clv_drift_monitoring/dagRuns \
  -H "Content-Type: application/json" \
  -d '{"conf":{}}' \
  -u airflow:airflow
```

2. **Wait 30 seconds** for DAG execution

3. **Check Prometheus metrics:**

```bash
curl http://localhost:9091/metrics | grep clv_drift
```

Expected to see non-zero values:
- `clv_drift_detected_total` (counters incrementing)
- `clv_drift_score` (high values indicating significant drift)
- `clv_drifted_columns_count` (number of drifted features)

4. **View in Grafana:**
   - Open http://localhost:3000
   - Check "CLV Drift Dashboard"
   - Both "Data Drift Events" and "Model Drift Events" panels should show metrics

5. **View drift report:**

```bash
docker exec drift_monitoring-airflow-webserver-1 \
  ls -la /opt/airflow/monitoring/reports/
```

---

## Complete Workflow Timeline

### Normal Operation (6-hour intervals)

```
00:00 - Drift monitoring DAG scheduled run
00:05 - Load reference data (original)
00:10 - Load current data (from data/current/)
00:15 - Run Evidently drift detection
00:20 - Generate drift report
00:25 - Push metrics to Prometheus
00:30 - Prometheus scrapes metrics
00:35 - Grafana updates dashboard
00:40 - Complete (ready for next cycle)
```

### Manual Drift Test (with generated drift)

```
00:00 - Run create_drift_raw_data.py
00:05 - Drift data written to /opt/airflow/data/current/
00:10 - Trigger clv_drift_monitoring DAG
00:15 - DAG loads reference + current data (with drift)
00:20 - Evidently detects significant drift
00:25 - Metrics show: drift_score=high, drifted_columns_count>0
00:30 - Metrics pushed to Prometheus Pushgateway
00:45 - Prometheus scrapes metrics
01:00 - Grafana dashboard updates
01:15 - View complete drift report
```

---

## Maintenance Tasks

### View Drift Reports

```bash
docker exec drift_monitoring-airflow-webserver-1 \
  cat /opt/airflow/monitoring/reports/latest_drift_report.json
```

### Reset to Clean State

```bash
# Remove current drift data (revert to reference)
docker exec drift_monitoring-airflow-webserver-1 \
  cp /opt/airflow/data/reference/reference_data.csv \
     /opt/airflow/data/current/current_data.csv

# Trigger drift detection (should show no drift)
curl -X POST http://localhost:8080/api/v1/dags/clv_drift_monitoring/dagRuns \
  -H "Content-Type: application/json" \
  -d '{"conf":{}}' \
  -u airflow:airflow
```

### Check Service Health

```bash
# All services
docker-compose ps

# Prometheus targets
curl http://localhost:9090/api/v1/targets

# Pushgateway metrics
curl http://localhost:9091/metrics | head -20

# Airflow tasks
curl -s http://localhost:8080/api/v1/dags/clv_drift_monitoring/dagRuns \
  -u airflow:airflow | grep -o '"state":"[^"]*"'
```

### Stop Services

```bash
docker-compose down
```

### Restart Services

```bash
docker-compose restart
```

### View Logs

```bash
# Airflow webserver
docker-compose logs airflow-webserver -f --tail=50

# Airflow scheduler
docker-compose logs airflow-scheduler -f --tail=50

# Prometheus
docker-compose logs prometheus -f --tail=50

# All services
docker-compose logs -f --tail=100
```

---

## Troubleshooting

### Issue: "No data in Grafana dashboard"

**Solution:**
1. Verify model trained: `docker-compose exec airflow-webserver ls models/`
2. Verify reference data: `docker-compose exec airflow-webserver wc -l data/reference/*.csv`
3. Trigger DAG: Use curl command above
4. Wait 60 seconds
5. Check metrics: `curl http://localhost:9091/metrics | grep clv_`

### Issue: "DAG not running"

**Solution:**
1. Verify DAG enabled: Airflow UI → DAG list → toggle ON
2. Check logs: `docker-compose logs airflow-scheduler | grep clv_drift`
3. Verify no errors: `curl http://localhost:8080/api/v1/dags/clv_drift_monitoring -u airflow:airflow`

### Issue: "Prometheus targets down"

**Solution:**
1. Check targets: `curl http://localhost:9090/api/v1/targets`
2. Verify services running: `docker-compose ps`
3. Restart prometheus: `docker-compose restart prometheus`

### Issue: "Metrics not pushing"

**Solution:**
1. Check pushgateway: `curl http://localhost:9091/metrics`
2. Check DAG logs: `docker-compose logs airflow-scheduler`
3. Verify drift_detector.py has push_to_gateway calls

---

## File Cleanup Notes

**Removed (Temporary/Testing Files):**
- `generate_drift_data.py` - Initial attempt (superceded by create_drift_raw_data.py)
- `create_reference_data.py` - One-off RFM processing
- `create_drift_data_rfm.py` - One-off RFM drift generation
- `test_drift.py` - Development test script
- Duplicate/old QUICKSTART files

**Kept (Production/Reference):**
- `create_drift_raw_data.py` - Active script for drift generation
- `validate_metrics.py` - Metric verification utility
- All markdown documentation
- All DAGs and monitoring scripts

---

## Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# Train model
curl -X POST http://localhost:8080/api/v1/dags/train_clv_model/dagRuns \
  -H "Content-Type: application/json" -d '{"conf":{}}' -u airflow:airflow

# Generate drift
docker exec drift_monitoring-airflow-webserver-1 \
  python /opt/airflow/create_drift_raw_data.py

# Trigger drift detection
curl -X POST http://localhost:8080/api/v1/dags/clv_drift_monitoring/dagRuns \
  -H "Content-Type: application/json" -d '{"conf":{}}' -u airflow:airflow

# View metrics
curl http://localhost:9091/metrics | grep clv_

# View logs
docker-compose logs -f --tail=100

# Stop services
docker-compose down
```

---

**Last Updated:** January 16, 2026  
**Status:** Production Ready
