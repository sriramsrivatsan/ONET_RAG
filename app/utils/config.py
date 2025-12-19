"""
Configuration and environment management for Labor Market RAG
"""
import os
from typing import Optional
import streamlit as st


class Config:
    """Centralized configuration management"""
    
    # Vector Database
    CHROMA_PERSIST_PATH: str = os.getenv('CHROMA_PERSIST_PATH', '/data/chroma_db')
    CHROMA_COLLECTION_NAME: str = 'labor_market_collection'
    ENABLE_PERSISTENCE: bool = os.getenv('ENABLE_PERSISTENCE', 'true').lower() == 'true'
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    EMBEDDING_DIMENSION: int = 384  # For all-MiniLM-L6-v2
    EMBEDDING_BATCH_SIZE: int = 32
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2000
    
    # Processing Configuration
    MAX_MEMORY_PERCENT: int = 80
    PARALLEL_BATCH_SIZE: int = 250
    MAX_DATASET_ROWS: int = 100000
    
    # Clustering Configuration
    N_CLUSTERS_TASKS: int = 15
    N_CLUSTERS_ROLES: int = 10
    N_CLUSTERS_OCCUPATIONS: int = 20
    CLUSTERING_SAMPLE_SIZE: int = 10000
    
    # Retrieval Configuration
    DEFAULT_TOP_K: int = 10
    MAX_TOP_K: int = 50
    SIMILARITY_THRESHOLD: float = 0.3
    
    # Query Classification Thresholds
    COMPUTATIONAL_KEYWORDS = [
        'count', 'total', 'how many', 'sum', 'average', 'top', 'rank',
        'percentage', 'proportion', 'compare', 'most', 'least', 'group by'
    ]
    
    SEMANTIC_KEYWORDS = [
        'similar', 'like', 'related', 'explain', 'describe', 'what is',
        'tell me about', 'difference between', 'comparison'
    ]
    
    @classmethod
    def get_openai_api_key(cls) -> Optional[str]:
        """Get OpenAI API key from Streamlit secrets or environment"""
        try:
            if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                return st.secrets['OPENAI_API_KEY']
            return os.getenv('OPENAI_API_KEY')
        except Exception:
            return None
    
    @classmethod
    def validate_config(cls) -> dict:
        """Validate configuration and return status"""
        status = {'valid': True, 'errors': [], 'warnings': []}
        
        if not cls.get_openai_api_key():
            status['errors'].append('OpenAI API key not configured')
            status['valid'] = False
        
        if cls.ENABLE_PERSISTENCE and not os.path.exists(os.path.dirname(cls.CHROMA_PERSIST_PATH)):
            status['warnings'].append(f'Persistence path may need creation: {cls.CHROMA_PERSIST_PATH}')
        
        return status


config = Config()
