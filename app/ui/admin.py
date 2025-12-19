"""
Admin View UI for system management
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional

from app.ingestion.csv_loader import CSVLoader
from app.ingestion.preprocessing import DataPreprocessor
from app.analytics.aggregations import DataAggregator
from app.analytics.clustering import LaborMarketClusterer
from app.analytics.similarity import SimilarityAnalyzer
from app.rag.vector_store import VectorStore
from app.utils.logging import logger
from app.utils.helpers import get_memory_usage, get_system_info


class AdminView:
    """Admin view for system management and monitoring"""
    
    def __init__(self):
        self.csv_loader = None
        self.preprocessor = DataPreprocessor()
    
    def render(self):
        """Render the admin view"""
        
        st.title("🔧 Labor Market RAG - Admin Panel")
        st.markdown("---")
        
        # System status
        self._render_system_status()
        
        st.markdown("---")
        
        # Data ingestion section
        self._render_data_ingestion()
        
        st.markdown("---")
        
        # System logs
        self._render_system_logs()
    
    def _render_system_status(self):
        """Render system status indicators"""
        
        st.subheader("📊 System Status")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            vector_store_status = st.session_state.get('vector_store_initialized', False)
            status_icon = "✅" if vector_store_status else "❌"
            st.metric("Vector Store", status_icon)
        
        with col2:
            doc_count = st.session_state.get('document_count', 0)
            st.metric("Indexed Documents", f"{doc_count:,}")
        
        with col3:
            memory = get_memory_usage()
            memory_color = "🟢" if memory['percent'] < 70 else "🟡" if memory['percent'] < 85 else "🔴"
            st.metric("Memory Usage", f"{memory_color} {memory['percent']:.1f}%")
        
        with col4:
            last_ingestion = st.session_state.get('last_ingestion_time', 'Never')
            st.metric("Last Ingestion", last_ingestion)
        
        # Detailed system info
        with st.expander("🖥️ Detailed System Information"):
            sys_info = get_system_info()
            if sys_info:
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write("**CPU**")
                    st.write(f"- Cores: {sys_info.get('cpu_count', 'N/A')}")
                    st.write(f"- Usage: {sys_info.get('cpu_percent', 0):.1f}%")
                    
                    st.write("**Memory**")
                    st.write(f"- Total: {sys_info.get('memory_total_gb', 0):.2f} GB")
                    st.write(f"- Available: {sys_info.get('memory_available_gb', 0):.2f} GB")
                    st.write(f"- Usage: {sys_info.get('memory_percent', 0):.1f}%")
                
                with col_b:
                    st.write("**Disk**")
                    st.write(f"- Total: {sys_info.get('disk_total_gb', 0):.2f} GB")
                    st.write(f"- Used: {sys_info.get('disk_used_gb', 0):.2f} GB")
                    st.write(f"- Usage: {sys_info.get('disk_percent', 0):.1f}%")
    
    def _render_data_ingestion(self):
        """Render data ingestion section"""
        
        st.subheader("📥 Data Ingestion Pipeline")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload ONET Labor Market CSV",
            type=['csv'],
            help="Upload your enhanced ONET dataset"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            rebuild_index = st.checkbox("Rebuild Index", value=True)
        
        if uploaded_file is not None:
            st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.2f} MB)")
            
            if st.button("🚀 Start Ingestion Pipeline", type="primary"):
                self._run_ingestion_pipeline(uploaded_file, rebuild_index)
        
        # Show dataset statistics if loaded
        if st.session_state.get('dataframe') is not None:
            self._render_dataset_statistics()
    
    def _run_ingestion_pipeline(self, uploaded_file, rebuild_index: bool):
        """Run the complete ingestion pipeline"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Load CSV
            status_text.text("Step 1/6: Loading CSV...")
            progress_bar.progress(10)
            
            self.csv_loader = CSVLoader()
            if not self.csv_loader.load_from_upload(uploaded_file):
                st.error("Failed to load CSV")
                return
            
            df = self.csv_loader.get_dataframe()
            
            # Step 2: Validate
            status_text.text("Step 2/6: Validating dataset...")
            progress_bar.progress(20)
            
            validation_results = self.csv_loader.validate_dataset()
            if not validation_results['valid']:
                st.error(f"Validation failed: {validation_results['errors']}")
                return
            
            # Step 3: Preprocess
            status_text.text("Step 3/6: Preprocessing data...")
            progress_bar.progress(35)
            
            df_processed = self.preprocessor.preprocess_dataset(df)
            
            # Step 4: Compute aggregations
            status_text.text("Step 4/6: Computing aggregations...")
            progress_bar.progress(50)
            
            aggregator = DataAggregator(df_processed)
            aggregations = aggregator.compute_all_aggregations()
            
            # Step 5: Clustering
            status_text.text("Step 5/6: Performing clustering...")
            progress_bar.progress(65)
            
            clusterer = LaborMarketClusterer(df_processed)
            cluster_results = clusterer.perform_all_clustering()
            df_processed = clusterer.df  # Get updated dataframe with cluster IDs
            
            # Step 6: Vector indexing
            status_text.text("Step 6/6: Creating vector index...")
            progress_bar.progress(80)
            
            vector_store = st.session_state.get('vector_store')
            if vector_store is None:
                vector_store = VectorStore()
                vector_store.initialize()
                st.session_state.vector_store = vector_store
            
            if rebuild_index:
                vector_store.create_or_get_collection(reset=True)
            else:
                vector_store.create_or_get_collection(reset=False)
            
            vector_store.index_documents(df_processed)
            
            progress_bar.progress(100)
            status_text.text("✅ Ingestion complete!")
            
            # Store in session state
            st.session_state.dataframe = df_processed
            st.session_state.aggregations = aggregations
            st.session_state.cluster_results = cluster_results
            st.session_state.aggregator = aggregator
            st.session_state.vector_store_initialized = True
            st.session_state.document_count = vector_store.document_count
            st.session_state.last_ingestion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            st.success("🎉 Data ingestion pipeline completed successfully!")
            
            # Show summary
            with st.expander("📋 Ingestion Summary", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Rows", f"{len(df_processed):,}")
                    st.metric("Columns", len(df_processed.columns))
                
                with col2:
                    st.metric("Industries", validation_results['statistics'].get('unique_industries', 0))
                    st.metric("Occupations", validation_results['statistics'].get('unique_occupations', 0))
                
                with col3:
                    st.metric("Indexed Documents", vector_store.document_count)
                    st.metric("Cluster Groups", len(cluster_results))
            
        except Exception as e:
            logger.error(f"Ingestion pipeline failed: {str(e)}", show_ui=True)
            st.error(f"Pipeline failed: {str(e)}")
        finally:
            progress_bar.empty()
            status_text.empty()
    
    def _render_dataset_statistics(self):
        """Render dataset statistics"""
        
        with st.expander("📊 Dataset Statistics", expanded=False):
            df = st.session_state.get('dataframe')
            
            if df is not None:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Shape**")
                    st.write(f"- Rows: {len(df):,}")
                    st.write(f"- Columns: {len(df.columns)}")
                    st.write(f"- Memory: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
                
                with col2:
                    st.write("**Data Types**")
                    dtype_counts = df.dtypes.value_counts()
                    for dtype, count in dtype_counts.items():
                        st.write(f"- {dtype}: {count}")
                
                # Show sample data
                st.write("**Sample Data (first 5 rows)**")
                display_cols = ['Industry title', 'ONET job title', 'Employment', 'Hourly wage']
                available_cols = [col for col in display_cols if col in df.columns]
                st.dataframe(df[available_cols].head())
    
    def _render_system_logs(self):
        """Render system logs"""
        
        st.subheader("📝 System Logs")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            log_level = st.selectbox(
                "Filter by level",
                ["All", "INFO", "WARNING", "ERROR", "DEBUG"]
            )
        
        with col2:
            max_logs = st.slider("Max logs to display", 10, 100, 50)
        
        with col3:
            if st.button("Clear Logs"):
                logger.clear_ui_logs()
                st.rerun()
        
        # Get and filter logs
        if log_level == "All":
            logs = logger.get_ui_logs()
        else:
            logs = logger.get_ui_logs(level=log_level)
        
        # Display logs
        if logs:
            logs_to_show = logs[-max_logs:]
            
            for log in reversed(logs_to_show):
                level = log['level']
                timestamp = log['timestamp']
                message = log['message']
                
                if level == 'ERROR':
                    st.error(f"[{timestamp}] {message}")
                elif level == 'WARNING':
                    st.warning(f"[{timestamp}] {message}")
                elif level == 'INFO':
                    st.info(f"[{timestamp}] {message}")
                else:
                    st.text(f"[{timestamp}] [{level}] {message}")
        else:
            st.info("No logs to display")
        
        # Download logs
        if logs:
            log_text = '\n'.join([
                f"[{log['timestamp']}] [{log['level']}] {log['message']}"
                for log in logs
            ])
            
            st.download_button(
                label="📥 Download Logs",
                data=log_text,
                file_name=f"labor_rag_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
