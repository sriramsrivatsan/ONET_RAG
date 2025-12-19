"""
CSV loading and validation for Labor Market data
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import streamlit as st
from io import BytesIO

from app.utils.logging import logger
from app.utils.helpers import bytes_to_mb, compute_file_hash


class CSVLoader:
    """Handles CSV file loading and validation"""
    
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}
        self.validation_results: Dict[str, Any] = {}
    
    def load_from_upload(self, uploaded_file) -> bool:
        """Load CSV from Streamlit uploaded file"""
        try:
            # Store file metadata
            file_size_mb = bytes_to_mb(uploaded_file.size)
            self.metadata['filename'] = uploaded_file.name
            self.metadata['file_size_mb'] = file_size_mb
            self.metadata['file_hash'] = compute_file_hash(uploaded_file.getvalue())
            
            logger.info(f"Loading CSV file: {uploaded_file.name} ({file_size_mb:.2f} MB)", show_ui=True)
            
            # Load CSV
            self.df = pd.read_csv(uploaded_file)
            
            logger.info(f"✓ Loaded {len(self.df):,} rows and {len(self.df.columns)} columns", show_ui=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load CSV: {str(e)}", show_ui=True)
            return False
    
    def load_from_path(self, filepath: str) -> bool:
        """Load CSV from file path"""
        try:
            logger.info(f"Loading CSV from: {filepath}", show_ui=True)
            
            self.df = pd.read_csv(filepath)
            self.metadata['filename'] = filepath.split('/')[-1]
            
            logger.info(f"✓ Loaded {len(self.df):,} rows and {len(self.df.columns)} columns", show_ui=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load CSV: {str(e)}", show_ui=True)
            return False
    
    def validate_dataset(self) -> Dict[str, Any]:
        """Validate the loaded dataset"""
        if self.df is None:
            return {'valid': False, 'errors': ['No dataset loaded']}
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # Basic statistics
            results['statistics']['total_rows'] = len(self.df)
            results['statistics']['total_columns'] = len(self.df.columns)
            results['statistics']['memory_usage_mb'] = self.df.memory_usage(deep=True).sum() / (1024 * 1024)
            
            # Check for required columns
            expected_columns = [
                'Industry title', 'ONET job title', 'Job description',
                'Detailed work activities', 'Detailed job tasks'
            ]
            
            missing_columns = [col for col in expected_columns if col not in self.df.columns]
            if missing_columns:
                results['warnings'].append(f"Missing expected columns: {', '.join(missing_columns)}")
            
            # Check for missing values
            missing_counts = self.df.isnull().sum()
            high_missing = missing_counts[missing_counts > len(self.df) * 0.5]
            if len(high_missing) > 0:
                results['warnings'].append(f"Columns with >50% missing: {list(high_missing.index)}")
            
            results['statistics']['missing_value_counts'] = missing_counts.to_dict()
            
            # Analyze data types
            results['statistics']['dtypes'] = self.df.dtypes.astype(str).to_dict()
            
            # Analyze cardinality
            if 'Industry title' in self.df.columns:
                results['statistics']['unique_industries'] = self.df['Industry title'].nunique()
                results['statistics']['industries'] = self.df['Industry title'].value_counts().head(10).to_dict()
            
            if 'ONET job title' in self.df.columns:
                results['statistics']['unique_occupations'] = self.df['ONET job title'].nunique()
                results['statistics']['occupations_sample'] = self.df['ONET job title'].value_counts().head(10).to_dict()
            
            # Check numeric columns
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                results['statistics']['numeric_columns'] = numeric_cols
                results['statistics']['numeric_stats'] = self.df[numeric_cols].describe().to_dict()
            
            logger.info("✓ Dataset validation complete", show_ui=True)
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}", show_ui=True)
            results['valid'] = False
            results['errors'].append(str(e))
        
        self.validation_results = results
        return results
    
    def get_column_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about each column"""
        if self.df is None:
            return []
        
        column_info = []
        for col in self.df.columns:
            info = {
                'name': col,
                'dtype': str(self.df[col].dtype),
                'non_null_count': self.df[col].notna().sum(),
                'null_count': self.df[col].isna().sum(),
                'unique_count': self.df[col].nunique(),
                'sample_values': self.df[col].dropna().head(3).tolist()
            }
            column_info.append(info)
        
        return column_info
    
    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """Get the loaded DataFrame"""
        return self.df
