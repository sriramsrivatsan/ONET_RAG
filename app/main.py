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
from app.utils.logging import logger
from app.utils.config import config


def initialize_session_state():
    """Initialize session state variables"""
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
    with st.sidebar:
        st.title("🎯 Navigation")
        
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
        page_title="Labor Market RAG",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Check for persisted index on startup
    check_persisted_index()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content based on current view
    if st.session_state.current_view == 'admin':
        admin_view = AdminView()
        admin_view.render()
    else:
        client_view = ClientView()
        client_view.render()
    
    # Footer
    st.markdown("---")
    st.caption("Labor Market RAG System | Built with Streamlit + ChromaDB + OpenAI")


if __name__ == "__main__":
    main()
