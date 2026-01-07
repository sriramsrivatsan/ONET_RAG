"""
Main Streamlit application for Labor Market RAG
"""
import streamlit as st
import sys
import os

# Add parent directory to Python path so 'app' module can be imported
# This adds /app to Python path when running from /app/app/main.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui.admin import AdminView
from app.ui.client import ClientView
from app.ui.landing import LandingPage
from app.utils.logging import logger
from app.utils.config import config
from app.utils.auth import is_authentication_required, is_authenticated, render_login_dialog


def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'show_landing' not in st.session_state:
        st.session_state.show_landing = True
    
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'client'
    
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    
    if 'vector_store_initialized' not in st.session_state:
        st.session_state.vector_store_initialized = False
    
    if 'dataframe' not in st.session_state:
        st.session_state.dataframe = None
    
    if 'aggregations' not in st.session_state:
        st.session_state.aggregations = None
    
    if 'cluster_results' not in st.session_state:
        st.session_state.cluster_results = None
    
    if 'aggregator' not in st.session_state:
        st.session_state.aggregator = None
    
    if 'document_count' not in st.session_state:
        st.session_state.document_count = 0
    
    # New: Query context management for follow-up queries and enhanced RAG
    if 'last_query' not in st.session_state:
        st.session_state.last_query = None
    
    if 'last_response' not in st.session_state:
        st.session_state.last_response = None
    
    if 'filtered_dataframe' not in st.session_state:
        st.session_state.filtered_dataframe = None
    
    if 'query_results_data' not in st.session_state:
        st.session_state.query_results_data = None
    
    if 'show_query_actions' not in st.session_state:
        st.session_state.show_query_actions = False
    
    if 'enhanced_rag_response' not in st.session_state:
        st.session_state.enhanced_rag_response = None
    
    # Persistent display flags for post-query features
    if 'show_followup_interface' not in st.session_state:
        st.session_state.show_followup_interface = False
    
    if 'show_download_section' not in st.session_state:
        st.session_state.show_download_section = False
    
    if 'enhanced_rag_data' not in st.session_state:
        st.session_state.enhanced_rag_data = None
    
    if 'run_enhanced_rag' not in st.session_state:
        st.session_state.run_enhanced_rag = False
    
    # Follow-up query state
    if 'last_query' not in st.session_state:
        st.session_state.last_query = None
    
    if 'last_query_results' not in st.session_state:
        st.session_state.last_query_results = None
    
    if 'filtered_dataset' not in st.session_state:
        st.session_state.filtered_dataset = None
    
    if 'show_post_query_buttons' not in st.session_state:
        st.session_state.show_post_query_buttons = False
    
    if 'enhanced_rag_data' not in st.session_state:
        st.session_state.enhanced_rag_data = None
    
    # Query input state
    if 'main_query' not in st.session_state:
        st.session_state.main_query = ""
    
    if 'reset_query_flag' not in st.session_state:
        st.session_state.reset_query_flag = False
    
    if 'last_ingestion_time' not in st.session_state:
        st.session_state.last_ingestion_time = 'Never'
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'system_logs' not in st.session_state:
        st.session_state.system_logs = []
    
    if 'index_check_done' not in st.session_state:
        st.session_state.index_check_done = False


def save_session_state_to_disk(df, aggregations, cluster_results):
    """Save session state data to disk for persistence"""
    import pickle
    from app.utils.helpers import ensure_directory
    
    if not config.ENABLE_PERSISTENCE:
        return
    
    try:
        # Create directory for session state data
        state_dir = os.path.join(config.CHROMA_PERSIST_PATH, 'session_state')
        ensure_directory(state_dir)
        
        # Save dataframe
        df_path = os.path.join(state_dir, 'dataframe.pkl')
        with open(df_path, 'wb') as f:
            pickle.dump(df, f)
        
        # Save aggregations
        agg_path = os.path.join(state_dir, 'aggregations.pkl')
        with open(agg_path, 'wb') as f:
            pickle.dump(aggregations, f)
        
        # Save cluster results
        cluster_path = os.path.join(state_dir, 'cluster_results.pkl')
        with open(cluster_path, 'wb') as f:
            pickle.dump(cluster_results, f)
        
        logger.info("✓ Session state saved to disk", show_ui=False)
        
    except Exception as e:
        logger.error(f"Failed to save session state: {str(e)}", show_ui=False)


def load_session_state_from_disk():
    """Load session state data from disk"""
    import pickle
    
    if not config.ENABLE_PERSISTENCE:
        return None, None, None
    
    try:
        state_dir = os.path.join(config.CHROMA_PERSIST_PATH, 'session_state')
        
        # Check if state files exist
        df_path = os.path.join(state_dir, 'dataframe.pkl')
        agg_path = os.path.join(state_dir, 'aggregations.pkl')
        cluster_path = os.path.join(state_dir, 'cluster_results.pkl')
        
        if not all([os.path.exists(df_path), os.path.exists(agg_path), os.path.exists(cluster_path)]):
            return None, None, None
        
        # Load dataframe
        with open(df_path, 'rb') as f:
            df = pickle.load(f)
        
        # Load aggregations
        with open(agg_path, 'rb') as f:
            aggregations = pickle.load(f)
        
        # Load cluster results
        with open(cluster_path, 'rb') as f:
            cluster_results = pickle.load(f)
        
        logger.info("✓ Session state loaded from disk", show_ui=False)
        
        return df, aggregations, cluster_results
        
    except Exception as e:
        logger.error(f"Failed to load session state: {str(e)}", show_ui=False)
        return None, None, None


def check_persisted_index():
    """Check for and load any persisted ChromaDB index on startup"""
    
    # Only check once per session
    if st.session_state.get('index_check_done', False):
        return
    
    # Only check if persistence is enabled
    if not config.ENABLE_PERSISTENCE:
        st.session_state.index_check_done = True
        return
    
    try:
        from app.rag.vector_store import VectorStore
        from app.analytics.aggregations import DataAggregator
        
        # Initialize vector store if not already done
        if st.session_state.vector_store is None:
            vector_store = VectorStore()
            st.session_state.vector_store = vector_store
        else:
            vector_store = st.session_state.vector_store
        
        # Check for existing index
        index_status = vector_store.check_existing_index()
        
        if index_status.get('has_data', False):
            # Load the existing index
            success = vector_store.load_existing_index()
            
            if success:
                st.session_state.vector_store_initialized = True
                st.session_state.document_count = index_status['document_count']
                
                # Load session state data (dataframe, aggregations, cluster_results)
                df, aggregations, cluster_results = load_session_state_from_disk()
                
                if df is not None:
                    st.session_state.dataframe = df
                    st.session_state.aggregations = aggregations
                    st.session_state.cluster_results = cluster_results
                    
                    # Recreate aggregator
                    aggregator = DataAggregator(df)
                    st.session_state.aggregator = aggregator
                    
                    logger.info(
                        f"✓ Restored complete state: {index_status['document_count']} documents, "
                        f"{len(df)} rows",
                        show_ui=False
                    )
                else:
                    logger.info(
                        f"✓ Restored index: {index_status['document_count']} documents "
                        f"(dataframe not available)",
                        show_ui=False
                    )
        
        st.session_state.index_check_done = True
        
    except Exception as e:
        logger.error(f"Error checking persisted index: {str(e)}", show_ui=False)
        st.session_state.index_check_done = True


def render_sidebar():
    """Render the sidebar with navigation and settings"""
    from app.utils.auth import is_authentication_required, logout
    
    with st.sidebar:
        st.title("🎯 Navigation")
        
        # Logout button if authentication is enabled
        if is_authentication_required():
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()
            st.markdown("---")
        
        # View selection
        view = st.radio(
            "Select View",
            ["Client (Analyst)", "Admin (System)"],
            key="view_selector"
        )
        
        st.session_state.current_view = 'client' if 'Client' in view else 'admin'
        
        st.markdown("---")
        
        # System info
        st.subheader("🔧 System Info")
        
        # Vector store status
        vector_status = st.session_state.get('vector_store_initialized', False)
        status_icon = "✅" if vector_status else "❌"
        st.write(f"{status_icon} Vector Store: {'Ready' if vector_status else 'Not Initialized'}")
        
        # Document count
        doc_count = st.session_state.get('document_count', 0)
        st.write(f"📚 Documents: {doc_count:,}")
        
        # Data loaded
        data_loaded = st.session_state.get('dataframe') is not None
        data_icon = "✅" if data_loaded else "❌"
        st.write(f"{data_icon} Data: {'Loaded' if data_loaded else 'Not Loaded'}")
        
        st.markdown("---")
        
        # Configuration validation
        st.subheader("⚙️ Configuration")
        
        config_status = config.validate_config()
        
        if config_status['valid']:
            st.success("✅ Configuration Valid")
        else:
            st.error("❌ Configuration Issues")
            for error in config_status['errors']:
                st.error(f"- {error}")
        
        if config_status['warnings']:
            for warning in config_status['warnings']:
                st.warning(f"- {warning}")
        
        st.markdown("---")
        
        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
            **Labor Market RAG System**
            
            A Hybrid Retrieval-Augmented Generation system for labor market intelligence.
            
            **Features:**
            - Semantic search (vector similarity)
            - Computational analytics
            - Hybrid query processing
            - Clustering for reduced hallucinations
            - Explainable responses
            
            **Technology:**
            - ChromaDB (vector store)
            - OpenAI GPT-4o-mini (LLM)
            - Sentence Transformers (embeddings)
            - Streamlit (UI)
            """)


def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title="Occupational Data Analysis System",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Authentication check - show login if required and not authenticated
    if is_authentication_required() and not is_authenticated():
        render_login_dialog()
        return  # Stop here if not authenticated
    
    # Check for persisted index on startup
    check_persisted_index()
    
    # Show landing page or views
    if st.session_state.get('show_landing', True):
        # Show landing page (no sidebar)
        landing_page = LandingPage()
        landing_page.render()
    else:
        # Show admin or client view with sidebar
        if st.session_state.current_view == 'admin':
            admin_view = AdminView()
            admin_view.render()
        else:
            client_view = ClientView()
            client_view.render()
    
    # Footer (only on landing page)
    if st.session_state.get('show_landing', True):
        st.markdown("---")
        st.caption("Occupational Data Analysis System | Built with Advanced RAG Technology")


if __name__ == "__main__":
    main()
