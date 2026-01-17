# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Start the Services
```powershell
# Navigate to project directory
cd c:\Users\ADMIN\SV_Practice_06102024\Self_Learning\MyProjects\airflow_project

# Start all Docker containers
docker-compose up -d

# Wait 2-3 minutes for initialization
```

### Step 2: Verify Setup
```powershell
# Check if all services are running
docker-compose ps

# Optional: Run health check script
pip install requests mysql-connector-python psycopg2-binary
python check_setup.py
```

### Step 3: Access Airflow UI
1. Open browser: **http://localhost:8080**
2. Login:
   - Username: `airflow`
   - Password: `airflow`

### Step 4: Run the Pipeline

**Option A: Manual Trigger (Recommended for First Run)**
1. In Airflow UI, go to **DAGs** page
2. Find `csv_to_mysql_with_metadata`
3. Toggle the switch to **enable** the DAG
4. Click the **Play (▶)** button to trigger
5. Watch the pipeline execute in real-time!

**Option B: Automatic Trigger**
Edit `dags/csv_ingestion_dag.py` line 204:
```python
schedule_interval='@daily'  # or '@hourly', '*/15 * * * *', etc.
```

### Step 5: Verify Results

**Check Data in MySQL:**
```powershell
docker-compose exec mysql mysql -u data_user -pdata_pass -e "SELECT * FROM data_db.sales_data LIMIT 5;"
```

**Check Metadata in PostgreSQL:**
```powershell
docker-compose exec postgres-metadata psql -U metadata_user metadata_db -c "SELECT file_name, row_count, ingestion_status FROM file_metadata;"
```

**Check Archived File:**
```powershell
ls data/archive/
```

## 📊 What Just Happened?

The pipeline:
1. ✅ Scanned `data/input/` for CSV files
2. ✅ Validated `sales_data.csv`
3. ✅ Loaded 50 rows into MySQL `sales_data` table
4. ✅ Extracted metadata (columns, types, stats)
5. ✅ Stored metadata in PostgreSQL
6. ✅ Moved file to `data/archive/` with timestamp

## 🎯 Next Steps

### Add Your Own CSV Files
1. Place CSV files in `data/input/` directory
2. Trigger the DAG (manual or wait for schedule)
3. Pipeline will automatically process new files

### Customize the Pipeline
- **Target table**: Edit `TARGET_TABLE` in `dags/csv_ingestion_dag.py`
- **Batch size**: Edit `batch_size` parameter in `utils/db_connectors.py`
- **Schedule**: Edit `schedule_interval` in `dags/csv_ingestion_dag.py`

### View Monitoring & Logs
- **Airflow UI**: http://localhost:8080 (DAG runs, task logs)
- **Service logs**: `docker-compose logs -f airflow-scheduler`
- **Database queries**: See README.md for sample queries

## 🛑 Stop Everything
```powershell
# Stop all services
docker-compose down

# Stop and remove all data (CAUTION!)
docker-compose down -v
```

## ❓ Troubleshooting

**DAG not showing up?**
```powershell
docker-compose restart airflow-scheduler
```

**Connection errors?**
```powershell
docker-compose ps  # Check all services are healthy
docker-compose logs mysql
docker-compose logs postgres-metadata
```

**Need to reset?**
```powershell
docker-compose down -v
docker-compose up -d
```

## 📖 Full Documentation
See [README.md](README.md) for complete architecture details and advanced configuration.

---
**You're all set! 🎉**
