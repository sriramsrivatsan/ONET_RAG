"""
Client View UI for analyst queries
"""
import streamlit as st
import pandas as pd
from io import StringIO
from typing import Optional, Dict, Any

from app.llm.response_builder import QueryProcessor, ResponseBuilder
from app.rag.retriever import HybridRetriever
from app.ui.system_status import SystemStatusSidebar
from app.utils.logging import logger
from app.utils.config import config


class ClientView:
    """Client view for labor market analysts to query the system"""
    
    def __init__(self):
        self.query_processor: Optional[QueryProcessor] = None
    
    def render(self):
        """Render the client view"""
        
        # Render system status sidebar
        SystemStatusSidebar.render(view_type='client')
        
        st.title("📊 Analyst Interface - Labor Market Intelligence")
        st.markdown("Ask questions about occupations, industries, tasks, and labor market trends")
        st.markdown("---")
        
        # Check if system is ready
        if not self._check_system_ready():
            st.warning("⚠️ System not initialized. Please go to Admin panel to upload and process data.")
            st.info("💡 Click the **Back to Home** button in the sidebar, then select **Admin View** to get started.")
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
        
        # Show success message if New Query was just clicked
        if st.session_state.get('show_new_query_message', False):
            st.success("✅ Ready for new query! Enter your question above.")
            st.session_state.show_new_query_message = False  # Clear flag
        
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
        
        # Query input - Use versioned key for proper reset behavior
        # Each time we reset, increment version to create a new widget
        if 'query_widget_version' not in st.session_state:
            st.session_state.query_widget_version = 0
        
        query = st.text_area(
            "Enter your question:",
            height=100,
            placeholder="Example: What jobs likely require creating digital documents as part of the work?",
            key=f"main_query_v{st.session_state.query_widget_version}"  # Versioned key
        )
        
        # Query settings - Always retrieve all documents
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Get total document count
            total_docs = st.session_state.get('document_count', 1000)
            k_results = total_docs  # Retrieve all documents
            
            st.info(f"ℹ️ Retrieving all {total_docs:,} documents for comprehensive analysis")
        
        with col2:
            show_debug = st.checkbox("Show Debug Info", value=False)
        
        # Query button
        if st.button("🚀 Analyze Query", type="primary", width="stretch"):
            if not query.strip():
                st.warning("Please enter a question")
                return
            
            # No need to store - widget with key="main_query" automatically updates session state!
            self._process_and_display_query(query, k_results, show_debug)
        
        # Render post-query buttons OUTSIDE the button callback
        # This ensures they render on every page load if show_post_query_buttons is True
        if st.session_state.get('show_post_query_buttons', False):
            st.markdown("---")
            self._render_post_query_buttons()
    
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
                
                # Store results for follow-up functionality
                st.session_state.last_query = query
                st.session_state.last_query_results = response
                st.session_state.show_post_query_buttons = True
                
                # Store filtered dataset if available
                logger.info("Attempting to store filtered dataset for follow-up queries", show_ui=False)
                
                retrieval_results = response.get('retrieval_results', {})
                logger.info(f"Retrieval results keys: {list(retrieval_results.keys())}", show_ui=False)
                
                if retrieval_results.get('filtered_dataframe') is not None:
                    filtered_df = retrieval_results['filtered_dataframe']
                    logger.info(f"Found filtered_dataframe: type={type(filtered_df)}, empty={filtered_df.empty if hasattr(filtered_df, 'empty') else 'N/A'}, shape={filtered_df.shape if hasattr(filtered_df, 'shape') else 'N/A'}", show_ui=False)
                    
                    if hasattr(filtered_df, 'empty') and not filtered_df.empty:
                        # Reset index for follow-up query compatibility
                        st.session_state.filtered_dataset = filtered_df.reset_index(drop=True)
                        logger.info(f"✅ Stored filtered dataset with {len(filtered_df)} rows for follow-up queries", show_ui=True)
                    else:
                        logger.warning("Filtered dataframe is empty or not a DataFrame", show_ui=True)
                        st.session_state.filtered_dataset = None
                elif retrieval_results.get('semantic_results'):
                    logger.info("No filtered_dataframe, trying to extract from semantic_results", show_ui=False)
                    # Extract row indices from semantic results and filter dataframe
                    semantic_results = retrieval_results['semantic_results']
                    row_indices = [
                        r['metadata'].get('row_index')
                        for r in semantic_results
                        if 'row_index' in r.get('metadata', {})
                    ]
                    logger.info(f"Found {len(row_indices)} row indices in semantic_results", show_ui=False)
                    
                    if row_indices and st.session_state.dataframe is not None:
                        # CRITICAL FIX: Reset index to avoid index mismatch in follow-up queries
                        st.session_state.filtered_dataset = st.session_state.dataframe.loc[row_indices].reset_index(drop=True)
                        logger.info(f"✅ Created filtered dataset from {len(row_indices)} row indices", show_ui=True)
                    else:
                        logger.warning("❌ No row indices found in semantic results or dataframe not available - follow-up queries won't work!", show_ui=True)
                        st.session_state.filtered_dataset = None
                else:
                    logger.warning("❌ No filtered dataframe or semantic results available - follow-up queries won't work!", show_ui=True)
                    st.session_state.filtered_dataset = None
                
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
                    st.dataframe(ind_df, width="stretch")
            
            with col_b:
                st.write("**Top 10 Occupations by Employment**")
                top_occs = emp_stats.get('employment_by_occupation', {})
                if top_occs:
                    occ_df = pd.DataFrame([
                        {'Occupation': k, 'Employment': v}
                        for k, v in list(top_occs.items())[:10]
                    ])
                    st.dataframe(occ_df, width="stretch")
        
        # Query history
        if st.session_state.get('query_history'):
            with st.expander("📜 Query History", expanded=False):
                history = st.session_state.query_history[-10:]  # Last 10 queries
                
                for i, item in enumerate(reversed(history), 1):
                    st.write(f"**{i}. {item['query'][:100]}...**")
                    st.caption(f"Time: {item['timestamp']}")
                    st.markdown("---")
    
    def _render_post_query_buttons(self):
        """Render post-query action buttons"""
        
        # Double-check: Only show if flag is set AND we have valid query results
        if not st.session_state.get('show_post_query_buttons', False):
            return
        
        if not st.session_state.get('last_query_results'):
            # No valid results - hide buttons
            st.session_state.show_post_query_buttons = False
            return
        
        st.subheader("🎯 Next Actions")
        st.markdown("Choose one of the following options to continue your analysis:")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 Follow-up Query", type="secondary", use_container_width=True, key="btn_followup"):
                st.session_state.show_followup_interface = True
                st.rerun()
        
        with col2:
            if st.button("🌐 Enhanced RAG", type="secondary", use_container_width=True, key="btn_enhanced"):
                # Set flag to trigger Enhanced RAG processing
                st.session_state.run_enhanced_rag = True
                st.rerun()
        
        with col3:
            # Direct download button - immediately downloads filtered dataset as CSV
            if st.session_state.filtered_dataset is not None and not st.session_state.filtered_dataset.empty:
                csv_buffer = StringIO()
                st.session_state.filtered_dataset.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                filename = f"labor_market_results_{timestamp}.csv"
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    type="secondary",
                    use_container_width=True,
                    key="btn_download_direct"
                )
            elif st.session_state.last_query_results and st.session_state.last_query_results.get('csv_data') is not None:
                # Fallback to CSV data from results
                csv_buffer = StringIO()
                st.session_state.last_query_results['csv_data'].to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                filename = f"labor_market_results_{timestamp}.csv"
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    type="secondary",
                    use_container_width=True,
                    key="btn_download_direct"
                )
            else:
                # No data available - show disabled button
                st.button(
                    "📥 Download CSV",
                    type="secondary",
                    use_container_width=True,
                    disabled=True,
                    key="btn_download_disabled",
                    help="No data available to download"
                )
        
        with col4:
            if st.button("🆕 New Query", type="primary", use_container_width=True, key="btn_new"):
                self._start_new_query()
        
        # Process Enhanced RAG if flag is set (happens OUTSIDE button callback for persistence)
        if st.session_state.get('run_enhanced_rag', False):
            self._execute_enhanced_rag()
            st.session_state.run_enhanced_rag = False  # Clear flag after processing
        
        # Display persistent sections after buttons (these persist across reruns)
        
        # Show follow-up query interface if activated
        if st.session_state.get('show_followup_interface', False):
            self._show_followup_query_interface()
        
        # Show enhanced RAG results if available (persists across reruns)
        if st.session_state.get('enhanced_rag_data'):
            self._display_enhanced_rag_section()
    
    def _execute_enhanced_rag(self):
        """Execute Enhanced RAG: re-query + external intelligence"""
        
        with st.spinner("🔄 Re-running query with external intelligence..."):
            try:
                original_query = st.session_state.last_query
                if not original_query:
                    st.warning("⚠️ No previous query to enhance. Please run a query first.")
                    return
                
                st.info(f"📝 Re-querying: '{original_query}'")
                
                # Step 1: Re-run the original query through RAG
                k_results = st.session_state.get('document_count', 1000)
                try:
                    response = self.query_processor.process_query(
                        query=original_query,
                        k_results=k_results
                    )
                    st.success("✅ Step 1/2: Query re-processed successfully")
                except Exception as e:
                    st.error(f"❌ Re-query failed: {str(e)}")
                    raise
                
                # Step 2: Generate external intelligence about the topic
                api_key = config.get_openai_api_key()
                response_builder = ResponseBuilder(api_key)
                
                enhancement_prompt = f"""
                Query: {original_query}
                
                Based on the query above, provide external market intelligence and context:
                
                1. Recent industry trends and developments (last 2-3 years)
                2. External statistics or data points from reliable sources
                3. Best practices and insights from industry reports
                4. Emerging patterns and future outlook (next 3-5 years)
                5. Key skills or competencies becoming more important
                
                Format as 5 concise bullet points. Focus on information that complements 
                internal data analysis for labor market planning.
                """
                
                try:
                    external_intelligence = response_builder.generate_enhanced_response(
                        query=enhancement_prompt,
                        context="",
                        use_web_search=True
                    )
                    st.success("✅ Step 2/2: External intelligence generated")
                except Exception as e:
                    st.error(f"❌ External intelligence generation failed: {str(e)}")
                    raise
                
                # Store both in session state for persistent display
                st.session_state.enhanced_rag_data = {
                    'query_result': response['answer'],
                    'external_intelligence': external_intelligence,
                    'csv_data': response.get('csv_data')
                }
                
                st.success("🎉 Enhanced RAG completed! Scroll down to see results.")
                logger.info("Enhanced RAG completed with re-query and external intelligence")
                
            except Exception as e:
                logger.error(f"Enhanced RAG failed: {str(e)}", show_ui=True)
                st.error(f"❌ Enhanced RAG failed: {str(e)}")
                st.info("💡 Please check your API key configuration and try again.")
    
    def _show_followup_query_interface(self):
        """Show interface for follow-up query on filtered dataset"""
        
        st.markdown("---")
        st.subheader("🔄 Follow-up Query")
        st.info("💡 This query will only search within the results from your previous query.")
        
        if st.session_state.filtered_dataset is None:
            st.error("⚠️ No filtered dataset available from previous query.")
            st.info("**Why this happened:** The previous query didn't produce a filterable dataset for follow-up queries. This usually happens when the query returns aggregated summaries instead of raw data.")
            st.info("**Solution:** Try a different type of query first (e.g., 'What tasks involve creating documents?'), then use follow-up queries to refine the results.")
            
            # Debug info
            if st.session_state.get('last_query_results'):
                with st.expander("🔍 Debug Info - Technical Details"):
                    st.write("**Last Query:**", st.session_state.get('last_query', 'N/A'))
                    st.write("**Response Keys:**", list(st.session_state.last_query_results.keys()))
                    if 'retrieval_results' in st.session_state.last_query_results:
                        retrieval = st.session_state.last_query_results['retrieval_results']
                        st.write("**Retrieval Results Keys:**", list(retrieval.keys()))
                        if 'filtered_dataframe' in retrieval:
                            fd = retrieval['filtered_dataframe']
                            st.write("**Filtered Dataframe:**")
                            st.write(f"  - Type: {type(fd)}")
                            st.write(f"  - Is None: {fd is None}")
                            if fd is not None:
                                st.write(f"  - Has 'empty' attr: {hasattr(fd, 'empty')}")
                                if hasattr(fd, 'empty'):
                                    st.write(f"  - Is empty: {fd.empty}")
                                    st.write(f"  - Shape: {fd.shape}")
                        else:
                            st.write("❌ No 'filtered_dataframe' key in retrieval_results")
                        
                        if 'semantic_results' in retrieval:
                            sem_results = retrieval['semantic_results']
                            st.write(f"**Semantic Results:** {len(sem_results)} results")
                            if len(sem_results) > 0:
                                st.write(f"  - First result metadata keys: {list(sem_results[0].get('metadata', {}).keys())}")
                                st.write(f"  - Has row_index: {'row_index' in sem_results[0].get('metadata', {})}")
                    else:
                        st.write("❌ No 'retrieval_results' in response")
            
            return
        
        if st.session_state.filtered_dataset.empty:
            st.warning("⚠️ Filtered dataset is empty.")
            return
        
        dataset_size = len(st.session_state.filtered_dataset)
        st.success(f"✓ Querying filtered dataset of {dataset_size:,} records")
        
        followup_query = st.text_area(
            "Enter your follow-up question:",
            height=80,
            placeholder="Ask a question about the previous results...",
            key="followup_query_input"
        )
        
        col_a, col_b = st.columns([3, 1])
        
        with col_a:
            if st.button("🚀 Run Follow-up Query", type="primary", key="btn_run_followup", use_container_width=True):
                if not followup_query.strip():
                    st.warning("Please enter a follow-up question")
                    return
                
                self._process_followup_query(followup_query)
        
        with col_b:
            if st.button("✖️ Close", key="close_followup", use_container_width=True):
                st.session_state.show_followup_interface = False
                st.rerun()
    
    def _process_followup_query(self, query: str):
        """Process follow-up query on filtered dataset"""
        
        with st.spinner("🔄 Processing follow-up query on filtered dataset..."):
            try:
                # Get the filtered dataset
                filtered_df = st.session_state.filtered_dataset
                
                if filtered_df is None or filtered_df.empty:
                    st.error("❌ No filtered dataset available. Please run an initial query first.")
                    return
                
                # Ensure index is reset
                filtered_df = filtered_df.reset_index(drop=True)
                
                st.info(f"📊 Analyzing {len(filtered_df):,} filtered records (from previous query)")
                
                # CRITICAL FIX: For follow-up queries, we CANNOT use semantic search
                # because the vector store has embeddings for the FULL dataset
                # We must work ONLY with the filtered dataframe using pattern matching/computational
                
                # Analyze the query to determine what's needed
                query_lower = query.lower()
                
                # Simple computational queries - no need for complex processing
                if any(word in query_lower for word in ['total', 'sum', 'count', 'average', 'how many']):
                    # Direct aggregation on filtered data
                    result = self._simple_aggregation_on_filtered_data(filtered_df, query)
                    if result:
                        st.markdown("### 📊 Follow-up Analysis Results")
                        st.markdown(result['answer'])
                        
                        if result.get('csv_data') is not None:
                            self._display_csv_download(result['csv_data'], "followup")
                        
                        st.success("✅ Follow-up query completed!")
                        return
                
                # For more complex queries, use pattern matching on filtered data
                # Create a minimal retriever that works WITHOUT vector search
                retriever = HybridRetriever(
                    vector_store=st.session_state.vector_store,  # Don't use for search
                    dataframe=filtered_df,  # Work on filtered data only
                    aggregator=st.session_state.aggregator
                )
                
                # Explicitly set df to filtered data
                retriever.df = filtered_df
                
                # Create temporary processor
                api_key = config.get_openai_api_key()
                response_builder = ResponseBuilder(api_key)
                temp_processor = QueryProcessor(
                    response_builder=response_builder,
                    retriever=retriever,
                    dataframe=filtered_df
                )
                
                # Process with k limited to filtered dataset size
                k_results = min(len(filtered_df), 50)
                
                logger.info(
                    f"Follow-up query on {len(filtered_df)} records (k={k_results})",
                    show_ui=False
                )
                
                response = temp_processor.process_query(
                    query=query,
                    k_results=k_results
                )
                
                # Validate response
                if not response or 'answer' not in response:
                    st.error("❌ Query returned no results. Try rephrasing or run a new initial query.")
                    return
                
                # Display results
                st.markdown("### 📊 Follow-up Analysis Results")
                st.markdown(response['answer'])
                
                # Show query details in expander
                with st.expander("🔍 Query Details"):
                    st.write(f"**Query:** {query}")
                    st.write(f"**Filtered Records:** {len(filtered_df):,}")
                    st.write(f"**Results Analyzed:** {k_results}")
                
                # Display CSV if available
                if response.get('csv_data') is not None:
                    try:
                        csv_df = response['csv_data']
                        if len(csv_df) > 0:
                            self._display_csv_download(csv_df, "followup")
                        else:
                            st.info("💡 No tabular data generated for this query")
                    except Exception as e:
                        logger.warning(f"Could not display CSV: {e}", show_ui=False)
                
                # Update state
                st.session_state.last_query = f"[Follow-up] {query}"
                st.session_state.last_query_results = response
                
                # Update filtered dataset if response refined it further
                if response.get('retrieval_results', {}).get('filtered_dataframe') is not None:
                    new_filtered = response['retrieval_results']['filtered_dataframe'].reset_index(drop=True)
                    st.session_state.filtered_dataset = new_filtered
                    logger.info(f"Refined filter to {len(new_filtered)} records", show_ui=False)
                
                st.success("✅ Follow-up query completed!")
                
            except Exception as e:
                logger.error(f"Follow-up query failed: {str(e)}", show_ui=True)
                st.error(f"❌ Follow-up query failed: {str(e)}")
                st.info("💡 Try simplifying your question or click 'New Query' to start fresh")
                
                with st.expander("🔍 Error Details"):
                    st.code(str(e))
    
    def _simple_aggregation_on_filtered_data(self, df: pd.DataFrame, query: str) -> Optional[Dict]:
        """Handle simple aggregation queries directly without complex processing"""
        query_lower = query.lower()
        
        try:
            # Total employment
            if 'total' in query_lower and 'employment' in query_lower:
                # CRITICAL FIX: De-duplicate by (occupation, industry) before summing
                # to avoid counting the same workers multiple times across different tasks
                if 'ONET job title' in df.columns and 'Industry title' in df.columns:
                    # De-duplicate by occupation-industry pairs
                    unique_pairs = df.groupby(['ONET job title', 'Industry title'])['Employment'].first().reset_index()
                    total_emp = unique_pairs['Employment'].sum()
                    logger.info(f"De-duplicated from {len(df)} rows to {len(unique_pairs)} occupation-industry pairs for employment calculation", show_ui=False)
                else:
                    # Fallback if columns not available
                    total_emp = df['Employment'].sum()
                    logger.warning("Could not de-duplicate employment - columns not found", show_ui=False)
                
                answer = f"**Total Employment:** {total_emp:,.2f} thousand workers ({total_emp*1000:,.0f} people)"
                return {
                    'answer': answer,
                    'csv_data': pd.DataFrame({'Metric': ['Total Employment (thousands)'], 'Value': [total_emp]})
                }
            
            # Count records
            if any(word in query_lower for word in ['how many', 'count']):
                if 'occupation' in query_lower:
                    count = df['ONET job title'].nunique()
                    answer = f"**Number of Occupations:** {count:,}"
                elif 'industry' in query_lower or 'industries' in query_lower:
                    count = df['Industry title'].nunique()
                    answer = f"**Number of Industries:** {count:,}"
                elif 'task' in query_lower:
                    count = len(df)
                    answer = f"**Number of Tasks:** {count:,}"
                else:
                    count = len(df)
                    answer = f"**Number of Records:** {count:,}"
                
                return {
                    'answer': answer,
                    'csv_data': pd.DataFrame({'Metric': ['Count'], 'Value': [count]})
                }
            
            # Average wage
            if 'average' in query_lower and 'wage' in query_lower:
                avg_wage = df['Hourly wage'].mean()
                answer = f"**Average Hourly Wage:** ${avg_wage:.2f}/hour"
                return {
                    'answer': answer,
                    'csv_data': pd.DataFrame({'Metric': ['Average Wage'], 'Value': [avg_wage]})
                }
            
            return None  # Not a simple query
            
        except Exception as e:
            logger.warning(f"Simple aggregation failed: {e}", show_ui=False)
            return None
    
    def _display_csv_download(self, csv_df: pd.DataFrame, prefix: str = "results"):
        """Display CSV data and download button"""
        st.markdown("---")
        st.subheader("📥 Exportable Data")
        
        st.dataframe(csv_df, use_container_width=True)
        
        csv_buffer = StringIO()
        csv_df.to_csv(csv_buffer, index=False)
        csv_str = csv_buffer.getvalue()
        
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_results_{timestamp}.csv"
        
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_str,
            file_name=filename,
            mime="text/csv",
            key=f"download_{prefix}_{timestamp}"
        )
    
    def _process_enhanced_rag(self):
        """Process enhanced RAG with external data (stores in session state)"""
        
        with st.spinner("🔄 Enhancing results with external intelligence..."):
            try:
                # Get the original query and response
                original_query = st.session_state.last_query
                original_response = st.session_state.last_query_results
                
                if not original_query:
                    st.warning("No previous query to enhance")
                    return
                
                # Call LLM to enhance the response with web search
                api_key = config.get_openai_api_key()
                response_builder = ResponseBuilder(api_key)
                
                # Build enhanced context using web search
                enhancement_prompt = f"""
                Original Query: {original_query}
                
                The user has received an initial analysis and now wants additional context from external sources.
                
                Please provide:
                1. Industry trends and recent developments related to this query
                2. External data points or statistics that complement the analysis
                3. Best practices or insights from industry reports
                4. Relevant market dynamics or emerging patterns
                
                Focus on information that would be valuable for labor market analysis and workforce planning.
                Keep the response concise (3-5 key points) and cite sources when possible.
                """
                
                # Get enhanced response (using web search if available)
                enhanced_data = response_builder.generate_enhanced_response(
                    query=enhancement_prompt,
                    context="",
                    use_web_search=True
                )
                
                # Store enhanced data in session state (will be displayed persistently)
                st.session_state.enhanced_rag_data = enhanced_data
                
                logger.info("Enhanced RAG processing completed")
                
            except Exception as e:
                logger.error(f"Enhanced RAG failed: {str(e)}", show_ui=True)
                st.error(f"Failed to enhance with external data: {str(e)}")
    
    def _display_enhanced_rag_section(self):
        """Display the enhanced RAG section persistently"""
        
        st.markdown("---")
        
        # Check if enhanced_rag_data is the new dict structure or old string structure
        enhanced_data = st.session_state.enhanced_rag_data
        
        if isinstance(enhanced_data, dict):
            # New structure with re-query results + external intelligence
            st.markdown("### 🔄 Enhanced Query Results")
            st.markdown(enhanced_data['query_result'])
            
            # Display CSV if available from re-query
            if enhanced_data.get('csv_data') is not None:
                st.markdown("---")
                st.subheader("📥 Enhanced Query Data")
                st.dataframe(enhanced_data['csv_data'])
                
                csv_buffer = StringIO()
                enhanced_data['csv_data'].to_csv(csv_buffer, index=False)
                st.download_button(
                    label="⬇️ Download Enhanced Query Results",
                    data=csv_buffer.getvalue(),
                    file_name="enhanced_query_results.csv",
                    mime="text/csv",
                    key="download_enhanced_persistent"
                )
            
            st.markdown("---")
            st.markdown("### 🌐 External Data & Intelligence")
            st.info("💡 The information below is sourced from external data and LLM intelligence to complement your analysis.")
            st.markdown(enhanced_data['external_intelligence'])
        else:
            # Old structure (just external intelligence string) - for backward compatibility
            st.markdown("### 🌐 External Data & Intelligence")
            st.info("💡 The information below is sourced from external data and LLM intelligence to complement your analysis.")
            st.markdown(enhanced_data)
        
        # Option to clear enhanced results
        if st.button("🗑️ Clear Enhanced Results", key="clear_enhanced_rag"):
            st.session_state.enhanced_rag_data = None
            st.rerun()
    
    def _display_download_section(self):
        """Display the download section persistently"""
        
        st.markdown("---")
        st.subheader("📥 Download Result Dataset")
        
        try:
            # Get the filtered dataset from previous query
            if st.session_state.filtered_dataset is not None and not st.session_state.filtered_dataset.empty:
                df_to_export = st.session_state.filtered_dataset
                st.info(f"📊 Exporting {len(df_to_export):,} records from your query results")
            elif st.session_state.last_query_results and st.session_state.last_query_results.get('csv_data') is not None:
                df_to_export = st.session_state.last_query_results['csv_data']
                st.info(f"📊 Exporting {len(df_to_export):,} records from analysis results")
            else:
                st.warning("⚠️ No data available to export")
                if st.button("Close", key="close_download_empty"):
                    st.session_state.show_download_section = False
                    st.rerun()
                return
            
            # Preview data
            st.markdown("**Preview (first 10 rows):**")
            st.dataframe(df_to_export.head(10), use_container_width=True)
            
            # Export format selection
            st.markdown("**Select Export Format:**")
            
            col_a, col_b = st.columns([3, 1])
            
            with col_a:
                export_format = st.radio(
                    "Format:",
                    ["CSV", "Excel", "JSON"],
                    horizontal=True,
                    key="export_format_radio"
                )
            
            # Generate export data based on format
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            
            if export_format == "CSV":
                buffer = StringIO()
                df_to_export.to_csv(buffer, index=False)
                data = buffer.getvalue()
                mime_type = "text/csv"
                filename = f"labor_market_results_{timestamp}.csv"
            elif export_format == "Excel":
                from io import BytesIO
                buffer = BytesIO()
                df_to_export.to_excel(buffer, index=False, engine='openpyxl')
                data = buffer.getvalue()
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                filename = f"labor_market_results_{timestamp}.xlsx"
            else:  # JSON
                data = df_to_export.to_json(orient='records', indent=2)
                mime_type = "application/json"
                filename = f"labor_market_results_{timestamp}.json"
            
            # Download buttons
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.download_button(
                    label=f"⬇️ Download {export_format} ({len(df_to_export):,} rows)",
                    data=data,
                    file_name=filename,
                    mime=mime_type,
                    type="primary",
                    use_container_width=True,
                    key="download_data_button"
                )
            
            with col2:
                if st.button("✖️ Close", use_container_width=True, key="close_download"):
                    st.session_state.show_download_section = False
                    st.rerun()
            
            st.success(f"✅ Ready to download! File: {filename}")
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}", show_ui=True)
            st.error(f"Failed to prepare export: {str(e)}")
            if st.button("Close", key="close_download_error"):
                st.session_state.show_download_section = False
                st.rerun()
    
    def _show_download_interface(self):
        """Show interface for downloading result dataset"""
        
        st.markdown("---")
        st.subheader("📥 Download Result Dataset")
        
        try:
            # Get the filtered dataset from previous query
            if st.session_state.filtered_dataset is not None and not st.session_state.filtered_dataset.empty:
                df_to_export = st.session_state.filtered_dataset
                st.info(f"📊 Exporting {len(df_to_export):,} records from your query results")
            elif st.session_state.last_query_results and st.session_state.last_query_results.get('csv_data') is not None:
                df_to_export = st.session_state.last_query_results['csv_data']
                st.info(f"📊 Exporting {len(df_to_export):,} records from analysis results")
            else:
                st.warning("⚠️ No data available to export")
                return
            
            # Preview data
            st.markdown("**Preview:**")
            st.dataframe(df_to_export.head(10))
            
            # Export options
            st.markdown("**Export Format:**")
            export_format = st.radio(
                "Choose format:",
                ["CSV", "Excel", "JSON"],
                horizontal=True,
                key="export_format"
            )
            
            # Generate export data
            if export_format == "CSV":
                buffer = StringIO()
                df_to_export.to_csv(buffer, index=False)
                data = buffer.getvalue()
                mime_type = "text/csv"
                file_extension = "csv"
            elif export_format == "Excel":
                from io import BytesIO
                buffer = BytesIO()
                df_to_export.to_excel(buffer, index=False, engine='openpyxl')
                data = buffer.getvalue()
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                file_extension = "xlsx"
            else:  # JSON
                data = df_to_export.to_json(orient='records', indent=2)
                mime_type = "application/json"
                file_extension = "json"
            
            # Download button
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"labor_market_results_{timestamp}.{file_extension}"
            
            st.download_button(
                label=f"⬇️ Download {export_format}",
                data=data,
                file_name=filename,
                mime=mime_type,
                type="primary",
                use_container_width=True,
                key="download_results"
            )
            
            st.success(f"✅ Ready to download! File: {filename}")
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}", show_ui=True)
            st.error(f"Failed to prepare export: {str(e)}")
    
    def _start_new_query(self):
        """Reset state and start a new query - complete UI reset"""
        
        logger.info("Resetting UI for new query", show_ui=False)
        
        # Clear ALL query-related state
        st.session_state.last_query = None
        st.session_state.last_query_results = None
        st.session_state.filtered_dataset = None
        st.session_state.enhanced_rag_data = None
        
        # Clear ALL display flags - this hides all buttons
        st.session_state.show_post_query_buttons = False
        st.session_state.show_followup_interface = False
        st.session_state.show_download_section = False
        st.session_state.run_enhanced_rag = False
        
        # Clear query history
        if 'query_history' in st.session_state:
            st.session_state.query_history = []
        
        # Clear error states
        if 'last_error' in st.session_state:
            st.session_state.last_error = None
        
        # Increment widget version to force new text input widget
        if 'query_widget_version' not in st.session_state:
            st.session_state.query_widget_version = 0
        st.session_state.query_widget_version += 1
        
        # Set a flag to show success message AFTER rerun
        st.session_state.show_new_query_message = True
        
        # Immediate rerun for clean reset - NO messages before this
        st.rerun()
