# Architecture Documentation

## 🏗️ Detailed Architecture Explanation

### 1. System Components

#### Core Services
- **Apache Airflow**: Workflow orchestration and scheduling
- **MySQL**: Transactional data storage
- **PostgreSQL (Airflow)**: Airflow metadata storage
- **PostgreSQL (Metadata)**: Data lineage and metadata tracking

#### Application Layers
- **Presentation Layer**: Airflow Web UI
- **Orchestration Layer**: Airflow Scheduler + Executor
- **Processing Layer**: Python operators with pandas
- **Storage Layer**: MySQL + PostgreSQL databases
- **Data Layer**: File system (input/archive)

---

## 📊 Data Flow Architecture

### Phase 1: Ingestion
```
CSV File → Scanner → Validator → DataFrame
```
1. Files placed in `data/input/`
2. Scanner detects new CSV files
3. Validator checks structure and content
4. Data loaded into pandas DataFrame

### Phase 2: Parallel Processing
```
DataFrame → ┌─→ MySQL Loader     → MySQL DB
            └─→ Metadata Extractor → PostgreSQL DB
```
Two parallel branches:
- **Branch A**: Transform and load data into MySQL
- **Branch B**: Extract metadata and store in PostgreSQL

### Phase 3: Finalization
```
Both Complete → Archive → Log Summary → Complete
```
1. Wait for both parallel tasks
2. Move processed file to archive
3. Log execution summary
4. Mark pipeline as complete

---

## 🔄 Task Dependencies

```
         ┌─────────────────────────────┐
         │  start (EmptyOperator)      │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  scan_for_csv_files         │
         │  - List files in input dir  │
         │  - Push path to XCom        │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  read_and_validate_csv      │
         │  - Read CSV with pandas     │
         │  - Validate structure       │
         │  - Extract basic metadata   │
         └──────────────┬──────────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
┌───────────▼─────────────┐ ┌──────▼──────────────────┐
│  load_data_to_mysql     │ │ extract_and_store_      │
│  - Transform data       │ │ metadata                │
│  - Create table         │ │ - Column statistics     │
│  - Batch insert         │ │ - Quality metrics       │
└───────────┬─────────────┘ └──────┬──────────────────┘
            │                      │
            └───────────┬──────────┘
                        │
         ┌──────────────▼──────────────┐
         │  archive_processed_file     │
         │  - Move to archive dir      │
         │  - Add timestamp            │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  log_pipeline_summary       │
         │  - Log statistics           │
         │  - Print summary            │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  end (EmptyOperator)        │
         └─────────────────────────────┘
```

---

## 💾 Database Schema

### MySQL Schema (Data Storage)

#### sales_data Table
```sql
CREATE TABLE sales_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(50),
    customer_id VARCHAR(50),
    product_name VARCHAR(255),
    quantity INT,
    price DECIMAL(10, 2),
    transaction_date DATE,
    region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_transaction_date(transaction_date),
    INDEX idx_customer_id(customer_id)
);
```

### PostgreSQL Schema (Metadata Storage)

#### file_metadata Table
```sql
CREATE TABLE file_metadata (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes BIGINT,
    row_count INTEGER,
    column_count INTEGER,
    columns_info JSONB,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ingestion_status VARCHAR(50),
    target_table VARCHAR(255),
    error_message TEXT,
    processing_duration_seconds DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### column_metadata Table
```sql
CREATE TABLE column_metadata (
    id SERIAL PRIMARY KEY,
    file_metadata_id INTEGER REFERENCES file_metadata(id),
    column_name VARCHAR(255) NOT NULL,
    column_type VARCHAR(100),
    null_count INTEGER,
    unique_count INTEGER,
    min_value TEXT,
    max_value TEXT,
    sample_values JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### data_quality_metrics Table
```sql
CREATE TABLE data_quality_metrics (
    id SERIAL PRIMARY KEY,
    file_metadata_id INTEGER REFERENCES file_metadata(id),
    metric_name VARCHAR(255) NOT NULL,
    metric_value TEXT,
    metric_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔐 Security Architecture

### Network Isolation
```
External Network (Port 8080)
    │
    ▼
┌────────────────────────────┐
│  Airflow Web Server        │
└───────────┬────────────────┘
            │
Internal Docker Network
    ┌───────┼───────┐
    │       │       │
    ▼       ▼       ▼
┌─────┐ ┌──────┐ ┌──────┐
│MySQL│ │Postgres│Postgres│
│3306 │ │5432  │ │5433  │
└─────┘ └──────┘ └──────┘
```

### Authentication Layers
1. **Airflow UI**: Username/password (configurable)
2. **MySQL**: User credentials from environment
3. **PostgreSQL**: User credentials from environment
4. **Docker Network**: Isolated bridge network

---

## ⚡ Performance Considerations

### Optimization Strategies

#### 1. Batch Processing
```python
# Insert in batches to optimize memory and network
batch_size = 1000  # Configurable
for i in range(0, total_rows, batch_size):
    batch = df.iloc[i:i+batch_size]
    insert_batch(batch)
```

#### 2. Parallel Execution
```python
# MySQL load and metadata extraction run in parallel
load_mysql >> archive_file
store_metadata >> archive_file
```

#### 3. Database Indexing
```sql
-- Indexes for faster queries
CREATE INDEX idx_transaction_date ON sales_data(transaction_date);
CREATE INDEX idx_ingestion_timestamp ON file_metadata(ingestion_timestamp);
```

#### 4. Connection Pooling
- Each task uses temporary connections
- Connections closed after use
- Prevents connection exhaustion

### Scalability Options

#### Vertical Scaling
- Increase Docker container resources
- Allocate more CPU/memory to databases

#### Horizontal Scaling
- Change executor: LocalExecutor → CeleryExecutor
- Add worker nodes for distributed processing
- Use external databases (AWS RDS, Cloud SQL)

#### Data Volume Scaling
- Adjust batch sizes for large files
- Implement chunked reading for huge CSVs
- Use dynamic task mapping for multiple files

---

## 🔄 Pipeline States

### State Transitions
```
queued → running → success
              ↓
           failed → retry → running → success
                            ↓
                         failed (max retries)
```

### Retry Logic
- **Max Retries**: 2
- **Retry Delay**: 5 minutes
- **Retry Strategy**: Exponential backoff (can be configured)

### Error Handling
1. Task failure → Log error → Update metadata status
2. Retry mechanism kicks in
3. If max retries exceeded → Mark as failed
4. Alert sent (if configured)

---

## 📁 File Management

### Directory Structure
```
data/
├── input/           # New CSV files placed here
│   └── *.csv       # Automatically detected
└── archive/         # Processed files moved here
    └── *_timestamp.csv  # Timestamped for audit trail
```

### File Lifecycle
1. **New**: File placed in `input/`
2. **Processing**: Read by pipeline
3. **Validated**: Structure checked
4. **Loaded**: Data inserted into databases
5. **Archived**: Moved to `archive/` with timestamp
6. **Retained**: Available for audit

---

## 🎯 Trigger Mechanisms

### Manual Trigger
- User clicks play button in UI
- Immediate execution
- Good for: Ad-hoc loads, testing

### Scheduled Trigger
```python
schedule_interval='@daily'      # Every midnight
schedule_interval='@hourly'     # Every hour
schedule_interval='*/15 * * * *' # Every 15 minutes
schedule_interval='0 9 * * 1-5' # Weekdays at 9 AM
```

### External Trigger
```bash
# Via Airflow CLI
airflow dags trigger csv_to_mysql_with_metadata

# Via REST API
curl -X POST http://localhost:8080/api/v1/dags/csv_to_mysql_with_metadata/dagRuns \
  -H "Content-Type: application/json" \
  -u "airflow:airflow" \
  -d '{"conf":{}}'
```

---

## 📈 Monitoring & Observability

### What's Monitored
1. **Task Status**: Success/Failure/Running
2. **Execution Time**: Duration per task
3. **Data Metrics**: Rows processed, file size
4. **Quality Metrics**: Completeness, duplicates
5. **Error Logs**: Stack traces, error messages

### Monitoring Interfaces
- **Airflow UI**: Real-time task monitoring
- **Database Queries**: Historical metadata analysis
- **Docker Logs**: System-level debugging
- **Task Logs**: Detailed execution traces

### Alerting (Can be configured)
- Email on failure
- Slack notifications
- PagerDuty integration
- Custom webhooks

---

## 🔧 Extensibility

### Adding New Data Sources
1. Create new scanner function
2. Add file format parser
3. Update data transformation logic
4. No changes needed in storage layer

### Adding New Destinations
1. Create new connector class
2. Add task in DAG
3. Configure credentials in `.env`
4. Update parallel execution logic

### Adding Data Quality Checks
1. Add validation function in `data_processor.py`
2. Insert as task in DAG
3. Store results in quality metrics table

---

## 💡 Best Practices Implemented

✅ **Separation of Concerns**: Data vs. Metadata storage  
✅ **Idempotency**: Can re-run without duplicates (add logic if needed)  
✅ **Error Handling**: Comprehensive try-catch blocks  
✅ **Logging**: Detailed logs at each step  
✅ **Configuration Management**: Environment variables  
✅ **Code Modularity**: Reusable utility functions  
✅ **Data Lineage**: Track source to destination  
✅ **Archive Strategy**: Maintain audit trail  
✅ **Parallel Processing**: Optimize execution time  
✅ **Batch Operations**: Handle large datasets efficiently  

---

## 📚 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Orchestration | Apache Airflow 2.8.0 | Workflow management |
| Language | Python 3.10 | Data processing |
| Data Processing | Pandas 2.1.4 | CSV manipulation |
| Data Storage | MySQL 8.0 | Transactional data |
| Metadata Storage | PostgreSQL 14 | Metadata & lineage |
| Containerization | Docker Compose | Service management |
| Web Server | Flask (Airflow) | UI & API |
| Database Drivers | mysql-connector, psycopg2 | DB connectivity |

---

**This architecture provides a production-ready, scalable, and maintainable data pipeline solution.**
