#!/usr/bin/env python3
"""
Validation script to verify metrics are being set in drift_detector.py
Run this to confirm all metrics are properly instrumented
"""

import sys
import re
from pathlib import Path

def check_metrics_instrumentation():
    """Verify all metrics are defined and being used"""
    
    drift_detector_path = Path(__file__).parent / "monitoring" / "drift_detector.py"
    
    if not drift_detector_path.exists():
        print(f"❌ File not found: {drift_detector_path}")
        return False
    
    with open(drift_detector_path, 'r') as f:
        content = f.read()
    
    print("=" * 70)
    print("METRICS INSTRUMENTATION VALIDATION")
    print("=" * 70)
    
    # Expected metrics
    expected_metrics = {
        'drift_detected_counter': 'Counter',
        'drift_score_gauge': 'Gauge',
        'drifted_columns_gauge': 'Gauge',
        'drift_share_gauge': 'Gauge',
        'model_performance_gauge': 'Gauge',
        'r2_score_gauge': 'Gauge',
        'detection_timestamp_gauge': 'Gauge'
    }
    
    print("\n1. CHECKING METRIC DEFINITIONS:")
    print("-" * 70)
    
    all_defined = True
    for metric_name, metric_type in expected_metrics.items():
        pattern = rf'{metric_name}\s*=\s*{metric_type}'
        if re.search(pattern, content):
            print(f"✅ {metric_name:30s} ({metric_type:6s}) - DEFINED")
        else:
            print(f"❌ {metric_name:30s} ({metric_type:6s}) - MISSING")
            all_defined = False
    
    print("\n2. CHECKING DATA DRIFT METRICS USAGE:")
    print("-" * 70)
    
    data_drift_checks = [
        ('drift_detected_counter.labels(drift_type=\'data\')', 'Data drift counter increment'),
        ('drift_score_gauge.labels(feature=\'dataset\')', 'Data drift score gauge'),
        ('drifted_columns_gauge.labels(drift_type=\'data\')', 'Drifted columns gauge'),
        ('drift_share_gauge.labels(drift_type=\'data\')', 'Drift share gauge'),
        ('detection_timestamp_gauge.set', 'Detection timestamp gauge'),
    ]
    
    for pattern, description in data_drift_checks:
        if re.search(re.escape(pattern), content):
            print(f"✅ {description:40s} - SET")
        else:
            print(f"❌ {description:40s} - NOT SET")
            all_defined = False
    
    print("\n3. CHECKING MODEL DRIFT METRICS USAGE:")
    print("-" * 70)
    
    model_drift_checks = [
        ('drift_detected_counter.labels(drift_type=\'model\')', 'Model drift counter increment'),
        ('model_performance_gauge.labels(metric=\'r2\')', 'R² performance gauge'),
        ('model_performance_gauge.labels(metric=\'mae\')', 'MAE performance gauge'),
        ('model_performance_gauge.labels(metric=\'rmse\')', 'RMSE performance gauge'),
        ('r2_score_gauge.labels(data_type=\'reference\')', 'Reference R² gauge'),
        ('r2_score_gauge.labels(data_type=\'current\')', 'Current R² gauge'),
    ]
    
    for pattern, description in model_drift_checks:
        if re.search(re.escape(pattern), content):
            print(f"✅ {description:40s} - SET")
        else:
            print(f"❌ {description:40s} - NOT SET")
            all_defined = False
    
    print("\n4. CHECKING PROMETHEUS PUSH:")
    print("-" * 70)
    
    if 'push_to_gateway' in content and 'registry=REGISTRY' in content:
        print(f"✅ push_to_gateway with REGISTRY - CONFIGURED")
    else:
        print(f"❌ push_to_gateway configuration - MISSING or INCORRECT")
        all_defined = False
    
    if 'from prometheus_client import REGISTRY' in content:
        print(f"✅ REGISTRY import - PRESENT")
    else:
        print(f"❌ REGISTRY import - MISSING")
        all_defined = False
    
    print("\n" + "=" * 70)
    if all_defined:
        print("✅ ALL METRICS PROPERLY INSTRUMENTED")
        print("=" * 70)
        return True
    else:
        print("❌ SOME METRICS ARE MISSING OR NOT CONFIGURED")
        print("=" * 70)
        return False

def count_metric_operations():
    """Count total metric operations in code"""
    
    drift_detector_path = Path(__file__).parent / "monitoring" / "drift_detector.py"
    
    with open(drift_detector_path, 'r') as f:
        content = f.read()
    
    print("\n5. METRIC OPERATIONS COUNT:")
    print("-" * 70)
    
    inc_count = len(re.findall(r'\.inc\(\)', content))
    set_count = len(re.findall(r'\.set\(', content))
    
    print(f"Counter .inc() calls     : {inc_count} operations")
    print(f"Gauge .set() calls       : {set_count} operations")
    print(f"Total metric operations  : {inc_count + set_count} operations")
    
    if inc_count >= 2 and set_count >= 6:
        print(f"\n✅ Sufficient metric operations for comprehensive monitoring")
    else:
        print(f"\n⚠️  Consider adding more metric operations for better observability")

if __name__ == '__main__':
    try:
        success = check_metrics_instrumentation()
        count_metric_operations()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        sys.exit(1)
