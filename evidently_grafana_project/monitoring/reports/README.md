# This directory contains drift detection reports

## Report Types

### Data Drift Reports
- Filename pattern: `data_drift_report_YYYYMMDD_HHMMSS.html`
- Contains: Feature distribution comparisons, statistical tests, drift detection results

### Model Drift Reports
- Filename pattern: `model_drift_report_YYYYMMDD_HHMMSS.html`
- Contains: Model performance metrics, prediction analysis, error distributions

### Drift Results (JSON)
- Filename pattern: `drift_results_YYYYMMDD_HHMMSS.json`
- Contains: Structured drift detection results, metrics, retraining decisions

## Viewing Reports

Reports are generated as HTML files. To view:
1. Navigate to this directory
2. Open any `.html` file in your web browser
3. Reports include interactive visualizations from Evidently

## Report Retention

Reports are kept indefinitely by default. Consider implementing a cleanup policy:
- Keep last 30 days of reports
- Archive older reports to cloud storage
- Automated cleanup via Airflow DAG (optional)

## Example Report Contents

### Data Drift Report includes:
- Dataset-level drift summary
- Per-feature drift detection
- Feature distribution plots
- Correlation changes
- Missing values analysis

### Model Drift Report includes:
- Model quality metrics (R², MAE, RMSE)
- Predicted vs actual scatter plots
- Error distribution plots
- Performance comparison (reference vs current)
