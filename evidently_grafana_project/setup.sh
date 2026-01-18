#!/bin/bash
# Setup script for CLV Drift Monitoring System

echo "=========================================="
echo "CLV Drift Monitoring - Setup Script"
echo "=========================================="
echo ""

# Check if Docker is running
echo "Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo "✅ Docker is running"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "AIRFLOW_UID=$(id -u)" > .env
    else
        echo "AIRFLOW_UID=50000" > .env
    fi
    echo "_AIRFLOW_WWW_USER_USERNAME=airflow" >> .env
    echo "_AIRFLOW_WWW_USER_PASSWORD=airflow" >> .env
    echo "_PIP_ADDITIONAL_REQUIREMENTS=evidently prometheus-client scikit-learn pandas numpy joblib" >> .env
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p models data/reference data/current monitoring/reports logs
echo "✅ Directories created"
echo ""

# Check if Online_Retail.csv.csv exists
if [ ! -f "Online_Retail.csv.csv" ]; then
    echo "⚠️  Warning: Online_Retail.csv.csv not found in current directory"
    echo "   Please ensure the data file is present before starting services"
else
    echo "✅ Data file found"
fi
echo ""

echo "=========================================="
echo "Setup complete! Next steps:"
echo "=========================================="
echo ""
echo "1. Start all services:"
echo "   docker-compose up -d"
echo ""
echo "2. Wait for services to initialize (2-3 minutes)"
echo "   Check status: docker-compose ps"
echo ""
echo "3. Access web interfaces:"
echo "   - Airflow:    http://localhost:8080 (airflow/airflow)"
echo "   - Grafana:    http://localhost:3000 (admin/admin)"
echo "   - Prometheus: http://localhost:9090"
echo ""
echo "4. Train initial model:"
echo "   docker-compose exec airflow-webserver airflow dags trigger clv_model_training"
echo ""
echo "5. Enable drift monitoring:"
echo "   Toggle the 'clv_drift_monitoring' DAG in Airflow UI"
echo ""
echo "For more details, see QUICKSTART.md"
echo ""
