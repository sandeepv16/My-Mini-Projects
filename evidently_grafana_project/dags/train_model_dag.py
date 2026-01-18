"""
Airflow DAG for CLV Model Training and Drift Monitoring
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append('/opt/airflow')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def train_model_task(**context):
    """Task to train CLV model"""
    sys.path.append('/opt/airflow/scripts')
    from train_clv_model import CLVModelTrainer
    
    data_path = '/opt/airflow/Online_Retail.csv.csv'
    trainer = CLVModelTrainer(
        data_path=data_path,
        model_dir='/opt/airflow/models',
        reference_dir='/opt/airflow/data/reference'
    )
    
    result = trainer.run()
    
    # Push results to XCom
    context['ti'].xcom_push(key='training_result', value=result)
    
    print(f"Model training completed: {result}")
    return result


with DAG(
    'clv_model_training',
    default_args=default_args,
    description='Train CLV prediction model',
    schedule_interval='@weekly',  # Train weekly
    start_date=days_ago(1),
    catchup=False,
    tags=['clv', 'training'],
) as dag:
    
    train_model = PythonOperator(
        task_id='train_clv_model',
        python_callable=train_model_task,
        provide_context=True,
    )
    
    train_model
