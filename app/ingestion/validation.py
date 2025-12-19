"""
Data validation for ONET labor market data
"""
import pandas as pd
from typing import Dict, List, Tuple
from ..utils import setup_logger

logger = setup_logger(__name__)

class DataValidator:
    """Validates data quality and structure"""
    
    REQUIRED_COLUMNS = [
        'Industry title',
        'ONET job title',
        'Employment'
    ]
    
    RECOMMENDED_COLUMNS = [
        'Detailed job tasks',
        'Detailed work activities',
        'Job description',
        'Hourly wage',
        'Total hours worked per week'
    ]
    
    def __init__(self):
        self.validation_results = {}
    
    def validate(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Validate dataset
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Tuple of (is_valid, validation_results)
        """
        logger.info("Starting data validation...")
        
        results = {
            'required_columns_present': self._check_required_columns(df),
            'recommended_columns_present': self._check_recommended_columns(df),
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_quality': self._check_data_quality(df),
            'warnings': [],
            'errors': []
        }
        
        # Determine if valid
        is_valid = (
            results['required_columns_present']['all_present'] and
            results['row_count'] > 0
        )
        
        # Compile warnings
        if not results['recommended_columns_present']['all_present']:
            missing = results['recommended_columns_present']['missing']
            results['warnings'].append(f"Missing recommended columns: {', '.join(missing)}")
        
        if results['data_quality']['high_missing_rate_columns']:
            cols = ', '.join(results['data_quality']['high_missing_rate_columns'])
            results['warnings'].append(f"High missing rate in columns: {cols}")
        
        # Compile errors
        if not results['required_columns_present']['all_present']:
            missing = results['required_columns_present']['missing']
            results['errors'].append(f"Missing required columns: {', '.join(missing)}")
        
        if results['row_count'] == 0:
            results['errors'].append("Dataset is empty")
        
        self.validation_results = results
        
        if is_valid:
            logger.info("Data validation passed")
        else:
            logger.error(f"Data validation failed: {results['errors']}")
        
        return is_valid, results
    
    def _check_required_columns(self, df: pd.DataFrame) -> Dict:
        """Check if required columns are present"""
        present = [col for col in self.REQUIRED_COLUMNS if col in df.columns]
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        
        return {
            'all_present': len(missing) == 0,
            'present': present,
            'missing': missing
        }
    
    def _check_recommended_columns(self, df: pd.DataFrame) -> Dict:
        """Check if recommended columns are present"""
        present = [col for col in self.RECOMMENDED_COLUMNS if col in df.columns]
        missing = [col for col in self.RECOMMENDED_COLUMNS if col not in df.columns]
        
        return {
            'all_present': len(missing) == 0,
            'present': present,
            'missing': missing
        }
    
    def _check_data_quality(self, df: pd.DataFrame) -> Dict:
        """Check data quality metrics"""
        quality = {
            'missing_rate_by_column': {},
            'high_missing_rate_columns': [],
            'duplicate_rows': 0,
            'zero_employment_rows': 0
        }
        
        # Missing rate per column
        for col in df.columns:
            missing_rate = df[col].isna().sum() / len(df) * 100
            quality['missing_rate_by_column'][col] = round(missing_rate, 2)
            
            if missing_rate > 50:  # More than 50% missing
                quality['high_missing_rate_columns'].append(col)
        
        # Check for duplicate rows
        quality['duplicate_rows'] = df.duplicated().sum()
        
        # Check for rows with zero employment
        if 'Employment' in df.columns:
            quality['zero_employment_rows'] = (df['Employment'] == 0).sum()
        
        return quality
    
    def get_validation_summary(self) -> str:
        """Get a human-readable validation summary"""
        if not self.validation_results:
            return "No validation performed yet"
        
        lines = []
        lines.append("=" * 60)
        lines.append("DATA VALIDATION SUMMARY")
        lines.append("=" * 60)
        
        # Basic info
        lines.append(f"Rows: {self.validation_results['row_count']}")
        lines.append(f"Columns: {self.validation_results['column_count']}")
        
        # Required columns
        req_cols = self.validation_results['required_columns_present']
        lines.append(f"\nRequired columns: {'✓ All present' if req_cols['all_present'] else '✗ Missing some'}")
        if req_cols['missing']:
            lines.append(f"  Missing: {', '.join(req_cols['missing'])}")
        
        # Recommended columns
        rec_cols = self.validation_results['recommended_columns_present']
        lines.append(f"Recommended columns: {'✓ All present' if rec_cols['all_present'] else '⚠ Missing some'}")
        if rec_cols['missing']:
            lines.append(f"  Missing: {', '.join(rec_cols['missing'])}")
        
        # Data quality
        quality = self.validation_results['data_quality']
        lines.append(f"\nData Quality:")
        lines.append(f"  Duplicate rows: {quality['duplicate_rows']}")
        lines.append(f"  Zero employment rows: {quality['zero_employment_rows']}")
        
        if quality['high_missing_rate_columns']:
            lines.append(f"  High missing rate columns: {', '.join(quality['high_missing_rate_columns'])}")
        
        # Warnings and errors
        if self.validation_results['warnings']:
            lines.append(f"\n⚠ Warnings:")
            for warning in self.validation_results['warnings']:
                lines.append(f"  - {warning}")
        
        if self.validation_results['errors']:
            lines.append(f"\n✗ Errors:")
            for error in self.validation_results['errors']:
                lines.append(f"  - {error}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
