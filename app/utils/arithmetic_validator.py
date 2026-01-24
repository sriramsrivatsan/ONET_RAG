# Arithmetic Validation and Verification System
# Ensures 100% accurate calculations with discrepancy detection

import re
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ArithmeticResult:
    """Container for arithmetic computation with metadata"""
    operation: str  # 'sum', 'count', 'average', 'percentage', 'min', 'max'
    value: float
    unit: str  # 'k', 'count', '%', etc.
    description: str
    source_data: Dict[str, Any]  # Original data used for computation
    confidence: str = "computed"  # 'computed', 'verified', 'flagged'
    
    def format(self) -> str:
        """Format for display"""
        if self.unit == 'k':
            return f"{self.value:,.2f}k"
        elif self.unit == '%':
            return f"{self.value:.1f}%"
        elif self.unit == 'count':
            return f"{int(self.value):,}"
        else:
            return f"{self.value:,.2f}"


@dataclass
class ArithmeticDiscrepancy:
    """Container for detected arithmetic discrepancies"""
    operation: str
    computed_value: float  # Ground truth from our calculations
    llm_value: float  # Value LLM reported
    difference: float
    difference_pct: float
    location: str  # Where in LLM output
    severity: str  # 'minor', 'major', 'critical'


class ArithmeticValidator:
    """
    Validates all arithmetic operations and detects discrepancies
    
    This is the GROUND TRUTH layer - all computations done here are authoritative
    """
    
    # Tolerance levels
    TOLERANCE_MINOR = 0.1  # 0.1% difference = minor
    TOLERANCE_MAJOR = 1.0  # 1% difference = major
    TOLERANCE_CRITICAL = 5.0  # 5% difference = critical
    
    def __init__(self):
        self.computed_values: Dict[str, ArithmeticResult] = {}
        self.discrepancies: List[ArithmeticDiscrepancy] = []
        
    def compute_sum(
        self, 
        data: List[float], 
        description: str,
        unit: str = 'k'
    ) -> ArithmeticResult:
        """
        Compute sum with full audit trail
        
        Args:
            data: List of values to sum
            description: Human-readable description
            unit: Unit of measurement
            
        Returns:
            ArithmeticResult with computed sum
        """
        if not data:
            logger.warning(f"Empty data for sum: {description}")
            return ArithmeticResult(
                operation='sum',
                value=0.0,
                unit=unit,
                description=description,
                source_data={'count': 0, 'values': []}
            )
        
        total = sum(data)
        
        result = ArithmeticResult(
            operation='sum',
            value=total,
            unit=unit,
            description=description,
            source_data={
                'count': len(data),
                'values': data,
                'min': min(data),
                'max': max(data),
                'mean': total / len(data) if len(data) > 0 else 0
            }
        )
        
        # Store with key for later validation
        key = f"sum_{description.replace(' ', '_')}"
        self.computed_values[key] = result
        
        logger.info(f"✓ COMPUTED SUM: {description} = {result.format()} (from {len(data)} values)")
        
        return result
    
    def compute_count(
        self,
        data: List[Any],
        description: str
    ) -> ArithmeticResult:
        """Compute count with audit trail"""
        count = len(data) if data else 0
        
        result = ArithmeticResult(
            operation='count',
            value=count,
            unit='count',
            description=description,
            source_data={'items': data if len(data) <= 100 else f"{len(data)} items"}
        )
        
        key = f"count_{description.replace(' ', '_')}"
        self.computed_values[key] = result
        
        logger.info(f"✓ COMPUTED COUNT: {description} = {count:,}")
        
        return result
    
    def compute_average(
        self,
        data: List[float],
        description: str,
        unit: str = ''
    ) -> ArithmeticResult:
        """Compute average with audit trail"""
        if not data:
            logger.warning(f"Empty data for average: {description}")
            return ArithmeticResult(
                operation='average',
                value=0.0,
                unit=unit,
                description=description,
                source_data={'count': 0}
            )
        
        avg = sum(data) / len(data)
        
        result = ArithmeticResult(
            operation='average',
            value=avg,
            unit=unit,
            description=description,
            source_data={
                'count': len(data),
                'sum': sum(data),
                'min': min(data),
                'max': max(data)
            }
        )
        
        key = f"average_{description.replace(' ', '_')}"
        self.computed_values[key] = result
        
        logger.info(f"✓ COMPUTED AVERAGE: {description} = {result.format()}")
        
        return result
    
    def compute_percentage(
        self,
        numerator: float,
        denominator: float,
        description: str
    ) -> ArithmeticResult:
        """Compute percentage with audit trail"""
        if denominator == 0:
            logger.warning(f"Division by zero in percentage: {description}")
            return ArithmeticResult(
                operation='percentage',
                value=0.0,
                unit='%',
                description=description,
                source_data={'numerator': numerator, 'denominator': 0, 'error': 'division_by_zero'}
            )
        
        pct = (numerator / denominator) * 100
        
        result = ArithmeticResult(
            operation='percentage',
            value=pct,
            unit='%',
            description=description,
            source_data={
                'numerator': numerator,
                'denominator': denominator,
                'ratio': numerator / denominator
            }
        )
        
        key = f"percentage_{description.replace(' ', '_')}"
        self.computed_values[key] = result
        
        logger.info(f"✓ COMPUTED PERCENTAGE: {description} = {pct:.1f}%")
        
        return result
    
    def compute_min_max(
        self,
        data: List[float],
        description: str,
        unit: str = 'k'
    ) -> Tuple[ArithmeticResult, ArithmeticResult]:
        """Compute min and max with audit trail"""
        if not data:
            empty_result = ArithmeticResult(
                operation='min',
                value=0.0,
                unit=unit,
                description=description,
                source_data={'count': 0}
            )
            return empty_result, empty_result
        
        min_val = min(data)
        max_val = max(data)
        
        min_result = ArithmeticResult(
            operation='min',
            value=min_val,
            unit=unit,
            description=f"Minimum {description}",
            source_data={'count': len(data), 'max': max_val}
        )
        
        max_result = ArithmeticResult(
            operation='max',
            value=max_val,
            unit=unit,
            description=f"Maximum {description}",
            source_data={'count': len(data), 'min': min_val}
        )
        
        self.computed_values[f"min_{description.replace(' ', '_')}"] = min_result
        self.computed_values[f"max_{description.replace(' ', '_')}"] = max_result
        
        logger.info(f"✓ COMPUTED MIN/MAX: {description} = {min_val:,.2f} to {max_val:,.2f}")
        
        return min_result, max_result
    
    def validate_llm_output(
        self,
        llm_text: str,
        expected_values: Dict[str, ArithmeticResult]
    ) -> List[ArithmeticDiscrepancy]:
        """
        Validate all arithmetic in LLM output against computed ground truth
        
        Args:
            llm_text: Text from LLM
            expected_values: Dictionary of expected values from computations
            
        Returns:
            List of discrepancies found
        """
        discrepancies = []
        
        # Extract all numbers from LLM output with context
        number_patterns = [
            (r'Total Employment:?\s*[\*\*]*([0-9,]+\.?\d*)\s*thousand', 'total_employment'),
            (r'Total:?\s*[\*\*]*([0-9,]+\.?\d*)\s*thousand', 'total'),
            (r'Total:?\s*[\*\*]*([0-9,]+\.?\d*)\s*k', 'total_k'),
            (r'([0-9,]+\.?\d*)\s*thousand\s*workers?', 'employment'),
            (r'([0-9,]+\.?\d*)\s*occupations?', 'occupation_count'),
            (r'([0-9,]+\.?\d*)\s*industries', 'industry_count'),
            (r'([0-9,]+\.?\d*)%', 'percentage'),
        ]
        
        for pattern, value_type in number_patterns:
            matches = re.finditer(pattern, llm_text, re.IGNORECASE)
            for match in matches:
                llm_value_str = match.group(1).replace(',', '')
                try:
                    llm_value = float(llm_value_str)
                    
                    # Find corresponding computed value
                    for key, computed in expected_values.items():
                        # Check if this LLM value corresponds to this computed value
                        if self._values_correspond(llm_value, computed, value_type):
                            # Check for discrepancy
                            diff = abs(llm_value - computed.value)
                            diff_pct = (diff / computed.value * 100) if computed.value != 0 else 0
                            
                            if diff_pct > self.TOLERANCE_MINOR:
                                # Determine severity
                                if diff_pct > self.TOLERANCE_CRITICAL:
                                    severity = 'critical'
                                elif diff_pct > self.TOLERANCE_MAJOR:
                                    severity = 'major'
                                else:
                                    severity = 'minor'
                                
                                discrepancy = ArithmeticDiscrepancy(
                                    operation=computed.operation,
                                    computed_value=computed.value,
                                    llm_value=llm_value,
                                    difference=diff,
                                    difference_pct=diff_pct,
                                    location=match.group(0),
                                    severity=severity
                                )
                                
                                discrepancies.append(discrepancy)
                                
                                logger.warning(
                                    f"⚠️ ARITHMETIC DISCREPANCY ({severity.upper()}): "
                                    f"LLM said {llm_value:,.2f} but computed value is {computed.value:,.2f} "
                                    f"(difference: {diff_pct:.1f}%)"
                                )
                
                except (ValueError, ZeroDivisionError):
                    continue
        
        self.discrepancies = discrepancies
        return discrepancies
    
    def _values_correspond(
        self,
        llm_value: float,
        computed: ArithmeticResult,
        value_type: str
    ) -> bool:
        """Check if LLM value corresponds to computed value"""
        # This is a heuristic - in production, you'd have more sophisticated matching
        
        # If values are close (within 0.01%), they likely correspond
        if abs(llm_value - computed.value) / computed.value < 0.0001:
            return True
        
        # If value_type matches operation and values are in same ballpark
        if value_type in ['total_employment', 'total', 'employment'] and computed.operation == 'sum':
            return abs(llm_value - computed.value) / computed.value < 0.5
        
        if 'count' in value_type and computed.operation == 'count':
            return abs(llm_value - computed.value) / computed.value < 0.5
        
        return False
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validations"""
        return {
            'total_computations': len(self.computed_values),
            'total_discrepancies': len(self.discrepancies),
            'discrepancies_by_severity': {
                'minor': len([d for d in self.discrepancies if d.severity == 'minor']),
                'major': len([d for d in self.discrepancies if d.severity == 'major']),
                'critical': len([d for d in self.discrepancies if d.severity == 'critical'])
            },
            'validation_status': 'PASSED' if len(self.discrepancies) == 0 else 'FAILED'
        }
    
    def format_discrepancy_report(self) -> str:
        """Format discrepancies for user display"""
        if not self.discrepancies:
            return ""
        
        report = "\n\n" + "="*80 + "\n"
        report += "⚠️ ARITHMETIC VALIDATION ALERT\n"
        report += "="*80 + "\n\n"
        report += "Discrepancies detected between LLM output and verified calculations:\n\n"
        
        for i, disc in enumerate(self.discrepancies, 1):
            report += f"{i}. {disc.operation.upper()} ({disc.severity.upper()}):\n"
            report += f"   ✓ Computed (Verified): {disc.computed_value:,.2f}\n"
            report += f"   ✗ LLM Reported: {disc.llm_value:,.2f}\n"
            report += f"   Δ Difference: {disc.difference:,.2f} ({disc.difference_pct:.1f}%)\n"
            report += f"   Location: \"{disc.location}\"\n\n"
        
        report += "="*80 + "\n"
        report += "✓ USE THE VERIFIED VALUES ABOVE - they are mathematically correct.\n"
        report += "📧 Please report this query to help us improve the system.\n"
        report += "="*80 + "\n"
        
        return report
