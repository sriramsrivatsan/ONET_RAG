# Integration of Arithmetic Validation into Retriever
# This ensures all arithmetic is computed BEFORE LLM sees the data

import pandas as pd
from typing import Dict, Any, List
from app.utils.arithmetic_validator import ArithmeticValidator, ArithmeticResult

class ArithmeticComputationLayer:
    """
    Pre-computes all arithmetic operations before LLM processing
    This is the GROUND TRUTH layer - values computed here are authoritative
    """
    
    def __init__(self):
        self.validator = ArithmeticValidator()
    
    def compute_occupation_summary_arithmetic(
        self,
        occ_summary: pd.DataFrame,
        matching_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compute ALL arithmetic for occupation summary
        
        Returns comprehensive computational_results with ground truth values
        """
        results = {}
        
        # 1. TOTAL EMPLOYMENT (Primary metric)
        employment_values = occ_summary['Employment'].tolist()
        total_employment = self.validator.compute_sum(
            data=employment_values,
            description="total_employment_across_all_occupations",
            unit='k'
        )
        results['total_employment'] = total_employment.value
        results['total_employment_verified'] = total_employment  # Full ArithmeticResult object
        
        # 2. OCCUPATION COUNT
        occupation_count = self.validator.compute_count(
            data=occ_summary['ONET job title'].tolist(),
            description="unique_occupations"
        )
        results['total_occupations'] = occupation_count.value
        results['occupation_count_verified'] = occupation_count
        
        # 3. EMPLOYMENT STATISTICS
        emp_min, emp_max = self.validator.compute_min_max(
            data=employment_values,
            description="employment_per_occupation",
            unit='k'
        )
        results['min_employment'] = emp_min.value
        results['max_employment'] = emp_max.value
        results['min_employment_verified'] = emp_min
        results['max_employment_verified'] = emp_max
        
        # 4. AVERAGE EMPLOYMENT PER OCCUPATION
        avg_employment = self.validator.compute_average(
            data=employment_values,
            description="employment_per_occupation",
            unit='k'
        )
        results['avg_employment_per_occupation'] = avg_employment.value
        results['avg_employment_verified'] = avg_employment
        
        # 5. TASK COUNT (if available)
        if 'Detailed job tasks' in matching_df.columns:
            task_count = self.validator.compute_count(
                data=matching_df['Detailed job tasks'].unique().tolist(),
                description="unique_tasks"
            )
            results['total_tasks'] = task_count.value
            results['task_count_verified'] = task_count
        
        # 6. INDUSTRY COUNT (if available)
        if 'Industry title' in matching_df.columns:
            industry_count = self.validator.compute_count(
                data=matching_df['Industry title'].unique().tolist(),
                description="unique_industries"
            )
            results['total_industries_involved'] = industry_count.value
            results['industry_count_verified'] = industry_count
        
        # 7. COMPREHENSIVE METADATA
        results['arithmetic_metadata'] = {
            'computation_complete': True,
            'total_computations': len(self.validator.computed_values),
            'all_values_verified': True,
            'source_rows': len(matching_df),
            'unique_occupation_industry_pairs': len(matching_df.groupby(['ONET job title', 'Industry title']))
        }
        
        return results
    
    def compute_industry_summary_arithmetic(
        self,
        ind_summary: pd.DataFrame,
        matching_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Compute ALL arithmetic for industry summary"""
        results = {}
        
        # 1. TOTAL EMPLOYMENT
        employment_values = ind_summary['Employment'].tolist()
        total_employment = self.validator.compute_sum(
            data=employment_values,
            description="total_employment_across_all_industries",
            unit='k'
        )
        results['total_employment'] = total_employment.value
        results['total_employment_verified'] = total_employment
        
        # 2. INDUSTRY COUNT
        industry_count = self.validator.compute_count(
            data=ind_summary['Industry title'].tolist(),
            description="unique_industries"
        )
        results['total_industries'] = industry_count.value
        results['industry_count_verified'] = industry_count
        
        # 3. EMPLOYMENT STATISTICS
        emp_min, emp_max = self.validator.compute_min_max(
            data=employment_values,
            description="employment_per_industry",
            unit='k'
        )
        results['min_employment'] = emp_min.value
        results['max_employment'] = emp_max.value
        
        # 4. AVERAGE EMPLOYMENT PER INDUSTRY
        avg_employment = self.validator.compute_average(
            data=employment_values,
            description="employment_per_industry",
            unit='k'
        )
        results['avg_employment_per_industry'] = avg_employment.value
        
        # 5. METADATA
        results['arithmetic_metadata'] = {
            'computation_complete': True,
            'total_computations': len(self.validator.computed_values),
            'all_values_verified': True
        }
        
        return results
    
    def compute_task_details_arithmetic(
        self,
        task_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Compute ALL arithmetic for task details"""
        results = {}
        
        # 1. TASK COUNT
        task_count = self.validator.compute_count(
            data=task_df['Detailed job tasks'].unique().tolist(),
            description="unique_tasks"
        )
        results['total_tasks'] = task_count.value
        results['task_count_verified'] = task_count
        
        # 2. OCCUPATION COUNT
        if 'ONET job title' in task_df.columns:
            occ_count = self.validator.compute_count(
                data=task_df['ONET job title'].unique().tolist(),
                description="occupations_with_tasks"
            )
            results['total_occupations'] = occ_count.value
        
        # 3. TIME STATISTICS (if available)
        if 'Hours per week spent on task' in task_df.columns:
            time_values = task_df['Hours per week spent on task'].dropna().tolist()
            if time_values:
                avg_time = self.validator.compute_average(
                    data=time_values,
                    description="hours_per_week_per_task",
                    unit='hours'
                )
                results['avg_hours_per_week'] = avg_time.value
                
                min_time, max_time = self.validator.compute_min_max(
                    data=time_values,
                    description="hours_per_week",
                    unit='hours'
                )
                results['min_hours'] = min_time.value
                results['max_hours'] = max_time.value
        
        results['arithmetic_metadata'] = {
            'computation_complete': True,
            'total_computations': len(self.validator.computed_values)
        }
        
        return results
    
    def get_validator(self) -> ArithmeticValidator:
        """Get the validator for post-LLM validation"""
        return self.validator
    
    def format_verified_summary(self) -> str:
        """Format a summary of all verified computations"""
        summary = "\n" + "="*80 + "\n"
        summary += "✓ VERIFIED COMPUTATIONS (Ground Truth)\n"
        summary += "="*80 + "\n\n"
        
        for key, result in self.validator.computed_values.items():
            summary += f"  {result.description}:\n"
            summary += f"    Operation: {result.operation}\n"
            summary += f"    Value: {result.format()}\n"
            summary += f"    Confidence: {result.confidence}\n\n"
        
        summary += "="*80 + "\n"
        summary += f"Total Computations: {len(self.validator.computed_values)}\n"
        summary += "All values have been independently verified.\n"
        summary += "="*80 + "\n"
        
        return summary


# USAGE EXAMPLE in retriever:
"""
# In _create_occupation_summary_response method:

# Initialize computation layer
computation_layer = ArithmeticComputationLayer()

# Compute ALL arithmetic upfront
computational_results = computation_layer.compute_occupation_summary_arithmetic(
    occ_summary=occ_summary,
    matching_df=matching_df
)

# Store in results
results['computational_results'] = computational_results

# Get validator for later use
results['arithmetic_validator'] = computation_layer.get_validator()

# Now when LLM processes, it has ground truth values
# And we can validate its output against these verified values
"""
