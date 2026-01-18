"""
Drift Detection using Evidently
Monitors data and model drift for CLV model
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime
import joblib

from evidently.legacy.report import Report
from evidently.legacy.metric_preset.data_drift import DataDriftPreset
from evidently.legacy.metric_preset.regression_performance import RegressionPreset

from prometheus_client import Counter, Gauge, push_to_gateway
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
drift_detected_counter = Counter(
    'clv_drift_detected_total', 
    'Number of times drift was detected',
    ['drift_type']
)

drift_score_gauge = Gauge(
    'clv_drift_score',
    'Current drift score',
    ['feature']
)

drifted_columns_gauge = Gauge(
    'clv_drifted_columns_count',
    'Number of drifted columns',
    ['drift_type']
)

drift_share_gauge = Gauge(
    'clv_drift_share',
    'Share of drifted features',
    ['drift_type']
)

model_performance_gauge = Gauge(
    'clv_model_performance',
    'Model performance metrics',
    ['metric']
)

r2_score_gauge = Gauge(
    'clv_r2_score',
    'R² score for model performance',
    ['data_type']  # reference or current
)

detection_timestamp_gauge = Gauge(
    'clv_drift_detection_timestamp',
    'Timestamp of last drift detection'
)


class DriftDetector:
    def __init__(
        self, 
        reference_data_path='data/reference/reference_data.csv',
        model_dir='models',
        report_dir='monitoring/reports',
        prometheus_gateway='localhost:9091'
    ):
        self.reference_data_path = Path(reference_data_path)
        self.model_dir = Path(model_dir)
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.prometheus_gateway = prometheus_gateway
        
        self.reference_data = None
        self.model = None
        self.scaler = None
        self.feature_columns = []
        
    def load_reference_data(self):
        """Load reference data for comparison"""
        logger.info(f"Loading reference data from {self.reference_data_path}")
        self.reference_data = pd.read_csv(self.reference_data_path, encoding='latin-1', on_bad_lines='skip')
        logger.info(f"Loaded {len(self.reference_data)} reference records")
        return self.reference_data
    
    def load_model(self):
        """Load the trained model"""
        logger.info("Loading trained model")
        
        model_path = self.model_dir / 'clv_model_latest.joblib'
        scaler_path = self.model_dir / 'scaler_latest.joblib'
        features_path = self.model_dir / 'features_latest.json'
        
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        
        with open(features_path, 'r') as f:
            self.feature_columns = json.load(f)
        
        logger.info(f"Model loaded with {len(self.feature_columns)} features")
        
    def load_current_data(self, current_data_path):
        """Load current data for drift detection"""
        logger.info(f"Loading current data from {current_data_path}")
        
        # Import the trainer to reuse data processing logic
        import sys
        sys.path.append('scripts')
        from train_clv_model import CLVModelTrainer
        
        trainer = CLVModelTrainer(current_data_path)
        df = trainer.load_data()
        rfm_df = trainer.calculate_rfm_features(df)
        
        logger.info(f"Processed {len(rfm_df)} current records")
        return rfm_df
    
    def prepare_for_prediction(self, data):
        """Prepare data for model prediction"""
        # Encode categorical
        country_dummies = pd.get_dummies(data['Country'], prefix='Country')
        
        # Select numerical features
        feature_df = data[['Recency', 'Frequency', 'Monetary', 'AvgQuantity', 
                          'TotalQuantity', 'AvgUnitPrice', 'NumOrders', 'NumProducts']]
        
        # Combine
        feature_df = pd.concat([feature_df, country_dummies], axis=1)
        
        # Ensure all expected columns are present
        for col in self.feature_columns:
            if col not in feature_df.columns:
                feature_df[col] = 0
        
        # Reorder columns to match training
        feature_df = feature_df[self.feature_columns]
        
        return feature_df
    
    def detect_data_drift(self, current_data):
        """Detect data drift using Evidently"""
        logger.info("Detecting data drift")
        
        # Select common columns
        common_columns = ['Recency', 'Frequency', 'Monetary', 'AvgQuantity', 
                         'TotalQuantity', 'AvgUnitPrice', 'NumOrders', 'NumProducts']
        
        reference_subset = self.reference_data[common_columns]
        current_subset = current_data[common_columns]
        
        # Create drift report
        # Use preset for data drift (specific metric classes differ across Evidently versions)
        data_drift_report = Report(metrics=[DataDriftPreset()])
        
        data_drift_report.run(
            reference_data=reference_subset,
            current_data=current_subset
        )
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.report_dir / f'data_drift_report_{timestamp}.html'
        data_drift_report.save_html(str(report_path))
        logger.info(f"Data drift report saved to {report_path}")
        
        # Extract drift metrics
        report_dict = data_drift_report.as_dict()
        
        # Check for dataset drift (metrics[0] is DatasetDriftMetric with dataset_drift key)
        dataset_drift = report_dict['metrics'][0]['result']['dataset_drift']
        num_drifted_features = report_dict['metrics'][0]['result']['number_of_drifted_columns']
        drift_share = report_dict['metrics'][0]['result']['share_of_drifted_columns']
        
        logger.info(f"Dataset drift detected: {dataset_drift}")
        logger.info(f"Number of drifted features: {num_drifted_features}")
        logger.info(f"Share of drifted columns: {drift_share:.4f}")
        
        # Update Prometheus metrics
        if dataset_drift:
            drift_detected_counter.labels(drift_type='data').inc()
        
        drift_score_gauge.labels(feature='dataset').set(num_drifted_features)
        drifted_columns_gauge.labels(drift_type='data').set(num_drifted_features)
        drift_share_gauge.labels(drift_type='data').set(drift_share)
        detection_timestamp_gauge.set(datetime.now().timestamp())
        
        return {
            'drift_detected': dataset_drift,
            'num_drifted_features': num_drifted_features,
            'drift_share': drift_share,
            'report_path': str(report_path)
        }
    
    def detect_model_drift(self, reference_data, current_data):
        """Detect model performance drift"""
        logger.info("Detecting model drift")
        
        # Prepare features
        ref_features = self.prepare_for_prediction(reference_data)
        curr_features = self.prepare_for_prediction(current_data)
        
        # Scale features
        ref_features_scaled = self.scaler.transform(ref_features)
        curr_features_scaled = self.scaler.transform(curr_features)
        
        # Make predictions
        ref_predictions = self.model.predict(ref_features_scaled)
        curr_predictions = self.model.predict(curr_features_scaled)
        
        # Add predictions to dataframes
        reference_with_pred = reference_data.copy()
        reference_with_pred['prediction'] = ref_predictions
        reference_with_pred['target'] = reference_data['CLV']
        
        current_with_pred = current_data.copy()
        current_with_pred['prediction'] = curr_predictions
        current_with_pred['target'] = current_data['CLV']
        
        # Create model performance report
        # Use regression preset for model performance metrics
        model_drift_report = Report(metrics=[RegressionPreset()])
        
        model_drift_report.run(
            reference_data=reference_with_pred[['target', 'prediction']],
            current_data=current_with_pred[['target', 'prediction']]
        )
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.report_dir / f'model_drift_report_{timestamp}.html'
        model_drift_report.save_html(str(report_path))
        logger.info(f"Model drift report saved to {report_path}")
        
        # Extract metrics
        report_dict = model_drift_report.as_dict()
        
        # Get R2 scores from current and reference data
        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
        
        current_r2 = r2_score(current_with_pred['target'], current_with_pred['prediction'])
        current_mae = mean_absolute_error(current_with_pred['target'], current_with_pred['prediction'])
        current_rmse = np.sqrt(mean_squared_error(current_with_pred['target'], current_with_pred['prediction']))
        
        reference_r2 = r2_score(reference_with_pred['target'], reference_with_pred['prediction'])
        reference_mae = mean_absolute_error(reference_with_pred['target'], reference_with_pred['prediction'])
        reference_rmse = np.sqrt(mean_squared_error(reference_with_pred['target'], reference_with_pred['prediction']))
        
        # Check for significant performance degradation
        r2_drop = reference_r2 - current_r2
        model_drift_detected = r2_drop > 0.1  # 10% drop threshold
        
        logger.info(f"Reference R²: {reference_r2:.4f}, Current R²: {current_r2:.4f}")
        logger.info(f"Reference MAE: {reference_mae:.4f}, Current MAE: {current_mae:.4f}")
        logger.info(f"Reference RMSE: {reference_rmse:.4f}, Current RMSE: {current_rmse:.4f}")
        logger.info(f"R² drop: {r2_drop:.4f}, Model drift detected: {model_drift_detected}")
        
        # Update Prometheus metrics
        if model_drift_detected:
            drift_detected_counter.labels(drift_type='model').inc()
        
        # Set current model metrics
        model_performance_gauge.labels(metric='r2').set(current_r2)
        model_performance_gauge.labels(metric='mae').set(current_mae)
        model_performance_gauge.labels(metric='rmse').set(current_rmse)
        
        # Set R2 scores by data type
        r2_score_gauge.labels(data_type='reference').set(reference_r2)
        r2_score_gauge.labels(data_type='current').set(current_r2)
        
        # Set detection timestamp
        detection_timestamp_gauge.set(datetime.now().timestamp())
        
        return {
            'model_drift_detected': model_drift_detected,
            'current_r2': current_r2,
            'reference_r2': reference_r2,
            'r2_drop': r2_drop,
            'current_mae': current_mae,
            'reference_mae': reference_mae,
            'current_rmse': current_rmse,
            'reference_rmse': reference_rmse,
            'report_path': str(report_path)
        }
    
    def push_metrics_to_prometheus(self):
        """Push metrics to Prometheus Pushgateway"""
        try:
            from prometheus_client import REGISTRY
            push_to_gateway(
                self.prometheus_gateway, 
                job='clv_drift_monitoring',
                registry=REGISTRY
            )
            logger.info("Metrics pushed to Prometheus")
        except Exception as e:
            logger.warning(f"Failed to push metrics to Prometheus: {str(e)}")
    
    def run_drift_detection(self, current_data_path):
        """Run complete drift detection pipeline"""
        logger.info("Starting drift detection pipeline")
        
        try:
            # Load reference data and model
            self.load_reference_data()
            self.load_model()
            
            # Load current data
            current_data = self.load_current_data(current_data_path)
            
            # Detect data drift
            data_drift_results = self.detect_data_drift(current_data)
            
            # Detect model drift
            model_drift_results = self.detect_model_drift(
                self.reference_data, 
                current_data
            )
            
            # Push metrics to Prometheus
            self.push_metrics_to_prometheus()
            
            # Combine results
            results = {
                'timestamp': datetime.now().isoformat(),
                'data_drift': data_drift_results,
                'model_drift': model_drift_results,
                'retraining_required': (
                    data_drift_results['drift_detected'] or 
                    model_drift_results['model_drift_detected']
                )
            }
            
            # Save results
            results_path = self.report_dir / f'drift_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Drift detection completed. Results saved to {results_path}")
            logger.info(f"Retraining required: {results['retraining_required']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Drift detection failed: {str(e)}")
            raise


if __name__ == '__main__':
    import sys
    
    current_data_path = sys.argv[1] if len(sys.argv) > 1 else 'Online_Retail.csv.csv'
    
    detector = DriftDetector()
    results = detector.run_drift_detection(current_data_path)
    
    print(json.dumps(results, indent=2))
