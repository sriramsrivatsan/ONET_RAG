"""
System Status Sidebar Component
Reusable sidebar for both Admin and Client views with comprehensive status indicators
"""
import streamlit as st
from app.utils.config import config
from datetime import datetime


class SystemStatusSidebar:
    """Comprehensive system status indicators for sidebar"""
    
    @staticmethod
    def render(view_type='client'):
        """
        Render system status sidebar
        
        Args:
            view_type: 'admin' or 'client' to customize status indicators
        """
        
        with st.sidebar:
            # Back button at top
            st.markdown("### 🏠")
            if st.button("← Back to Home", key=f"back_button_{view_type}", use_container_width=True):
                st.session_state.show_landing = True
                st.rerun()
            
            st.markdown("---")
            
            # View indicator
            view_title = "🔧 Admin View" if view_type == 'admin' else "📊 Client View"
            st.markdown(f"### {view_title}")
            
            st.markdown("---")
            
            # System Status Section
            st.markdown("### 🔍 System Status")
            
            # Vector Store Status
            vector_status = st.session_state.get('vector_store_initialized', False)
            status_color = "🟢" if vector_status else "🔴"
            st.markdown(f"{status_color} **Vector Store:** {'Ready' if vector_status else 'Not Initialized'}")
            
            # Document Count
            doc_count = st.session_state.get('document_count', 0)
            st.markdown(f"📚 **Documents:** {doc_count:,}")
            
            # Data Status
            data_loaded = st.session_state.get('dataframe') is not None
            data_color = "🟢" if data_loaded else "🔴"
            st.markdown(f"{data_color} **Data:** {'Loaded' if data_loaded else 'Not Loaded'}")
            
            if data_loaded:
                df = st.session_state.dataframe
                st.markdown(f"   └ Rows: {len(df):,}")
                st.markdown(f"   └ Columns: {len(df.columns)}")
            
            # Aggregations Status
            agg_loaded = st.session_state.get('aggregations') is not None
            agg_color = "🟢" if agg_loaded else "🔴"
            st.markdown(f"{agg_color} **Aggregations:** {'Ready' if agg_loaded else 'Not Available'}")
            
            # Clustering Status
            cluster_loaded = st.session_state.get('cluster_results') is not None
            cluster_color = "🟢" if cluster_loaded else "🔴"
            st.markdown(f"{cluster_color} **Clustering:** {'Complete' if cluster_loaded else 'Not Run'}")
            
            st.markdown("---")
            
            # Data Dictionary Status (if admin view)
            if view_type == 'admin':
                st.markdown("### 📖 Data Dictionary")
                dict_status = st.session_state.get('dictionary_loaded', False)
                dict_color = "🟢" if dict_status else "🟡"
                st.markdown(f"{dict_color} **Status:** {'Loaded' if dict_status else 'Available'}")
                
                if hasattr(st.session_state, 'enrichment_stats'):
                    stats = st.session_state.enrichment_stats
                    st.markdown(f"   └ Skills: {stats.get('skills_extracted', 0):,}")
                    st.markdown(f"   └ Industries: {stats.get('industries_matched', 0):,}")
                
                st.markdown("---")
            
            # Configuration Status
            st.markdown("### ⚙️ Configuration")
            
            config_status = config.validate_config()
            
            if config_status['valid']:
                st.success("✅ All Systems OK")
            else:
                st.error("⚠️ Configuration Issues")
                for error in config_status['errors']:
                    st.error(f"• {error}")
            
            if config_status['warnings']:
                for warning in config_status['warnings']:
                    st.warning(f"• {warning}")
            
            st.markdown("---")
            
            # Model Information
            st.markdown("### 🤖 AI Models")
            st.markdown(f"**LLM:** {config.LLM_MODEL}")
            st.markdown(f"**Embeddings:** {config.EMBEDDING_MODEL.split('/')[-1][:20]}")
            
            st.markdown("---")
            
            # Session Info (if admin view)
            if view_type == 'admin':
                st.markdown("### 📊 Session Info")
                
                # Last ingestion time
                last_ingest = st.session_state.get('last_ingestion_time', 'Never')
                st.markdown(f"**Last Upload:** {last_ingest}")
                
                # Query count
                query_history = st.session_state.get('query_history', [])
                st.markdown(f"**Queries Run:** {len(query_history)}")
                
                st.markdown("---")
            
            # Client View Specific Status
            if view_type == 'client':
                st.markdown("### 💬 Query Status")
                
                # Query count
                query_history = st.session_state.get('query_history', [])
                st.markdown(f"**Total Queries:** {len(query_history)}")
                
                # Last query time
                if query_history:
                    last_query_time = query_history[-1].get('timestamp', 'Unknown')
                    st.markdown(f"**Last Query:** {last_query_time}")
                
                st.markdown("---")
            
            # System Resources
            st.markdown("### 💾 Resources")
            
            # Memory status (if available)
            try:
                import psutil
                memory = psutil.virtual_memory()
                memory_used = memory.percent
                memory_color = "🟢" if memory_used < 70 else "🟡" if memory_used < 90 else "🔴"
                st.markdown(f"{memory_color} **Memory:** {memory_used:.1f}%")
            except:
                st.markdown("🟡 **Memory:** Not Available")
            
            # Disk status
            try:
                import shutil
                disk = shutil.disk_usage("/")
                disk_used = (disk.used / disk.total) * 100
                disk_color = "🟢" if disk_used < 70 else "🟡" if disk_used < 90 else "🔴"
                st.markdown(f"{disk_color} **Disk:** {disk_used:.1f}%")
            except:
                st.markdown("🟡 **Disk:** Not Available")
            
            st.markdown("---")
            
            # Quick Actions (if admin)
            if view_type == 'admin':
                with st.expander("⚡ Quick Actions"):
                    if st.button("🔄 Refresh Status", key="refresh_status", use_container_width=True):
                        st.rerun()
                    
                    if st.button("🗑️ Clear Cache", key="clear_cache", use_container_width=True):
                        st.cache_data.clear()
                        st.success("Cache cleared!")
                        st.rerun()
            
            # About section
            with st.expander("ℹ️ About"):
                st.markdown("""
                **Occupational Data Analysis System**
                
                Version: 2.0.7
                
                An intelligent labor market analysis system 
                powered by advanced RAG technology.
                
                **Technology Stack:**
                - ChromaDB (Vector Store)
                - OpenAI GPT-4o-mini (LLM)
                - Sentence Transformers (Embeddings)
                - Streamlit (UI Framework)
                - Data Dictionary (Labor Market Ontology)
                """)
