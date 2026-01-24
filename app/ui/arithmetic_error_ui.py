# User-Facing Arithmetic Error Reporting UI Component
# Displays discrepancies and provides error reporting mechanism

import streamlit as st
from typing import List, Dict, Any
from datetime import datetime
import json
from app.utils.arithmetic_validator import ArithmeticDiscrepancy

class ArithmeticErrorReporter:
    """
    Handles user-facing display of arithmetic discrepancies and error reporting
    """
    
    @staticmethod
    def display_discrepancy_alert(
        discrepancies: List[ArithmeticDiscrepancy],
        query: str,
        session_id: str
    ) -> None:
        """
        Display arithmetic discrepancies to user with clear reporting option
        
        Args:
            discrepancies: List of detected discrepancies
            query: Original user query
            session_id: Session identifier for error tracking
        """
        if not discrepancies:
            return
        
        # Severity-based styling
        severity_colors = {
            'minor': 'warning',
            'major': 'error',
            'critical': 'error'
        }
        
        severity_icons = {
            'minor': '⚠️',
            'major': '🚨',
            'critical': '🔴'
        }
        
        # Group by severity
        critical = [d for d in discrepancies if d.severity == 'critical']
        major = [d for d in discrepancies if d.severity == 'major']
        minor = [d for d in discrepancies if d.severity == 'minor']
        
        # Display alert box
        st.markdown("---")
        
        if critical or major:
            st.error("### ⚠️ ARITHMETIC VALIDATION ALERT")
        else:
            st.warning("### ⚠️ Minor Arithmetic Discrepancy Detected")
        
        st.markdown("""
        **We detected differences between our verified calculations and the displayed values.**
        
        ✅ **Use the VERIFIED VALUES below** - they are mathematically correct and independently computed from the source data.
        """)
        
        # Display each discrepancy with clear comparison
        for i, disc in enumerate(discrepancies, 1):
            severity_icon = severity_icons[disc.severity]
            
            with st.expander(f"{severity_icon} Discrepancy #{i}: {disc.operation.title()} ({disc.severity.upper()})", expanded=(disc.severity in ['critical', 'major'])):
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    st.markdown("##### ✓ VERIFIED VALUE")
                    st.markdown(f"### **{disc.computed_value:,.2f}**")
                    st.caption("This is the correct value from our calculations")
                
                with col2:
                    st.markdown("##### ✗ Displayed Value")
                    st.markdown(f"### ~~{disc.llm_value:,.2f}~~")
                    st.caption("This value may be inaccurate")
                
                with col3:
                    st.markdown("##### Δ Difference")
                    st.markdown(f"### {disc.difference:,.2f}")
                    st.caption(f"({disc.difference_pct:.1f}% difference)")
                
                st.markdown(f"**Location in response:** `{disc.location}`")
        
        st.markdown("---")
        
        # Verified values summary
        st.success("### ✓ VERIFIED VALUES (Use These)")
        
        summary_data = []
        for disc in discrepancies:
            summary_data.append({
                'Metric': disc.operation.title(),
                'Verified Value': f"{disc.computed_value:,.2f}",
                'Confidence': '100%'
            })
        
        st.table(summary_data)
        
        # Error reporting section
        st.markdown("---")
        st.markdown("### 📧 Report This Issue")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            **Help us improve!** Reporting this query helps us understand and fix arithmetic accuracy issues.
            
            Your report will include:
            - The query you asked
            - The discrepancies detected
            - Timestamp and session information
            - No personal information
            """)
        
        with col2:
            if st.button("📧 Report Error", type="primary", use_container_width=True):
                ArithmeticErrorReporter.submit_error_report(
                    query=query,
                    discrepancies=discrepancies,
                    session_id=session_id
                )
                st.success("✅ Report submitted! Thank you for helping us improve.")
        
        st.markdown("---")
    
    @staticmethod
    def submit_error_report(
        query: str,
        discrepancies: List[ArithmeticDiscrepancy],
        session_id: str
    ) -> None:
        """
        Submit error report for analysis
        
        In production, this would send to:
        - Error tracking system (Sentry, Rollbar, etc.)
        - Database for analysis
        - Email notification to dev team
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'query': query,
            'discrepancies': [
                {
                    'operation': d.operation,
                    'computed_value': d.computed_value,
                    'llm_value': d.llm_value,
                    'difference': d.difference,
                    'difference_pct': d.difference_pct,
                    'severity': d.severity,
                    'location': d.location
                }
                for d in discrepancies
            ],
            'total_discrepancies': len(discrepancies),
            'severity_breakdown': {
                'critical': len([d for d in discrepancies if d.severity == 'critical']),
                'major': len([d for d in discrepancies if d.severity == 'major']),
                'minor': len([d for d in discrepancies if d.severity == 'minor'])
            }
        }
        
        # Log to file
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"ARITHMETIC ERROR REPORT: {json.dumps(report, indent=2)}")
        
        # In production, also:
        # - Send to error tracking service
        # - Store in database
        # - Send email notification
        # - Trigger alert
        
        # For now, save to file
        try:
            import os
            error_dir = 'data/error_reports'
            os.makedirs(error_dir, exist_ok=True)
            
            filename = f"{error_dir}/arithmetic_error_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Error report saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save error report: {e}")
    
    @staticmethod
    def display_verification_badge(
        has_discrepancies: bool = False
    ) -> None:
        """Display verification status badge"""
        if has_discrepancies:
            st.warning("⚠️ **Arithmetic Verification:** Discrepancies detected (see details below)")
        else:
            st.success("✓ **Arithmetic Verification:** All values independently verified")
    
    @staticmethod
    def display_computation_details(
        computational_results: Dict[str, Any],
        show_details: bool = False
    ) -> None:
        """Display computation details for transparency"""
        if not show_details:
            with st.expander("🔍 View Computation Details", expanded=False):
                ArithmeticErrorReporter._render_computation_details(computational_results)
        else:
            ArithmeticErrorReporter._render_computation_details(computational_results)
    
    @staticmethod
    def _render_computation_details(computational_results: Dict[str, Any]) -> None:
        """Render computation details"""
        st.markdown("### 📊 Verified Computations")
        
        # Display all verified values
        verified_values = []
        for key, value in computational_results.items():
            if key.endswith('_verified'):
                metric_name = key.replace('_verified', '').replace('_', ' ').title()
                if hasattr(value, 'format'):
                    verified_values.append({
                        'Metric': metric_name,
                        'Value': value.format(),
                        'Operation': value.operation.title(),
                        'Status': '✓ Verified'
                    })
        
        if verified_values:
            st.table(verified_values)
        
        # Display metadata
        if 'arithmetic_metadata' in computational_results:
            metadata = computational_results['arithmetic_metadata']
            st.markdown("#### Computation Metadata")
            
            cols = st.columns(3)
            with cols[0]:
                st.metric("Total Computations", metadata.get('total_computations', 'N/A'))
            with cols[1]:
                st.metric("Source Rows", metadata.get('source_rows', 'N/A'))
            with cols[2]:
                st.metric("Verification Status", "✓ Complete" if metadata.get('computation_complete') else "Pending")


# INTEGRATION EXAMPLE:
"""
# In client.py, after getting LLM response:

# Validate arithmetic
discrepancies = validator.validate_llm_output(
    llm_text=answer,
    expected_values=retrieval_results['computational_results']
)

# Display verification badge
ArithmeticErrorReporter.display_verification_badge(
    has_discrepancies=len(discrepancies) > 0
)

# Display main response
st.markdown(answer)

# Display discrepancies if any
if discrepancies:
    ArithmeticErrorReporter.display_discrepancy_alert(
        discrepancies=discrepancies,
        query=query,
        session_id=st.session_state.get('session_id', 'unknown')
    )

# Optionally show computation details
ArithmeticErrorReporter.display_computation_details(
    computational_results=retrieval_results['computational_results'],
    show_details=False
)
"""
