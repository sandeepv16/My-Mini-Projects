# Setup script for CLV Drift Monitoring System (Windows PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "CLV Drift Monitoring - Setup Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
AIRFLOW_UID=50000
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
_PIP_ADDITIONAL_REQUIREMENTS=evidently prometheus-client scikit-learn pandas numpy joblib
"@ | Out-File -FilePath .env -Encoding ASCII
    Write-Host "✅ Created .env file" -ForegroundColor Green
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}
Write-Host ""

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Yellow
$directories = @(
    "models",
    "data\reference",
    "data\current",
    "monitoring\reports",
    "logs"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "✅ Directories created" -ForegroundColor Green
Write-Host ""

# Check if Online_Retail.csv.csv exists
if (-not (Test-Path "Online_Retail.csv.csv")) {
    Write-Host "⚠️  Warning: Online_Retail.csv.csv not found in current directory" -ForegroundColor Yellow
    Write-Host "   Please ensure the data file is present before starting services" -ForegroundColor Yellow
} else {
    Write-Host "✅ Data file found" -ForegroundColor Green
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup complete! Next steps:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Start all services:" -ForegroundColor White
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Wait for services to initialize (2-3 minutes)" -ForegroundColor White
Write-Host "   Check status: docker-compose ps" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Access web interfaces:" -ForegroundColor White
Write-Host "   - Airflow:    http://localhost:8080 (airflow/airflow)" -ForegroundColor Gray
Write-Host "   - Grafana:    http://localhost:3000 (admin/admin)" -ForegroundColor Gray
Write-Host "   - Prometheus: http://localhost:9090" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Train initial model:" -ForegroundColor White
Write-Host "   docker-compose exec airflow-webserver airflow dags trigger clv_model_training" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Enable drift monitoring:" -ForegroundColor White
Write-Host "   Toggle the 'clv_drift_monitoring' DAG in Airflow UI" -ForegroundColor Gray
Write-Host ""
Write-Host "For more details, see QUICKSTART.md" -ForegroundColor Cyan
Write-Host ""
