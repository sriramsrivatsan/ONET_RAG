# Test Suite for Arithmetic Validation System
# Ensures all arithmetic operations are accurate and validated

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.arithmetic_validator import ArithmeticValidator, ArithmeticResult, ArithmeticDiscrepancy
from app.utils.arithmetic_computation import ArithmeticComputationLayer
import pandas as pd


class TestArithmeticValidator(unittest.TestCase):
    """Test core arithmetic validator functionality"""
    
    def setUp(self):
        self.validator = ArithmeticValidator()
    
    def test_compute_sum_basic(self):
        """Test basic sum computation"""
        result = self.validator.compute_sum(
            data=[100.0, 200.0, 300.0],
            description="test_sum",
            unit='k'
        )
        
        self.assertEqual(result.value, 600.0)
        self.assertEqual(result.operation, 'sum')
        self.assertEqual(result.unit, 'k')
        self.assertEqual(result.format(), "600.00k")
    
    def test_compute_sum_empty(self):
        """Test sum with empty data"""
        result = self.validator.compute_sum(
            data=[],
            description="empty_sum",
            unit='k'
        )
        
        self.assertEqual(result.value, 0.0)
        self.assertEqual(result.source_data['count'], 0)
    
    def test_compute_count(self):
        """Test count computation"""
        result = self.validator.compute_count(
            data=['A', 'B', 'C', 'D'],
            description="test_count"
        )
        
        self.assertEqual(result.value, 4)
        self.assertEqual(result.format(), "4")
    
    def test_compute_average(self):
        """Test average computation"""
        result = self.validator.compute_average(
            data=[100.0, 200.0, 300.0],
            description="test_average",
            unit='k'
        )
        
        self.assertEqual(result.value, 200.0)
        self.assertEqual(result.source_data['count'], 3)
        self.assertEqual(result.source_data['sum'], 600.0)
    
    def test_compute_percentage(self):
        """Test percentage computation"""
        result = self.validator.compute_percentage(
            numerator=25.0,
            denominator=100.0,
            description="test_percentage"
        )
        
        self.assertEqual(result.value, 25.0)
        self.assertEqual(result.unit, '%')
        self.assertEqual(result.format(), "25.0%")
    
    def test_compute_percentage_zero_denominator(self):
        """Test percentage with zero denominator"""
        result = self.validator.compute_percentage(
            numerator=25.0,
            denominator=0.0,
            description="test_div_zero"
        )
        
        self.assertEqual(result.value, 0.0)
        self.assertIn('error', result.source_data)
    
    def test_compute_min_max(self):
        """Test min/max computation"""
        min_result, max_result = self.validator.compute_min_max(
            data=[100.0, 300.0, 200.0, 50.0],
            description="test_range",
            unit='k'
        )
        
        self.assertEqual(min_result.value, 50.0)
        self.assertEqual(max_result.value, 300.0)
        self.assertEqual(min_result.operation, 'min')
        self.assertEqual(max_result.operation, 'max')
    
    def test_validate_llm_output_no_discrepancy(self):
        """Test validation when LLM output is correct"""
        # Compute ground truth
        result = self.validator.compute_sum(
            data=[100.0, 200.0],
            description="total",
            unit='k'
        )
        
        # LLM output with correct value
        llm_text = "Total Employment: 300.00 thousand workers across 2 occupations"
        
        # Validate
        discrepancies = self.validator.validate_llm_output(
            llm_text=llm_text,
            expected_values={'total': result}
        )
        
        self.assertEqual(len(discrepancies), 0)
    
    def test_validate_llm_output_with_discrepancy(self):
        """Test validation when LLM output is wrong"""
        # Compute ground truth
        result = self.validator.compute_sum(
            data=[100.0, 200.0],
            description="total",
            unit='k'
        )
        
        # LLM output with WRONG value
        llm_text = "Total Employment: 500.00 thousand workers"
        
        # Validate
        discrepancies = self.validator.validate_llm_output(
            llm_text=llm_text,
            expected_values={'total': result}
        )
        
        self.assertGreater(len(discrepancies), 0)
        
        # Check discrepancy details
        disc = discrepancies[0]
        self.assertEqual(disc.computed_value, 300.0)
        self.assertEqual(disc.llm_value, 500.0)
        self.assertEqual(disc.difference, 200.0)
        self.assertGreater(disc.difference_pct, 0)
        self.assertEqual(disc.severity, 'critical')  # >5% difference
    
    def test_severity_classification(self):
        """Test discrepancy severity classification"""
        # Create validator with test values
        validator = ArithmeticValidator()
        
        # Test MINOR (0.1% - 1%)
        result_minor = validator.compute_sum([1000.0], "test", 'k')
        llm_text_minor = "Total: 1005.0k"  # 0.5% off
        disc_minor = validator.validate_llm_output(llm_text_minor, {'test': result_minor})
        if disc_minor:
            self.assertEqual(disc_minor[0].severity, 'minor')
        
        # Test MAJOR (1% - 5%)
        result_major = validator.compute_sum([1000.0], "test2", 'k')
        llm_text_major = "Total: 1030.0k"  # 3% off
        disc_major = validator.validate_llm_output(llm_text_major, {'test2': result_major})
        if disc_major:
            self.assertEqual(disc_major[0].severity, 'major')
        
        # Test CRITICAL (>5%)
        result_critical = validator.compute_sum([1000.0], "test3", 'k')
        llm_text_critical = "Total: 2000.0k"  # 100% off
        disc_critical = validator.validate_llm_output(llm_text_critical, {'test3': result_critical})
        self.assertGreater(len(disc_critical), 0)
        self.assertEqual(disc_critical[0].severity, 'critical')


class TestArithmeticComputationLayer(unittest.TestCase):
    """Test computation layer integration"""
    
    def setUp(self):
        self.computation_layer = ArithmeticComputationLayer()
        
        # Create sample data
        self.sample_occ_summary = pd.DataFrame({
            'ONET job title': ['Accountants', 'Engineers', 'Nurses'],
            'Employment': [1562.0, 500.0, 1320.0],
            'Industry title': [20, 15, 18],
            'Hours per week spent on task': [2.5, 3.0, 2.8]
        })
        
        self.sample_matching_df = pd.DataFrame({
            'ONET job title': ['Accountants', 'Accountants', 'Engineers'],
            'Industry title': ['Finance', 'Healthcare', 'Technology'],
            'Employment': [1000.0, 562.0, 500.0],
            'Detailed job tasks': ['Task A', 'Task B', 'Task C']
        })
    
    def test_compute_occupation_summary_arithmetic(self):
        """Test full occupation summary computation"""
        results = self.computation_layer.compute_occupation_summary_arithmetic(
            occ_summary=self.sample_occ_summary,
            matching_df=self.sample_matching_df
        )
        
        # Check all expected keys exist
        self.assertIn('total_employment', results)
        self.assertIn('total_occupations', results)
        self.assertIn('min_employment', results)
        self.assertIn('max_employment', results)
        self.assertIn('avg_employment_per_occupation', results)
        
        # Check values are correct
        self.assertEqual(results['total_employment'], 3382.0)  # 1562 + 500 + 1320
        self.assertEqual(results['total_occupations'], 3)
        self.assertEqual(results['min_employment'], 500.0)
        self.assertEqual(results['max_employment'], 1562.0)
        self.assertAlmostEqual(results['avg_employment_per_occupation'], 1127.33, places=2)
        
        # Check verified objects exist
        self.assertIn('total_employment_verified', results)
        self.assertIsInstance(results['total_employment_verified'], ArithmeticResult)
        
        # Check metadata
        self.assertIn('arithmetic_metadata', results)
        self.assertTrue(results['arithmetic_metadata']['computation_complete'])
    
    def test_validator_stores_computations(self):
        """Test that validator stores all computations"""
        self.computation_layer.compute_occupation_summary_arithmetic(
            occ_summary=self.sample_occ_summary,
            matching_df=self.sample_matching_df
        )
        
        validator = self.computation_layer.get_validator()
        
        # Check computations were stored
        self.assertGreater(len(validator.computed_values), 0)
        
        # Check specific computation exists
        self.assertIn('sum_total_employment_across_all_occupations', validator.computed_values)


class TestEndToEndValidation(unittest.TestCase):
    """Test complete end-to-end validation pipeline"""
    
    def test_correct_llm_output(self):
        """Test pipeline when LLM outputs correct values"""
        # Step 1: Compute ground truth
        computation_layer = ArithmeticComputationLayer()
        
        occ_summary = pd.DataFrame({
            'ONET job title': ['Accountants', 'Engineers'],
            'Employment': [1562.0, 500.0],
            'Industry title': [20, 15],
            'Hours per week spent on task': [2.5, 3.0]
        })
        
        matching_df = pd.DataFrame({
            'ONET job title': ['Accountants', 'Engineers'],
            'Industry title': ['Finance', 'Technology'],
            'Employment': [1562.0, 500.0],
            'Detailed job tasks': ['Task A', 'Task B']
        })
        
        results = computation_layer.compute_occupation_summary_arithmetic(
            occ_summary=occ_summary,
            matching_df=matching_df
        )
        
        # Step 2: Simulate LLM output (correct)
        llm_output = """
        Here are the occupations:
        
        | Occupation  | Employment (k) |
        |-------------|----------------|
        | Accountants | 1,562.00       |
        | Engineers   | 500.00         |
        
        Total Employment: 2,062.00 thousand workers across 2 occupations
        """
        
        # Step 3: Validate
        validator = computation_layer.get_validator()
        expected_values = {k: v for k, v in results.items() if k.endswith('_verified')}
        
        discrepancies = validator.validate_llm_output(
            llm_text=llm_output,
            expected_values=expected_values
        )
        
        # Step 4: Assert no errors
        self.assertEqual(len(discrepancies), 0, "Should have no discrepancies for correct output")
    
    def test_incorrect_llm_output(self):
        """Test pipeline when LLM outputs incorrect values"""
        # Step 1: Compute ground truth
        computation_layer = ArithmeticComputationLayer()
        
        occ_summary = pd.DataFrame({
            'ONET job title': ['Accountants', 'Engineers'],
            'Employment': [1562.0, 500.0],
            'Industry title': [20, 15],
            'Hours per week spent on task': [2.5, 3.0]
        })
        
        matching_df = pd.DataFrame({
            'ONET job title': ['Accountants', 'Engineers'],
            'Industry title': ['Finance', 'Technology'],
            'Employment': [1562.0, 500.0],
            'Detailed job tasks': ['Task A', 'Task B']
        })
        
        results = computation_layer.compute_occupation_summary_arithmetic(
            occ_summary=occ_summary,
            matching_df=matching_df
        )
        
        # Step 2: Simulate LLM output (WRONG - doubled!)
        llm_output = """
        Total Employment: 4,124.00 thousand workers across 2 occupations
        """
        
        # Step 3: Validate
        validator = computation_layer.get_validator()
        expected_values = {k: v for k, v in results.items() if k.endswith('_verified')}
        
        discrepancies = validator.validate_llm_output(
            llm_text=llm_output,
            expected_values=expected_values
        )
        
        # Step 4: Assert error detected
        self.assertGreater(len(discrepancies), 0, "Should detect discrepancy")
        
        # Check discrepancy details
        disc = discrepancies[0]
        self.assertAlmostEqual(disc.computed_value, 2062.0, places=1)
        self.assertAlmostEqual(disc.llm_value, 4124.0, places=1)
        self.assertEqual(disc.severity, 'critical')
    
    def test_real_world_scenario_result2(self):
        """Test with actual user bug report from result2.txt"""
        # Actual data from result2.txt
        computation_layer = ArithmeticComputationLayer()
        
        # Create sample data matching result2
        occ_data = [
            1562.00, 1320.04, 337.00, 291.90, 256.80, 169.20, 127.30, 112.30,
            111.60, 96.30, 94.60, 87.30, 68.90, 45.10, 43.20, 41.70,
            30.20, 29.70, 24.00, 22.20, 22.10, 19.60, 18.70, 14.40,
            13.30, 12.00, 9.90, 9.50, 8.80, 8.70, 8.20, 1.90
        ]
        
        occ_summary = pd.DataFrame({
            'ONET job title': [f'Occupation {i}' for i in range(len(occ_data))],
            'Employment': occ_data,
            'Industry title': [10] * len(occ_data),
            'Hours per week spent on task': [2.0] * len(occ_data)
        })
        
        matching_df = occ_summary.copy()
        
        results = computation_layer.compute_occupation_summary_arithmetic(
            occ_summary=occ_summary,
            matching_df=matching_df
        )
        
        # LLM output from result2.txt (WRONG total)
        llm_output = "Total Employment: 2,824.30 thousand workers across 32 occupations"
        
        # Validate
        validator = computation_layer.get_validator()
        expected_values = {k: v for k, v in results.items() if k.endswith('_verified')}
        
        discrepancies = validator.validate_llm_output(
            llm_text=llm_output,
            expected_values=expected_values
        )
        
        # Should detect the error
        self.assertGreater(len(discrepancies), 0)
        
        # Correct total should be sum of all values
        correct_total = sum(occ_data)
        self.assertAlmostEqual(results['total_employment'], correct_total, places=2)
        self.assertEqual(results['total_employment'], 5018.44)  # Known correct value
        
        # LLM reported wrong value
        disc = discrepancies[0]
        self.assertEqual(disc.llm_value, 2824.30)
        self.assertEqual(disc.severity, 'critical')


class TestArithmeticAccuracy(unittest.TestCase):
    """Test arithmetic accuracy for all operations"""
    
    def test_float_precision(self):
        """Test floating point precision"""
        validator = ArithmeticValidator()
        
        # Test with values that might have floating point issues
        result = validator.compute_sum(
            data=[1562.00, 1320.04],
            description="precision_test",
            unit='k'
        )
        
        self.assertAlmostEqual(result.value, 2882.04, places=2)
    
    def test_large_numbers(self):
        """Test with large employment numbers"""
        validator = ArithmeticValidator()
        
        large_values = [10000.0, 20000.0, 30000.0]
        result = validator.compute_sum(
            data=large_values,
            description="large_numbers",
            unit='k'
        )
        
        self.assertEqual(result.value, 60000.0)
    
    def test_small_percentages(self):
        """Test small percentage calculations"""
        validator = ArithmeticValidator()
        
        result = validator.compute_percentage(
            numerator=1.0,
            denominator=1000.0,
            description="small_percentage"
        )
        
        self.assertAlmostEqual(result.value, 0.1, places=3)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
