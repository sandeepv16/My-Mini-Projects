# CSV to MySQL Data Pipeline with Metadata Tracking

A production-ready Apache Airflow data pipeline that ingests CSV data into MySQL and tracks comprehensive metadata in PostgreSQL. The pipeline supports both manual and automatic triggering.

## 🏗️ Architecture Overview

### System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AIRFLOW ORCHESTRATION                        │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐            │
│  │   Scheduler  │───▶│  Web Server  │◀───│   Workers    │           │
│  └──────────────┘    └──────────────┘    └──────────────┘            │
│         │                                         │                  │
│         │                  DAG Execution          │                  │
│         └─────────────────────┬───────────────────┘                  │
└───────────────────────────────┼──────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
        ┌───────────▼──────────┐  ┌─────────▼─────────┐
        │   CSV Input Files    │  │  Airflow Metadata │
        │   /data/input/       │  │   PostgreSQL DB   │
        └───────────┬──────────┘  └───────────────────┘
                    │
        ┌───────────▼─────────────────────────────────┐
        │         Data Processing Layer               │
        │  ┌────────────────────────────────────────┐ │
        │  │  1. Scan & Validate CSV Files          │ │
        │  │  2. Extract Data + Metadata            │ │
        │  │  3. Transform & Clean Data             │ │
        │  │  4. Parallel Load Operations           │ │
        │  └────────────────────────────────────────┘ │
        └───────────┬──────────────┬──────────────────┘
                    │              │
        ┌───────────▼──────────┐   │
        │  MySQL Database      │   │
        │  (Actual Data)       │   │
        │  - sales_data table  │   │
        │  - Transactional     │   │
        └──────────────────────┘   │
                                   │
                    ┌──────────────▼───────────────┐
                    │  PostgreSQL Database         │
                    │  (Metadata Repository)       │
                    │  - file_metadata             │
                    │  - column_metadata           │
                    │  - data_quality_metrics      │
                    └──────────────────────────────┘
                                   │
                    ┌──────────────▼──────────┐
                    │  Archive Directory      │
                    │  /data/archive/         │
                    │  (Processed Files)      │
                    └─────────────────────────┘
```

### Data Flow

1. **Ingestion Layer**: CSV files are placed in `/data/input/`
2. **Processing Layer**: Airflow DAG orchestrates parallel operations
3. **Storage Layer**: 
   - MySQL stores the actual business data
   - PostgreSQL stores metadata and data lineage
4. **Archive Layer**: Processed files moved to `/data/archive/`

### Component Details

#### 1. **Apache Airflow**
- **Scheduler**: Monitors DAGs and triggers task execution
- **Web Server**: Provides UI for monitoring and manual triggers
- **Executor**: LocalExecutor for task execution
- **Metadata DB**: PostgreSQL database for Airflow's internal state

#### 2. **MySQL Database**
- Stores actual CSV data in structured tables
- Optimized for transactional queries
- Indexed columns for performance
- Example: `sales_data` table with transaction records

#### 3. **PostgreSQL Database**
- Stores comprehensive metadata about ingested files
- Tracks data quality metrics
- Maintains data lineage and audit trail
- Three main tables:
  - `file_metadata`: File-level information
  - `column_metadata`: Column statistics and profiles
  - `data_quality_metrics`: Quality checks and validations

#### 4. **Utility Modules**
- `data_processor.py`: Data transformation and validation
- `db_connectors.py`: Database connection management

## 📊 Pipeline Workflow

### DAG Tasks

```
Start
  │
  ▼
Scan CSV Files ──────────────┐
  │                           │
  ▼                           │
Read & Validate CSV           │
  │                           │
  ├─────────────┬─────────────┤
  │             │             │
  ▼             ▼             │
Load to       Extract         │
MySQL         Metadata        │
  │             │             │
  └──────┬──────┘             │
         │                    │
         ▼                    │
    Archive File              │
         │                    │
         ▼                    │
    Log Summary               │
         │                    │
         ▼                    │
       End ◀──────────────────┘
```

### Task Details

1. **scan_for_csv_files**
   - Scans `/data/input/` directory
   - Identifies CSV files for processing
   - Pushes file path to XCom for downstream tasks

2. **read_and_validate_csv**
   - Reads CSV using pandas
   - Validates data structure and content
   - Extracts basic file metadata
   - Shares metadata via XCom

3. **load_data_to_mysql** (Parallel)
   - Prepares DataFrame for MySQL
   - Creates table dynamically based on CSV schema
   - Batch inserts data (1000 rows per batch)
   - Handles data type conversions

4. **extract_and_store_metadata** (Parallel)
   - Extracts column-level statistics
   - Calculates data quality metrics
   - Stores in PostgreSQL tables
   - Updates processing status

5. **archive_processed_file**
   - Moves file to archive directory
   - Appends timestamp to filename
   - Ensures audit trail

6. **log_pipeline_summary**
   - Logs execution summary
   - Provides visibility into pipeline results

## 🚀 Setup and Installation

### Prerequisites

- Docker Desktop installed
- Docker Compose v3.8+
- At least 4GB RAM allocated to Docker
- Windows PowerShell or Command Prompt

### Step 1: Environment Setup

```powershell
# Navigate to project directory
cd c:\Users\ADMIN\SV_Practice_06102024\Self_Learning\MyProjects\airflow_project

# Verify .env file exists
cat .env
```

### Step 2: Start Services

```powershell
# Start all services (first time - may take 5-10 minutes)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f airflow-webserver
```

### Step 3: Access Airflow UI

1. Open browser: http://localhost:8080
2. Login credentials:
   - Username: `airflow`
   - Password: `airflow`

### Step 4: Trigger the DAG

#### Manual Trigger:
1. Navigate to DAGs page
2. Find `csv_to_mysql_with_metadata`
3. Click the play button (▶) to trigger

#### Automatic Trigger (Optional):
Edit [dags/csv_ingestion_dag.py](dags/csv_ingestion_dag.py#L204):
```python
# Change from manual
schedule_interval=None

# To automatic (examples)
schedule_interval='@daily'      # Daily at midnight
schedule_interval='@hourly'     # Every hour
schedule_interval='0 9 * * *'   # Every day at 9 AM
schedule_interval='*/15 * * * *' # Every 15 minutes
```

## 📁 Project Structure

```
airflow_project/
├── dags/
│   └── csv_ingestion_dag.py        # Main DAG definition
├── utils/
│   ├── __init__.py
│   ├── data_processor.py           # Data transformation utilities
│   └── db_connectors.py            # Database connection classes
├── data/
│   ├── input/                      # Place CSV files here
│   │   └── sales_data.csv          # Sample data
│   └── archive/                    # Processed files moved here
├── config/
│   ├── init-mysql-db.sql           # MySQL initialization
│   └── init-metadata-db.sql        # PostgreSQL initialization
├── logs/                           # Airflow execution logs (auto-generated)
├── plugins/                        # Custom Airflow plugins
├── docker-compose.yml              # Service definitions
├── .env                            # Environment variables
└── README.md                       # This file
```

### What is the logs/ Directory For?

The `logs/` directory is **automatically used by Airflow** to store execution logs for all DAG runs and task executions. It starts empty and gets populated when you run pipelines.

**What Gets Stored:**
- Task execution output (print statements, logger messages)
- Error messages and stack traces if tasks fail
- Start/end timestamps for each task
- Database connection logs
- Data processing statistics

**Log Structure (after execution):**
```
logs/
├── dag_id=csv_to_mysql_with_metadata/
│   ├── run_id=manual__2026-01-12T10:30:00+00:00/
│   │   ├── task_id=scan_for_csv_files/
│   │   │   └── attempt=1.log
│   │   ├── task_id=load_data_to_mysql/
│   │   │   └── attempt=1.log
│   │   └── task_id=extract_and_store_metadata/
│   │       └── attempt=1.log
├── scheduler/
└── dag_processor_manager/
```

**How to View Logs:**

*Option 1: Airflow UI (Recommended)*
- Navigate to your DAG run
- Click on any task
- Click the "Log" tab for real-time log streaming

*Option 2: Directly in filesystem*
```powershell
# View specific task log
cat logs/dag_id=csv_to_mysql_with_metadata/run_id=*/task_id=load_data_to_mysql/attempt=1.log
```

*Option 3: Via Docker*
```powershell
# View scheduler logs
docker-compose logs -f airflow-scheduler
```

## 🔧 Configuration

### Database Connections

All connections are configured via environment variables in [.env](.env):

**MySQL (Data Storage)**
```
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=data_db
MYSQL_USER=data_user
MYSQL_PASSWORD=data_pass
```

**PostgreSQL (Metadata Storage)**
```
POSTGRES_METADATA_HOST=postgres-metadata
POSTGRES_METADATA_PORT=5432
POSTGRES_METADATA_DATABASE=metadata_db
POSTGRES_METADATA_USER=metadata_user
POSTGRES_METADATA_PASSWORD=metadata_pass
```

### Accessing Databases

**MySQL**
```powershell
docker-compose exec mysql mysql -u data_user -pdata_pass data_db
```

**PostgreSQL**
```powershell
docker-compose exec postgres-metadata psql -U metadata_user metadata_db
```

## 📊 Sample Queries

### MySQL - View Ingested Data

```sql
USE data_db;

-- View all records
SELECT * FROM sales_data LIMIT 10;

-- Sales by region
SELECT region, COUNT(*) as transaction_count, SUM(price * quantity) as total_revenue
FROM sales_data
GROUP BY region
ORDER BY total_revenue DESC;

-- Recent transactions
SELECT * FROM sales_data 
ORDER BY transaction_date DESC 
LIMIT 20;
```

### PostgreSQL - View Metadata

```sql
-- View file ingestion history
SELECT 
    file_name,
    row_count,
    column_count,
    ingestion_status,
    ingestion_timestamp,
    processing_duration_seconds
FROM file_metadata
ORDER BY ingestion_timestamp DESC;

-- View column statistics
SELECT 
    fm.file_name,
    cm.column_name,
    cm.column_type,
    cm.null_count,
    cm.unique_count
FROM column_metadata cm
JOIN file_metadata fm ON cm.file_metadata_id = fm.id
ORDER BY fm.ingestion_timestamp DESC;

-- View data quality metrics
SELECT 
    fm.file_name,
    dqm.metric_name,
    dqm.metric_value,
    dqm.metric_type
FROM data_quality_metrics dqm
JOIN file_metadata fm ON dqm.file_metadata_id = fm.id
ORDER BY fm.ingestion_timestamp DESC;
```

## 🎯 Key Features

### ✅ Parallel Processing
- Data loading and metadata extraction run in parallel
- Optimizes pipeline execution time

### ✅ Comprehensive Metadata
- File-level statistics (size, row count, columns)
- Column-level profiling (types, nulls, unique values)
- Data quality metrics (completeness, duplicates)

### ✅ Error Handling
- Retry logic (2 retries with 5-minute delay)
- Status tracking in metadata database
- Detailed error logging

### ✅ Data Lineage
- Tracks source file to target table mapping
- Maintains processing timestamps
- Archives processed files with timestamps

### ✅ Scalability
- Batch insertion for large datasets
- Dynamic table creation based on CSV schema
- Configurable batch sizes

### ✅ Monitoring
- Airflow UI for real-time monitoring
- Execution logs and task status
- Pipeline summary logging

## 🔍 Monitoring and Troubleshooting

### View Airflow Logs
```powershell
# Scheduler logs
docker-compose logs -f airflow-scheduler

# Webserver logs
docker-compose logs -f airflow-webserver

# All services
docker-compose logs -f
```

### Check Task Logs
1. Navigate to Airflow UI
2. Click on DAG run
3. Click on specific task
4. View "Log" tab

### Common Issues

**Issue: DAG not appearing**
```powershell
# Restart scheduler
docker-compose restart airflow-scheduler
```

**Issue: Database connection failed**
```powershell
# Check database health
docker-compose ps
docker-compose logs mysql
docker-compose logs postgres-metadata
```

**Issue: No CSV files found**
- Ensure files are in `data/input/` directory
- Check file permissions
- Verify file extension is `.csv`

## 🧪 Testing the Pipeline

### 1. Place Sample Data
Sample file already exists: `data/input/sales_data.csv`

### 2. Trigger DAG
- Open http://localhost:8080
- Enable the DAG (toggle switch)
- Click play button to trigger

### 3. Verify Results

**Check MySQL:**
```powershell
docker-compose exec mysql mysql -u data_user -pdata_pass -e "SELECT COUNT(*) FROM data_db.sales_data;"
```

**Check PostgreSQL:**
```powershell
docker-compose exec postgres-metadata psql -U metadata_user metadata_db -c "SELECT * FROM file_metadata;"
```

**Check Archive:**
```powershell
ls data/archive/
```

## 🛑 Stopping and Cleaning Up

### Stop Services
```powershell
docker-compose down
```

### Stop and Remove Volumes (CAUTION: Deletes all data)
```powershell
docker-compose down -v
```

### Restart Fresh
```powershell
docker-compose down -v
docker-compose up -d
```

## 📈 Performance Optimization

### Batch Size Tuning
Edit [utils/db_connectors.py](utils/db_connectors.py):
```python
# Adjust batch_size parameter in insert_dataframe method
rows_inserted = mysql_conn.insert_dataframe(df_clean, TARGET_TABLE, batch_size=5000)
```

### Parallel Task Execution
The DAG already implements parallel execution:
- `load_data_to_mysql` and `extract_and_store_metadata` run in parallel
- Can be extended with dynamic task mapping for multiple files

## 🔐 Security Considerations

### Production Recommendations:
1. Change default passwords in `.env`
2. Use secrets management (e.g., AWS Secrets Manager, HashiCorp Vault)
3. Enable SSL/TLS for database connections
4. Implement network segregation
5. Use Airflow connections instead of hardcoded credentials
6. Enable authentication and RBAC in Airflow

## 📚 Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review Airflow task logs in UI
3. Verify database connections
4. Check file permissions and paths

## 📝 License

This project is provided as-is for educational and development purposes.

---

## 🎯 Project Purpose and End-to-End Functioning

### Purpose
This project serves as a **comprehensive data engineering solution** designed to automate the ingestion of CSV files into a relational database (MySQL) while maintaining robust metadata tracking and data lineage in a separate PostgreSQL database. The primary goal is to provide organizations with a scalable, production-ready pipeline that not only processes data but also captures critical metadata for data governance, quality monitoring, and audit compliance. This dual-storage approach separates transactional data from metadata, enabling efficient analytics on business data while maintaining comprehensive tracking of data provenance, quality metrics, and processing history.

### Trigger Mechanisms

**Manual Trigger:**
When triggered manually through the Airflow UI, the pipeline operates on-demand, allowing users to process CSV files at their discretion. A user navigates to the Airflow web interface (http://localhost:8080), enables the DAG, and clicks the play button. This immediately initiates the workflow, making it ideal for ad-hoc data loads, testing scenarios, or when processing files that arrive irregularly. Manual triggering provides complete control over execution timing and allows operators to verify data availability and system readiness before processing.

**Automatic Trigger:**
For automated operations, the pipeline can be configured with a schedule interval (such as `@daily`, `@hourly`, or custom cron expressions like `*/15 * * * *` for every 15 minutes). Once scheduled, the Airflow scheduler continuously monitors the configured time intervals and automatically triggers the DAG when the schedule condition is met. This autonomous operation is perfect for production environments with regular data deliveries, eliminating the need for manual intervention. The scheduler ensures pipelines run consistently at predetermined times, processing any new CSV files that have been deposited in the input directory since the last run.

### Complete Data Flow from Start to End

**Phase 1 - Initialization & Discovery (Tasks: start → scan_for_csv_files)**
The pipeline begins when triggered (manually or automatically). The first task scans the `/data/input/` directory to detect available CSV files. The file path is stored in Airflow's XCom (cross-communication) system, making it available to all downstream tasks. If no files are found, the pipeline terminates gracefully with a warning message.

**Phase 2 - Validation & Preparation (Task: read_and_validate_csv)**
Once a CSV file is identified, pandas reads it into a DataFrame. The system performs structural validation, checking for empty files, malformed data, or missing headers. Basic metadata is extracted at this stage, including row count, column count, file size, and processing start time. This metadata is pushed to XCom for downstream consumption. If validation fails, the pipeline halts with detailed error logging.

**Phase 3 - Parallel Data Processing (Tasks: load_data_to_mysql + extract_and_store_metadata)**
The pipeline executes two critical tasks simultaneously for optimal performance:

- **MySQL Data Loading Branch**: The DataFrame undergoes transformation—column names are standardized (lowercase, underscores), date columns are parsed, and NULL values are properly handled. A MySQL table is dynamically created or verified based on the CSV schema, with appropriate data types mapped from pandas to MySQL formats. Data is then inserted in configurable batches (default 1000 rows per batch) to balance memory usage and performance. Each successful batch insertion is logged for traceability.

- **PostgreSQL Metadata Extraction Branch**: Running in parallel, this branch analyzes the DataFrame to extract comprehensive metadata. A record is created in the `file_metadata` table containing file information, processing metrics, and ingestion status. For each column, detailed statistics are computed—data types, null counts, unique value counts, min/max values, and sample data—stored in the `column_metadata` table. Additionally, data quality metrics are calculated, including overall completeness percentage, duplicate row counts, columns with missing values, and memory usage, all stored in the `data_quality_metrics` table. Each metadata insertion receives a unique ID that creates a traceable link between the source file and its analytical metadata.

**Phase 4 - Archival & Completion (Tasks: archive_processed_file → log_pipeline_summary → end)**
After both parallel branches complete successfully, the processed CSV file is moved from `/data/input/` to `/data/archive/` with a timestamp appended to its filename (e.g., `sales_data_20260112_143025.csv`). This archival strategy maintains an audit trail while preventing reprocessing of the same file. A comprehensive execution summary is logged, including file name, rows processed, metadata IDs, target table, and execution timestamp. Finally, the pipeline marks itself as successfully completed, updating the Airflow metadata database and making the execution results visible in the UI with task statuses, duration metrics, and logs.

### Error Handling & Recovery
Throughout the entire process, comprehensive error handling ensures resilience. If any task fails, the pipeline implements a retry mechanism (configured for 2 retries with 5-minute delays). Failed tasks update the metadata status in PostgreSQL, logging error messages for debugging. The Airflow UI displays task states (queued, running, success, failed, retry) in real-time, enabling operators to monitor progress and intervene when necessary. Logs are preserved in the `logs/` directory and accessible through the UI, providing complete visibility into every execution step.

### End Result
Upon successful completion, the system achieves three key outcomes: (1) Business data is cleanly stored in MySQL's `sales_data` table, queryable for analytics and reporting; (2) Comprehensive metadata resides in PostgreSQL, enabling data governance teams to track data lineage, monitor quality trends, and maintain regulatory compliance; (3) Processed files are archived with timestamps, creating an immutable audit trail that supports data forensics and troubleshooting. This architecture ensures that organizations not only move data efficiently but also maintain complete visibility and control over their data assets from ingestion through archival.

---

**Built with ❤️ using Apache Airflow, MySQL, PostgreSQL, and Docker**
