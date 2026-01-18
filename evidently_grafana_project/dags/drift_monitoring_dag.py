"""
Airflow DAG for Drift Monitoring and Retraining
"""
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import json

sys.path.append('/opt/airflow')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def check_for_new_data(**context):
    """Check if new data is available for drift detection"""
    import os
    from pathlib import Path
    
    # Check both root /opt/airflow and /opt/airflow/data/current folders
    root_path = Path('/opt/airflow')
    current_path = Path('/opt/airflow/data/current')
    
    # Collect CSV files from both locations
    csv_files = list(root_path.glob('*.csv')) + list(current_path.glob('*.csv'))
    
    # Filter out reference data files
    csv_files = [f for f in csv_files if 'reference' not in f.name.lower()]
    
    if csv_files:
        # Get the most recent file
        latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
        context['ti'].xcom_push(key='current_data_file', value=str(latest_file))
        print(f"Found new data file: {latest_file}")
        return True
    else:
        print("No new data files found")
        return False


def detect_drift_task(**context):
    """Task to detect drift using Evidently"""
    sys.path.append('/opt/airflow/monitoring')
    from drift_detector import DriftDetector
    
    # Get current data file from XCom
    current_data_file = context['ti'].xcom_pull(
        task_ids='check_new_data', 
        key='current_data_file'
    )
    
    if not current_data_file:
        # Fallback: find any CSV in root or data/current
        from pathlib import Path
        root_path = Path('/opt/airflow')
        csv_files = [f for f in root_path.glob('*.csv') if 'reference' not in f.name.lower()]
        if csv_files:
            current_data_file = str(max(csv_files, key=lambda p: p.stat().st_mtime))
        else:
            raise FileNotFoundError("No current data file found")
    
    detector = DriftDetector(
        reference_data_path='/opt/airflow/data/reference/reference_data.csv',
        model_dir='/opt/airflow/models',
        report_dir='/opt/airflow/monitoring/reports',
        prometheus_gateway='pushgateway:9091'
    )
    
    results = detector.run_drift_detection(current_data_file)
    
    # Push results to XCom
    context['ti'].xcom_push(key='drift_results', value=results)
    
    print(f"Drift detection completed: {json.dumps(results, indent=2)}")
    return results


def check_retraining_needed(**context):
    """Determine if retraining is needed based on drift results"""
    drift_results = context['ti'].xcom_pull(
        task_ids='detect_drift',
        key='drift_results'
    )
    
    retraining_required = drift_results.get('retraining_required', False)
    
    print(f"Retraining required: {retraining_required}")
    
    if retraining_required:
        return 'trigger_retraining'
    else:
        return 'no_retraining_needed'


def no_retraining_task(**context):
    """Task executed when no retraining is needed"""
    print("No drift detected. Model is performing well. No retraining needed.")


def log_retraining_trigger(**context):
    """Log that retraining has been triggered"""
    drift_results = context['ti'].xcom_pull(
        task_ids='detect_drift',
        key='drift_results'
    )
    
    print("=" * 50)
    print("DRIFT DETECTED - TRIGGERING MODEL RETRAINING")
    print("=" * 50)
    print(f"Data drift detected: {drift_results['data_drift']['drift_detected']}")
    print(f"Model drift detected: {drift_results['model_drift']['model_drift_detected']}")
    print(f"Current R²: {drift_results['model_drift']['current_r2']:.4f}")
    print(f"Reference R²: {drift_results['model_drift']['reference_r2']:.4f}")
    print("=" * 50)


with DAG(
    'clv_drift_monitoring',
    default_args=default_args,
    description='Monitor drift and trigger retraining',
    schedule_interval='@daily',  # Check daily
    start_date=days_ago(1),
    catchup=False,
    tags=['clv', 'monitoring', 'drift'],
) as dag:
    
    check_new_data = PythonOperator(
        task_id='check_new_data',
        python_callable=check_for_new_data,
        provide_context=True,
    )
    
    detect_drift = PythonOperator(
        task_id='detect_drift',
        python_callable=detect_drift_task,
        provide_context=True,
    )
    
    check_retraining = BranchPythonOperator(
        task_id='check_retraining_needed',
        python_callable=check_retraining_needed,
        provide_context=True,
    )
    
    no_retraining = PythonOperator(
        task_id='no_retraining_needed',
        python_callable=no_retraining_task,
        provide_context=True,
    )
    
    log_trigger = PythonOperator(
        task_id='log_retraining_trigger',
        python_callable=log_retraining_trigger,
        provide_context=True,
    )
    
    trigger_retraining = TriggerDagRunOperator(
        task_id='trigger_retraining',
        trigger_dag_id='clv_model_training',
        wait_for_completion=False,
    )
    
    # Define task dependencies
    check_new_data >> detect_drift >> check_retraining
    check_retraining >> no_retraining
    check_retraining >> log_trigger >> trigger_retraining
