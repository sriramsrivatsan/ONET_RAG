"""
Vector store implementation using ChromaDB
"""
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import streamlit as st

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from app.utils.logging import logger
from app.utils.config import config
from app.utils.helpers import ensure_directory, PerformanceTimer


class VectorStore:
    """ChromaDB-based vector store for labor market data"""
    
    def __init__(self):
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB or SentenceTransformers not available")
        
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.is_initialized = False
        self.document_count = 0
        
    def initialize(self):
        """Initialize ChromaDB client and embedding model"""
        try:
            logger.info("Initializing vector store", show_ui=True)
            
            # Initialize embedding model
            with st.spinner("Loading embedding model..."):
                self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            logger.info(f"✓ Loaded embedding model: {config.EMBEDDING_MODEL}", show_ui=True)
            
            # Initialize ChromaDB client
            if config.ENABLE_PERSISTENCE:
                ensure_directory(config.CHROMA_PERSIST_PATH)
                self.client = chromadb.PersistentClient(
                    path=config.CHROMA_PERSIST_PATH,
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info(f"✓ ChromaDB client initialized (persistent mode)", show_ui=True)
            else:
                self.client = chromadb.Client(
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info(f"✓ ChromaDB client initialized (in-memory mode)", show_ui=True)
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}", show_ui=True)
            raise
    
    def check_existing_index(self) -> Dict[str, Any]:
        """
        Check if an existing index exists and return its status
        Returns: dict with 'exists', 'document_count', 'collection_name'
        """
        try:
            if not self.is_initialized:
                self.initialize()
            
            # List all collections
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if config.CHROMA_COLLECTION_NAME in collection_names:
                # Get the collection
                temp_collection = self.client.get_collection(name=config.CHROMA_COLLECTION_NAME)
                doc_count = temp_collection.count()
                
                return {
                    'exists': True,
                    'document_count': doc_count,
                    'collection_name': config.CHROMA_COLLECTION_NAME,
                    'has_data': doc_count > 0
                }
            else:
                return {
                    'exists': False,
                    'document_count': 0,
                    'collection_name': config.CHROMA_COLLECTION_NAME,
                    'has_data': False
                }
                
        except Exception as e:
            logger.error(f"Error checking existing index: {str(e)}", show_ui=False)
            return {
                'exists': False,
                'document_count': 0,
                'collection_name': config.CHROMA_COLLECTION_NAME,
                'has_data': False,
                'error': str(e)
            }
    
    def load_existing_index(self) -> bool:
        """
        Load an existing persisted index if available
        Returns: True if loaded successfully, False otherwise
        """
        try:
            if not self.is_initialized:
                self.initialize()
            
            index_status = self.check_existing_index()
            
            if index_status['exists'] and index_status['has_data']:
                # Get the existing collection
                self.collection = self.client.get_collection(name=config.CHROMA_COLLECTION_NAME)
                self.document_count = self.collection.count()
                
                logger.info(f"✓ Loaded existing index: {self.document_count} documents", show_ui=True)
                return True
            else:
                logger.info("No existing index found", show_ui=False)
                return False
                
        except Exception as e:
            logger.error(f"Failed to load existing index: {str(e)}", show_ui=True)
            return False
    
    def create_or_get_collection(self, reset: bool = False) -> bool:
        """Create or get the collection"""
        try:
            if reset:
                # Delete existing collection
                try:
                    self.client.delete_collection(name=config.CHROMA_COLLECTION_NAME)
                    logger.info("✓ Deleted existing collection", show_ui=True)
                except:
                    pass
            
            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=config.CHROMA_COLLECTION_NAME,
                metadata={"description": "Labor market ONET data"}
            )
            
            self.document_count = self.collection.count()
            logger.info(f"✓ Collection ready: {self.document_count} documents", show_ui=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}", show_ui=True)
            return False
    
    def index_documents(
        self,
        df: pd.DataFrame,
        batch_size: int = None
    ) -> bool:
        """Index documents from DataFrame"""
        
        if batch_size is None:
            batch_size = config.EMBEDDING_BATCH_SIZE
        
        try:
            with PerformanceTimer("Document Indexing"):
                logger.info(f"Starting document indexing: {len(df)} documents", show_ui=True)
                
                # Prepare documents
                documents = []
                metadatas = []
                ids = []
                
                for idx, row in df.iterrows():
                    try:
                        # Create document text
                        doc_text = self._create_document_text(row)
                        
                        # Create metadata
                        metadata = self._create_metadata(row, idx)
                        
                        documents.append(doc_text)
                        metadatas.append(metadata)
                        ids.append(f"doc_{idx}")
                    except Exception as e:
                        logger.error(f"Error processing row {idx}: {str(e)}", show_ui=False)
                        logger.error(f"Row data types: {row.dtypes if hasattr(row, 'dtypes') else 'N/A'}", show_ui=False)
                        # Re-raise to see full traceback
                        raise
                
                # Create embeddings and add to collection in batches
                total_docs = len(documents)
                for i in range(0, total_docs, batch_size):
                    batch_end = min(i + batch_size, total_docs)
                    batch_docs = documents[i:batch_end]
                    batch_metadata = metadatas[i:batch_end]
                    batch_ids = ids[i:batch_end]
                    
                    # Generate embeddings
                    embeddings = self.embedding_model.encode(
                        batch_docs,
                        show_progress_bar=False,
                        convert_to_numpy=True
                    ).tolist()
                    
                    # Add to collection
                    self.collection.add(
                        documents=batch_docs,
                        embeddings=embeddings,
                        metadatas=batch_metadata,
                        ids=batch_ids
                    )
                    
                    if (batch_end) % (batch_size * 10) == 0:
                        logger.info(f"  Indexed {batch_end}/{total_docs} documents", show_ui=True)
                
                self.document_count = self.collection.count()
                logger.info(f"✓ Indexing complete: {self.document_count} documents indexed", show_ui=True)
                
                return True
                
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}", show_ui=True)
            return False
    
    def _create_document_text(self, row: pd.Series) -> str:
        """Create searchable document text from row"""
        parts = []
        
        # Helper function to safely get string value
        def safe_str(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                return ' '.join(str(v) for v in value)
            # For scalar values, check if NaN
            try:
                if pd.isna(value):
                    return None
            except (TypeError, ValueError):
                # pd.isna might fail on some types, just convert to string
                pass
            return str(value)
        
        # Add key fields
        val = safe_str(row.get('ONET job title'))
        if val:
            parts.append(f"Occupation: {val}")
        
        val = safe_str(row.get('Industry title'))
        if val:
            parts.append(f"Industry: {val}")
        
        val = safe_str(row.get('Job description'))
        if val:
            parts.append(f"Description: {val}")
        
        val = safe_str(row.get('Detailed job tasks'))
        if val:
            parts.append(f"Tasks: {val}")
        
        val = safe_str(row.get('Detailed work activities'))
        if val:
            parts.append(f"Activities: {val}")
        
        return ' '.join(parts)
    
    def _create_metadata(self, row: pd.Series, idx: int) -> Dict[str, Any]:
        """Create metadata dictionary from row"""
        metadata = {'row_index': int(idx)}
        
        # Helper to safely check if value is usable
        def is_valid_value(val):
            """Check if value is valid (not NaN, not None, not empty array)"""
            if val is None:
                return False
            
            # For arrays/lists, check if non-empty
            if hasattr(val, '__len__') and not isinstance(val, str):
                try:
                    return len(val) > 0
                except:
                    return False
            
            # For scalar values, use pd.isna
            try:
                if pd.isna(val):
                    return False
            except (TypeError, ValueError):
                # pd.isna might fail on some types, assume valid
                pass
            
            return True
        
        # Add string fields
        str_fields = [
            'Industry title', 'ONET job title', 'BLS job title',
            'ONET SOC code', 'BLS SOC code'
        ]
        
        for field in str_fields:
            if field in row.index:
                val = row[field]
                if is_valid_value(val):
                    metadata[field.lower().replace(' ', '_')] = str(val)
        
        # Add numeric fields
        num_fields = [
            'Employment', 'Hourly wage', 'Total hours worked per week',
            'Hours per week spent on task'
        ]
        
        for field in num_fields:
            if field in row.index:
                val = row[field]
                if is_valid_value(val):
                    try:
                        metadata[field.lower().replace(' ', '_')] = float(val)
                    except (ValueError, TypeError):
                        pass
        
        # Add cluster IDs if present
        cluster_fields = ['task_cluster_id', 'activity_cluster_id', 'occupation_cluster_id']
        for field in cluster_fields:
            if field in row.index:
                val = row[field]
                if is_valid_value(val):
                    try:
                        metadata[field] = int(val)
                    except (ValueError, TypeError):
                        pass
        
        # Add enriched fields from data dictionary
        enriched_str_fields = [
            'Industry_Canonical', 'Occupation_Major_Group', 'Wage_Band',
            'Task_Importance_Level', 'Required_Education', 'NAICS_Code'
        ]
        
        for field in enriched_str_fields:
            if field in row.index:
                val = row[field]
                if is_valid_value(val):
                    metadata[field.lower()] = str(val)
        
        # Add skill count if available
        if 'Skill_Count' in row.index:
            val = row['Skill_Count']
            if is_valid_value(val):
                try:
                    metadata['skill_count'] = int(val)
                except (ValueError, TypeError):
                    pass
        
        # Add extracted skills (convert list to string for metadata)
        if 'Extracted_Skills' in row.index:
            val = row['Extracted_Skills']
            if is_valid_value(val):
                try:
                    # Handle list of skills
                    if isinstance(val, list) and len(val) > 0:
                        # Join skill names
                        skill_names = [s.get('skill', '') for s in val if isinstance(s, dict) and s.get('skill')]
                        # Explicit length check to avoid numpy array ambiguity
                        if len(skill_names) > 0:
                            metadata['extracted_skills'] = ', '.join(skill_names[:10])  # Limit to 10 skills
                except Exception as e:
                    logger.debug(f"Could not process Extracted_Skills for row {idx}: {str(e)}", show_ui=False)
        
        return metadata
    
    def search(
        self,
        query: str,
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        
        if not self.collection:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                query,
                convert_to_numpy=True
            ).tolist()
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter_dict if filter_dict else None
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'score': float(1 - results['distances'][0][i]) if results['distances'] else 0.0
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", show_ui=False)
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        if not self.collection:
            return {'initialized': False}
        
        return {
            'initialized': self.is_initialized,
            'document_count': self.document_count,
            'collection_name': config.CHROMA_COLLECTION_NAME,
            'embedding_model': config.EMBEDDING_MODEL,
            'persistence_enabled': config.ENABLE_PERSISTENCE,
            'persistence_path': config.CHROMA_PERSIST_PATH if config.ENABLE_PERSISTENCE else None
        }
