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
