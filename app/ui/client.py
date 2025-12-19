"""
Client View UI for analyst queries
"""
import streamlit as st
import pandas as pd
from io import StringIO
from typing import Optional

from app.llm.response_builder import QueryProcessor, ResponseBuilder
from app.rag.retriever import HybridRetriever
from app.utils.logging import logger
from app.utils.config import config


class ClientView:
    """Client view for labor market analysts to query the system"""
    
    def __init__(self):
        self.query_processor: Optional[QueryProcessor] = None
    
    def render(self):
        """Render the client view"""
        
        st.title("💼 Labor Market Intelligence - Analyst Interface")
        st.markdown("Ask questions about occupations, industries, tasks, and labor market trends")
        st.markdown("---")
        
        # Check if system is ready
        if not self._check_system_ready():
            st.warning("⚠️ System not initialized. Please go to Admin panel to upload and process data.")
            return
        
        # Initialize query processor if needed
        if self.query_processor is None:
            self._initialize_query_processor()
        
        # Query interface
        self._render_query_interface()
        
        st.markdown("---")
        
        # Quick insights
        self._render_quick_insights()
    
    def _check_system_ready(self) -> bool:
        """Check if system is ready for queries"""
        return (
            st.session_state.get('vector_store_initialized', False) and
            st.session_state.get('dataframe') is not None and
            st.session_state.get('aggregator') is not None
        )
    
    def _initialize_query_processor(self):
        """Initialize the query processor"""
        try:
            api_key = config.get_openai_api_key()
            if not api_key:
                st.error("OpenAI API key not configured")
                return
            
            response_builder = ResponseBuilder(api_key)
            
            retriever = HybridRetriever(
                vector_store=st.session_state.vector_store,
                dataframe=st.session_state.dataframe,
                aggregator=st.session_state.aggregator
            )
            
            self.query_processor = QueryProcessor(
                response_builder=response_builder,
                retriever=retriever,
                dataframe=st.session_state.dataframe
            )
            
            logger.info("Query processor initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize query processor: {str(e)}", show_ui=True)
    
    def _render_query_interface(self):
        """Render the main query interface"""
        
        st.subheader("🔍 Query Interface")
        
        # Sample queries
        with st.expander("💡 Sample Queries", expanded=False):
            st.markdown("""
            **Digital Document Creation:**
            - What jobs likely require creating digital documents?
            - What's the total employment of workers that create digital documents?
            - What industries are rich in digital document users?
            
            **AI Agent Impact:**
            - What jobs could benefit from a customer service AI agent?
            - How much time could an AI agent save per week?
            - What's the dollar savings this agentic solution could achieve?
            
            **General Labor Market:**
            - Which industries have the highest employment?
            - What occupations require the most diverse skill sets?
            - Compare task requirements across Healthcare and Technology industries
            """)
        
        # Query input
        query = st.text_area(
            "Enter your question:",
            height=100,
            placeholder="Example: What jobs likely require creating digital documents as part of the work?",
            key="main_query"
        )
        
        # Query settings
        col1, col2 = st.columns([3, 1])
        
        with col1:
            k_results = st.slider(
                "Number of documents to retrieve",
                min_value=5,
                max_value=50,
                value=10,
                help="More documents = more comprehensive but slower"
            )
        
        with col2:
            show_debug = st.checkbox("Show Debug Info", value=False)
        
        # Query button
        if st.button("🚀 Analyze Query", type="primary", use_container_width=True):
            if not query.strip():
                st.warning("Please enter a question")
                return
            
            self._process_and_display_query(query, k_results, show_debug)
    
    def _process_and_display_query(self, query: str, k_results: int, show_debug: bool):
        """Process query and display results"""
        
        with st.spinner("🔄 Processing your query..."):
            try:
                # Process query
                response = self.query_processor.process_query(
                    query=query,
                    k_results=k_results
                )
                
                # Display answer
                st.markdown("### 📊 Analysis Results")
                st.markdown(response['answer'])
                
                # Display CSV if available
                if response.get('csv_data') is not None:
                    st.markdown("---")
                    st.subheader("📥 Exportable Data")
                    
                    csv_df = response['csv_data']
                    st.dataframe(csv_df)
                    
                    # Download button
                    csv_buffer = StringIO()
                    csv_df.to_csv(csv_buffer, index=False)
                    csv_str = csv_buffer.getvalue()
                    
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_str,
                        file_name="labor_market_analysis.csv",
                        mime="text/csv"
                    )
                
                # Show debug info if requested
                if show_debug:
                    self._render_debug_info(response)
                
                # Store in history
                if 'query_history' not in st.session_state:
                    st.session_state.query_history = []
                
                st.session_state.query_history.append({
                    'query': query,
                    'timestamp': pd.Timestamp.now(),
                    'response': response
                })
                
            except Exception as e:
                logger.error(f"Query processing failed: {str(e)}", show_ui=True)
                st.error(f"Failed to process query: {str(e)}")
    
    def _render_debug_info(self, response: dict):
        """Render debug information"""
        
        with st.expander("🔍 Debug Information", expanded=False):
            routing_info = response.get('routing_info', {})
            metadata = response.get('metadata', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Query Routing**")
                st.json(routing_info)
            
            with col2:
                st.write("**Retrieval Metadata**")
                st.json(metadata)
            
            # Semantic results
            retrieval_results = response.get('retrieval_results', {})
            semantic_results = retrieval_results.get('semantic_results', [])
            
            if semantic_results:
                st.write("**Top Semantic Results**")
                for i, result in enumerate(semantic_results[:5], 1):
                    with st.container():
                        st.write(f"**Result {i}** (Score: {result.get('score', 0):.3f})")
                        st.write(result.get('text', '')[:300] + "...")
                        st.caption(f"Metadata: {result.get('metadata', {})}")
    
    def _render_quick_insights(self):
        """Render quick insights panel"""
        
        st.subheader("⚡ Quick Insights")
        
        aggregations = st.session_state.get('aggregations', {})
        
        if not aggregations:
            st.info("No aggregations available")
            return
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            occ_stats = aggregations.get('occupation_stats', {})
            total_occupations = occ_stats.get('total_occupations', 0)
            st.metric("Total Occupations", f"{total_occupations:,}")
        
        with col2:
            ind_stats = aggregations.get('industry_stats', {})
            total_industries = ind_stats.get('total_industries', 0)
            st.metric("Total Industries", f"{total_industries:,}")
        
        with col3:
            emp_stats = aggregations.get('employment_stats', {})
            total_employment = emp_stats.get('total_employment', 0)
            st.metric("Total Employment", f"{total_employment:,.0f}")
        
        with col4:
            task_stats = aggregations.get('task_stats', {})
            unique_tasks = task_stats.get('total_unique_tasks', 0)
            st.metric("Unique Tasks", f"{unique_tasks:,}")
        
        # Top industries and occupations
        with st.expander("📈 Top Industries & Occupations", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write("**Top 10 Industries by Employment**")
                top_industries = emp_stats.get('top_10_industries_by_employment', {})
                if top_industries:
                    ind_df = pd.DataFrame([
                        {'Industry': k, 'Employment': v}
                        for k, v in list(top_industries.items())[:10]
                    ])
                    st.dataframe(ind_df, use_container_width=True)
            
            with col_b:
                st.write("**Top 10 Occupations by Employment**")
                top_occs = emp_stats.get('employment_by_occupation', {})
                if top_occs:
                    occ_df = pd.DataFrame([
                        {'Occupation': k, 'Employment': v}
                        for k, v in list(top_occs.items())[:10]
                    ])
                    st.dataframe(occ_df, use_container_width=True)
        
        # Query history
        if st.session_state.get('query_history'):
            with st.expander("📜 Query History", expanded=False):
                history = st.session_state.query_history[-10:]  # Last 10 queries
                
                for i, item in enumerate(reversed(history), 1):
                    st.write(f"**{i}. {item['query'][:100]}...**")
                    st.caption(f"Time: {item['timestamp']}")
                    st.markdown("---")
