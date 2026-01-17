#!/usr/bin/env python3
"""
Quick start script to verify the setup
Run this after docker-compose up to ensure everything is configured correctly
"""

import os
import time
import requests
import mysql.connector
import psycopg2

def check_airflow():
    """Check if Airflow web server is accessible"""
    print("🔍 Checking Airflow web server...")
    try:
        response = requests.get('http://localhost:8080/health', timeout=5)
        if response.status_code == 200:
            print("✅ Airflow web server is running")
            return True
        else:
            print(f"⚠️  Airflow returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Airflow web server not accessible: {str(e)}")
        return False

def check_mysql():
    """Check MySQL connection"""
    print("\n🔍 Checking MySQL database...")
    try:
        conn = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='data_db',
            user='data_user',
            password='data_pass'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        print("✅ MySQL database is accessible")
        return True
    except Exception as e:
        print(f"❌ MySQL connection failed: {str(e)}")
        return False

def check_postgres():
    """Check PostgreSQL connection"""
    print("\n🔍 Checking PostgreSQL database...")
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            database='metadata_db',
            user='metadata_user',
            password='metadata_pass'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        print("✅ PostgreSQL database is accessible")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        return False

def check_csv_file():
    """Check if sample CSV exists"""
    print("\n🔍 Checking sample CSV file...")
    csv_path = 'data/input/sales_data.csv'
    if os.path.exists(csv_path):
        print(f"✅ Sample CSV file exists: {csv_path}")
        return True
    else:
        print(f"❌ Sample CSV file not found: {csv_path}")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("🚀 Airflow Data Pipeline - Health Check")
    print("=" * 60)
    
    results = {
        'Airflow': check_airflow(),
        'MySQL': check_mysql(),
        'PostgreSQL': check_postgres(),
        'CSV File': check_csv_file()
    }
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "=" * 60)
        print("🎉 All checks passed! Ready to use.")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("1. Open Airflow UI: http://localhost:8080")
        print("2. Login with: airflow / airflow")
        print("3. Enable and trigger the DAG: csv_to_mysql_with_metadata")
        print("\n💡 To add more CSV files, place them in: data/input/")
    else:
        print("\n" + "=" * 60)
        print("⚠️  Some checks failed. Please review the errors above.")
        print("=" * 60)
        print("\n🔧 Troubleshooting:")
        print("- Ensure Docker containers are running: docker-compose ps")
        print("- Check logs: docker-compose logs -f")
        print("- Wait a few minutes if services just started")

if __name__ == '__main__':
    main()
