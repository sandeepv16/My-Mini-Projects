"""
CLV Model Training Script
Calculates Customer Lifetime Value and trains a predictive model
"""
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import json
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CLVModelTrainer:
    def __init__(self, data_path, model_dir='models', reference_dir='data/reference'):
        self.data_path = data_path
        self.model_dir = Path(model_dir)
        self.reference_dir = Path(reference_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.reference_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.scaler = None
        self.feature_columns = []
        
    def load_data(self):
        """Load and preprocess the retail data"""
        logger.info(f"Loading data from {self.data_path}")
        df = pd.read_csv(self.data_path, encoding='latin-1')
        
        # Clean the data
        df = df.dropna(subset=['CustomerID'])
        df['CustomerID'] = df['CustomerID'].astype(int)
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], format='%d-%m-%Y %H:%M')
        
        # Remove returns (negative quantities)
        df = df[df['Quantity'] > 0]
        df = df[df['UnitPrice'] > 0]
        
        # Calculate total amount
        df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
        
        logger.info(f"Loaded {len(df)} records with {df['CustomerID'].nunique()} unique customers")
        return df
    
    def calculate_rfm_features(self, df):
        """Calculate RFM (Recency, Frequency, Monetary) features"""
        logger.info("Calculating RFM features")
        
        # Get the latest date in dataset as reference
        current_date = df['InvoiceDate'].max()
        
        # Aggregate by customer
        rfm = df.groupby('CustomerID').agg({
            'InvoiceDate': lambda x: (current_date - x.max()).days,  # Recency
            'InvoiceNo': 'nunique',  # Frequency
            'TotalAmount': 'sum'  # Monetary
        }).reset_index()
        
        rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']
        
        # Additional features
        customer_stats = df.groupby('CustomerID').agg({
            'Quantity': ['mean', 'sum'],
            'UnitPrice': 'mean',
            'InvoiceNo': 'nunique',
            'StockCode': 'nunique',
            'Country': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown'
        }).reset_index()
        
        customer_stats.columns = ['CustomerID', 'AvgQuantity', 'TotalQuantity', 
                                  'AvgUnitPrice', 'NumOrders', 'NumProducts', 'Country']
        
        # Merge features
        rfm = rfm.merge(customer_stats, on='CustomerID')
        
        # Calculate CLV (target variable)
        # Simple CLV = Monetary * (Frequency / Recency) * AvgLifespan
        # Assuming average customer lifespan of 1 year (365 days)
        rfm['CLV'] = rfm['Monetary'] * (rfm['Frequency'] / (rfm['Recency'] + 1)) * 365
        
        logger.info(f"Calculated features for {len(rfm)} customers")
        return rfm
    
    def prepare_features(self, rfm_df):
        """Prepare features for model training"""
        logger.info("Preparing features")
        
        # Encode categorical variable
        country_dummies = pd.get_dummies(rfm_df['Country'], prefix='Country')
        
        # Select numerical features
        feature_df = rfm_df[['Recency', 'Frequency', 'Monetary', 'AvgQuantity', 
                            'TotalQuantity', 'AvgUnitPrice', 'NumOrders', 'NumProducts']]
        
        # Combine with country dummies
        feature_df = pd.concat([feature_df, country_dummies], axis=1)
        
        self.feature_columns = feature_df.columns.tolist()
        
        X = feature_df.values
        y = rfm_df['CLV'].values
        
        logger.info(f"Prepared {X.shape[1]} features")
        return X, y, rfm_df
    
    def train_model(self, X, y):
        """Train the CLV prediction model"""
        logger.info("Training CLV model")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        logger.info(f"Model trained - Train R²: {train_score:.4f}, Test R²: {test_score:.4f}")
        
        return {
            'train_score': train_score,
            'test_score': test_score,
            'n_features': X.shape[1],
            'n_samples': X.shape[0]
        }
    
    def save_model(self, metadata):
        """Save the trained model and metadata"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save model
        model_path = self.model_dir / f'clv_model_{timestamp}.joblib'
        joblib.dump(self.model, model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Save scaler
        scaler_path = self.model_dir / f'scaler_{timestamp}.joblib'
        joblib.dump(self.scaler, scaler_path)
        logger.info(f"Scaler saved to {scaler_path}")
        
        # Save feature columns
        features_path = self.model_dir / f'features_{timestamp}.json'
        with open(features_path, 'w') as f:
            json.dump(self.feature_columns, f, indent=2)
        
        # Save metadata
        metadata.update({
            'timestamp': timestamp,
            'model_path': str(model_path),
            'scaler_path': str(scaler_path),
            'features_path': str(features_path),
            'feature_columns': self.feature_columns
        })
        
        metadata_path = self.model_dir / f'metadata_{timestamp}.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata saved to {metadata_path}")
        
        # Save as latest
        joblib.dump(self.model, self.model_dir / 'clv_model_latest.joblib')
        joblib.dump(self.scaler, self.model_dir / 'scaler_latest.joblib')
        with open(self.model_dir / 'features_latest.json', 'w') as f:
            json.dump(self.feature_columns, f, indent=2)
        with open(self.model_dir / 'metadata_latest.json', 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return model_path, metadata_path
    
    def save_reference_data(self, rfm_df):
        """Save reference data for drift detection"""
        reference_path = self.reference_dir / 'reference_data.csv'
        rfm_df.to_csv(reference_path, index=False)
        logger.info(f"Reference data saved to {reference_path}")
        return reference_path
    
    def run(self):
        """Run the complete training pipeline"""
        logger.info("Starting CLV model training pipeline")
        
        try:
            # Load data
            df = self.load_data()
            
            # Calculate features
            rfm_df = self.calculate_rfm_features(df)
            
            # Prepare features
            X, y, rfm_with_clv = self.prepare_features(rfm_df)
            
            # Train model
            metadata = self.train_model(X, y)
            
            # Save model
            model_path, metadata_path = self.save_model(metadata)
            
            # Save reference data
            reference_path = self.save_reference_data(rfm_with_clv)
            
            logger.info("Training pipeline completed successfully")
            
            return {
                'status': 'success',
                'model_path': str(model_path),
                'metadata_path': str(metadata_path),
                'reference_path': str(reference_path),
                'metrics': metadata
            }
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {str(e)}")
            raise


if __name__ == '__main__':
    import sys
    
    data_path = sys.argv[1] if len(sys.argv) > 1 else 'Online_Retail.csv.csv'
    
    trainer = CLVModelTrainer(data_path)
    result = trainer.run()
    
    print(json.dumps(result, indent=2))
