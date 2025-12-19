"""
Computational analytics and aggregations for Labor Market data
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from collections import Counter

from app.utils.logging import logger


class DataAggregator:
    """Handles computational analytics and aggregations"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.aggregations: Dict[str, Any] = {}
    
    def compute_all_aggregations(self) -> Dict[str, Any]:
        """Compute all aggregations"""
        logger.info("Computing dataset aggregations", show_ui=True)
        
        self.aggregations = {
            'occupation_stats': self._compute_occupation_stats(),
            'industry_stats': self._compute_industry_stats(),
            'task_stats': self._compute_task_stats(),
            'employment_stats': self._compute_employment_stats(),
            'wage_stats': self._compute_wage_stats(),
            'work_activity_stats': self._compute_work_activity_stats(),
        }
        
        logger.info("✓ All aggregations computed", show_ui=True)
        
        return self.aggregations
    
    def _compute_occupation_stats(self) -> Dict[str, Any]:
        """Compute occupation-level statistics"""
        stats = {}
        
        if 'ONET job title' in self.df.columns:
            stats['total_occupations'] = self.df['ONET job title'].nunique()
            stats['occupation_counts'] = self.df['ONET job title'].value_counts().to_dict()
            stats['top_10_occupations'] = self.df['ONET job title'].value_counts().head(10).to_dict()
        
        return stats
    
    def _compute_industry_stats(self) -> Dict[str, Any]:
        """Compute industry-level statistics"""
        stats = {}
        
        if 'Industry title' in self.df.columns:
            stats['total_industries'] = self.df['Industry title'].nunique()
            stats['industry_counts'] = self.df['Industry title'].value_counts().to_dict()
            stats['top_10_industries'] = self.df['Industry title'].value_counts().head(10).to_dict()
            
            # Occupation count per industry
            if 'ONET job title' in self.df.columns:
                stats['occupations_per_industry'] = (
                    self.df.groupby('Industry title')['ONET job title']
                    .nunique()
                    .to_dict()
                )
        
        return stats
    
    def _compute_task_stats(self) -> Dict[str, Any]:
        """Compute task-related statistics"""
        stats = {}
        
        if 'Detailed job tasks_list' in self.df.columns:
            # Task counts per row
            stats['avg_tasks_per_job'] = self.df['Detailed job tasks_count'].mean()
            stats['max_tasks_per_job'] = self.df['Detailed job tasks_count'].max()
            stats['min_tasks_per_job'] = self.df['Detailed job tasks_count'].min()
            
            # Flatten all tasks
            all_tasks = []
            for tasks_list in self.df['Detailed job tasks_list'].dropna():
                if isinstance(tasks_list, list):
                    all_tasks.extend(tasks_list)
            
            stats['total_unique_tasks'] = len(set(all_tasks))
            stats['total_tasks'] = len(all_tasks)
            
            # Most common tasks
            task_counts = Counter(all_tasks)
            stats['top_20_tasks'] = dict(task_counts.most_common(20))
        
        # Task hours
        if 'Hours per week spent on task' in self.df.columns:
            stats['avg_hours_per_task'] = self.df['Hours per week spent on task'].mean()
            stats['total_task_hours'] = self.df['Hours per week spent on task'].sum()
        
        return stats
    
    def _compute_employment_stats(self) -> Dict[str, Any]:
        """Compute employment statistics"""
        stats = {}
        
        if 'Employment' in self.df.columns:
            stats['total_employment'] = self.df['Employment'].sum()
            stats['avg_employment'] = self.df['Employment'].mean()
            stats['median_employment'] = self.df['Employment'].median()
            
            # Employment by industry
            if 'Industry title' in self.df.columns:
                stats['employment_by_industry'] = (
                    self.df.groupby('Industry title')['Employment']
                    .sum()
                    .sort_values(ascending=False)
                    .to_dict()
                )
                
                stats['top_10_industries_by_employment'] = (
                    dict(list(stats['employment_by_industry'].items())[:10])
                )
            
            # Employment by occupation
            if 'ONET job title' in self.df.columns:
                stats['employment_by_occupation'] = (
                    self.df.groupby('ONET job title')['Employment']
                    .sum()
                    .sort_values(ascending=False)
                    .head(20)
                    .to_dict()
                )
        
        return stats
    
    def _compute_wage_stats(self) -> Dict[str, Any]:
        """Compute wage statistics"""
        stats = {}
        
        if 'Hourly wage' in self.df.columns:
            stats['avg_hourly_wage'] = self.df['Hourly wage'].mean()
            stats['median_hourly_wage'] = self.df['Hourly wage'].median()
            stats['min_hourly_wage'] = self.df['Hourly wage'].min()
            stats['max_hourly_wage'] = self.df['Hourly wage'].max()
            
            # Wage by industry
            if 'Industry title' in self.df.columns:
                stats['avg_wage_by_industry'] = (
                    self.df.groupby('Industry title')['Hourly wage']
                    .mean()
                    .sort_values(ascending=False)
                    .to_dict()
                )
            
            # Wage by occupation
            if 'ONET job title' in self.df.columns:
                stats['avg_wage_by_occupation'] = (
                    self.df.groupby('ONET job title')['Hourly wage']
                    .mean()
                    .sort_values(ascending=False)
                    .head(20)
                    .to_dict()
                )
        
        return stats
    
    def _compute_work_activity_stats(self) -> Dict[str, Any]:
        """Compute work activity statistics"""
        stats = {}
        
        if 'Detailed work activities_list' in self.df.columns:
            # Activity counts
            stats['avg_activities_per_job'] = self.df['Detailed work activities_count'].mean()
            
            # Flatten all activities
            all_activities = []
            for activities_list in self.df['Detailed work activities_list'].dropna():
                if isinstance(activities_list, list):
                    all_activities.extend(activities_list)
            
            stats['total_unique_activities'] = len(set(all_activities))
            
            # Most common activities
            activity_counts = Counter(all_activities)
            stats['top_20_activities'] = dict(activity_counts.most_common(20))
        
        return stats
    
    def get_aggregation(self, key: str) -> Any:
        """Get specific aggregation result"""
        return self.aggregations.get(key, {})
    
    def query_aggregations(self, query_type: str, **kwargs) -> Any:
        """Query aggregations dynamically"""
        if query_type == 'occupation_count':
            return self.aggregations.get('occupation_stats', {}).get('total_occupations', 0)
        
        elif query_type == 'industry_employment':
            industry = kwargs.get('industry')
            employment_by_industry = self.aggregations.get('employment_stats', {}).get('employment_by_industry', {})
            return employment_by_industry.get(industry, 0)
        
        elif query_type == 'top_occupations_by_employment':
            n = kwargs.get('n', 10)
            employment_by_occ = self.aggregations.get('employment_stats', {}).get('employment_by_occupation', {})
            return dict(list(employment_by_occ.items())[:n])
        
        elif query_type == 'industries_by_task_density':
            # Industries with highest average task count
            if 'Industry title' in self.df.columns and 'Detailed job tasks_count' in self.df.columns:
                result = (
                    self.df.groupby('Industry title')['Detailed job tasks_count']
                    .mean()
                    .sort_values(ascending=False)
                    .head(kwargs.get('n', 10))
                    .to_dict()
                )
                return result
        
        return None
