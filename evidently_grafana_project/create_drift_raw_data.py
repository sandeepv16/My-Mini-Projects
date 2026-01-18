#!/usr/bin/env python3
"""
Create drift data from raw sales data with modifications
"""
import pandas as pd
import numpy as np
from pathlib import Path

# Load raw data
raw_path = Path('/opt/airflow/Online_Retail.csv.csv')
df = pd.read_csv(raw_path, encoding='latin-1', on_bad_lines='skip')

print(f"Raw data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# Create drift version
drift_df = df.copy()

# DATA DRIFT: Modify quantities and prices
print("\n" + "="*60)
print("CREATING DATA DRIFT")
print("="*60)

# Increase quantities
drift_df['Quantity'] = drift_df['Quantity'] * np.random.uniform(1.5, 3.0, len(drift_df))
print("Quantity: Increased by 1.5-3x")

# Increase unit prices
drift_df['UnitPrice'] = drift_df['UnitPrice'] * np.random.uniform(1.3, 2.5, len(drift_df))
print("UnitPrice: Increased by 1.3-2.5x")

# MODEL DRIFT: Add extreme values and corrupt data
print("\n" + "="*60)
print("CREATING MODEL DRIFT")
print("="*60)

# Add extreme outliers to 10% of rows
outlier_indices = np.random.choice(drift_df.index, size=int(len(drift_df) * 0.10), replace=False)
print(f"Adding outliers to {len(outlier_indices)} rows ({len(outlier_indices)/len(drift_df)*100:.1f}%)")

# Create extreme quantities
drift_df.loc[outlier_indices, 'Quantity'] = np.random.choice([-9999, 99999], len(outlier_indices))
print("Quantity: Added extreme outliers (-9999 or 99999)")

# Create extreme prices
drift_df.loc[outlier_indices, 'UnitPrice'] = np.random.uniform(0.01, 100000, len(outlier_indices))
print("UnitPrice: Added extreme outliers")

# Ensure we have our original data for validation
print("\n" + "="*60)
print("Summary Statistics")
print("="*60)
print(f"Original Quantity - Mean: {df['Quantity'].mean():.2f}, Std: {df['Quantity'].std():.2f}")
print(f"Drift Quantity    - Mean: {drift_df['Quantity'].mean():.2f}, Std: {drift_df['Quantity'].std():.2f}")
print(f"Original UnitPrice - Mean: {df['UnitPrice'].mean():.2f}, Std: {df['UnitPrice'].std():.2f}")
print(f"Drift UnitPrice    - Mean: {drift_df['UnitPrice'].mean():.2f}, Std: {drift_df['UnitPrice'].std():.2f}")

# Save
current_path = Path('/opt/airflow/data/current/current_data.csv')
current_path.parent.mkdir(parents=True, exist_ok=True)
drift_df.to_csv(current_path, index=False)

print("\n" + "="*60)
print("✅ Drift data generated!")
print("="*60)
print(f"Saved to: {current_path}")
print(f"Rows: {len(drift_df)}, Columns: {len(drift_df.columns)}")
