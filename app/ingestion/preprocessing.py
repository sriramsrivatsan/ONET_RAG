"""
Data preprocessing and text normalization for Labor Market data
Enhanced with data dictionary support
"""
import pandas as pd
import numpy as np
import re
from typing import List, Dict, Any, Optional
import streamlit as st

from app.utils.logging import logger
from app.ingestion.dictionary_enrichment import LaborMarketDictionary, DataEnricher


class DataPreprocessor:
    """Handles data preprocessing, text normalization, and dictionary-based enrichment"""
    
    def __init__(self, use_dictionary: bool = True):
        self.stopwords = self._get_stopwords()
        self.domain_terms = self._get_domain_terms()
        self.use_dictionary = use_dictionary
        self.dictionary = None
        self.enricher = None
        
        # Load data dictionary if enabled
        if self.use_dictionary:
            try:
                self.dictionary = LaborMarketDictionary()
                self.enricher = DataEnricher(self.dictionary)
                logger.info("✓ Data dictionary loaded and ready", show_ui=True)
            except Exception as e:
                logger.warning(f"Could not load data dictionary: {str(e)}", show_ui=True)
                self.use_dictionary = False
    
    def _get_stopwords(self) -> set:
        """Get stopwords list (fallback if NLTK unavailable)"""
        try:
            from nltk.corpus import stopwords
            return set(stopwords.words('english'))
        except:
            # Basic stopwords fallback
            return {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which'
            }
    
    def _get_domain_terms(self) -> set:
        """Get domain-specific terms to preserve"""
        return {
            'data analysis', 'data analytics', 'patient care', 'customer service',
            'project management', 'quality assurance', 'business intelligence',
            'machine learning', 'artificial intelligence', 'computer science',
            'software development', 'web development', 'mobile development',
            'financial analysis', 'market research', 'human resources',
            'supply chain', 'operations management', 'sales management'
        }
    
    def preprocess_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main preprocessing pipeline with dictionary-based enrichment"""
        logger.info("Starting data preprocessing", show_ui=True)
        
        df_processed = df.copy()
        
        # 1. Handle multi-value columns
        df_processed = self._handle_multivalue_columns(df_processed)
        
        # 2. Normalize text fields
        df_processed = self._normalize_text_fields(df_processed)
        
        # 3. ENHANCED: Apply data dictionary enrichment
        if self.use_dictionary and self.enricher:
            logger.info("Applying data dictionary enrichment", show_ui=True)
            try:
                df_processed = self.enricher.enrich_dataframe(df_processed)
                
                # Get enrichment summary
                summary = self.enricher.get_enrichment_summary(df_processed)
                logger.info(f"✓ Enrichment complete: {summary}", show_ui=False)
                
                # Show key stats to user
                if 'industry_canonicalization' in summary:
                    perfect = summary['industry_canonicalization']['perfect_matches']
                    logger.info(f"  - Matched {perfect} industries to canonical terms", show_ui=True)
                
                if 'skill_extraction' in summary:
                    skills = summary['skill_extraction']['total_skills_extracted']
                    logger.info(f"  - Extracted {skills} skill references from tasks", show_ui=True)
                
            except Exception as e:
                logger.warning(f"Dictionary enrichment failed: {str(e)}", show_ui=True)
        
        # 4. Create combined search text (now includes enriched fields)
        df_processed = self._create_combined_text(df_processed)
        
        # 5. Handle missing values
        df_processed = self._handle_missing_values(df_processed)
        
        logger.info(f"✓ Preprocessing complete: {len(df_processed):,} rows, {len(df_processed.columns)} columns", 
                   show_ui=True)
        
        return df_processed
    
    def _handle_multivalue_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Split and normalize multi-value columns"""
        multi_value_cols = [
            'Detailed work activities',
            'Detailed job tasks',
            'Other known job titles for this occupation'
        ]
        
        for col in multi_value_cols:
            if col in df.columns:
                # Split by semicolon and clean
                df[f'{col}_list'] = df[col].fillna('').apply(self._split_and_clean)
                df[f'{col}_count'] = df[f'{col}_list'].apply(len)
                
                logger.debug(f"Processed multi-value column: {col}")
        
        return df
    
    def _split_and_clean(self, text: str) -> List[str]:
        """Split text by semicolon and clean each item"""
        if not text or pd.isna(text):
            return []
        
        items = [item.strip() for item in str(text).split(';')]
        items = [item for item in items if item and len(item) > 2]
        return list(set(items))  # Remove duplicates
    
    def _normalize_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize text in key fields"""
        text_columns = [
            'Industry title', 'ONET job title', 'BLS job title',
            'Job description', 'Detailed work activities', 'Detailed job tasks'
        ]
        
        for col in text_columns:
            if col in df.columns:
                df[f'{col}_normalized'] = df[col].fillna('').apply(self._normalize_text)
        
        return df
    
    def _normalize_text(self, text: str) -> str:
        """Normalize a single text field"""
        if not text or pd.isna(text):
            return ''
        
        text = str(text)
        
        # Lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep domain terms
        # Preserve hyphens and apostrophes
        text = re.sub(r'[^a-z0-9\s\-\']', ' ', text)
        
        # Remove extra spaces again
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _create_combined_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create combined searchable text field with enriched data"""
        text_fields = []
        
        # Priority fields for search
        priority_fields = [
            'ONET job title',
            'Job description',
            'Industry title',
            'Detailed work activities',
            'Detailed job tasks'
        ]
        
        # Add enriched fields if available (from data dictionary)
        enriched_fields = [
            'Industry_Canonical',  # Canonical industry name
            'Occupation_Major_Group',  # Occupation category
            'Canonical_Activities',  # Canonical work activities
            'Wage_Band',  # Wage classification
            'Task_Importance_Level'  # Task importance category
        ]
        
        # Collect all fields
        for field in priority_fields:
            if field in df.columns:
                text_fields.append(df[field].fillna(''))
        
        # Add enriched fields if they exist
        for field in enriched_fields:
            if field in df.columns:
                # Handle list fields (like Canonical_Activities)
                try:
                    # Check if this is a list field by examining first non-null value
                    sample_val = df[field].dropna().iloc[0] if len(df[field].dropna()) > 0 else None
                    if sample_val is not None and isinstance(sample_val, list):
                        text_fields.append(df[field].apply(lambda x: ' '.join(x) if isinstance(x, list) else str(x)))
                    else:
                        text_fields.append(df[field].fillna('').astype(str))
                except (IndexError, AttributeError):
                    # If we can't determine type, treat as string
                    text_fields.append(df[field].fillna('').astype(str))
        
        # Add extracted skills if available
        if 'Extracted_Skills' in df.columns:
            text_fields.append(
                df['Extracted_Skills'].apply(
                    lambda skills: ' '.join([s.get('skill', '') for s in skills]) if isinstance(skills, list) and len(skills) > 0 else ''
                )
            )
        
        # Combine with spaces
        df['combined_text'] = text_fields[0] if text_fields else ''
        for field in text_fields[1:]:
            df['combined_text'] = df['combined_text'] + ' ' + field
        
        # Normalize combined text
        df['combined_text_normalized'] = df['combined_text'].apply(self._normalize_text)
        
        logger.debug(f"Created combined text with {len(text_fields)} field types")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values appropriately"""
        # Fill numeric columns with 0
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col].fillna(0, inplace=True)
        
        # Fill text columns with empty string
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            df[col].fillna('', inplace=True)
        
        return df
    
    def tokenize_and_clean(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """Tokenize and clean text for analysis"""
        if not text or pd.isna(text):
            return []
        
        # Normalize
        text = self._normalize_text(text)
        
        # Simple tokenization
        tokens = text.split()
        
        # Remove stopwords if requested
        if remove_stopwords:
            tokens = [t for t in tokens if t not in self.stopwords and len(t) > 2]
        
        return tokens
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract key terms from text"""
        tokens = self.tokenize_and_clean(text, remove_stopwords=True)
        
        # Count frequency
        from collections import Counter
        token_counts = Counter(tokens)
        
        # Return top N
        return [word for word, count in token_counts.most_common(top_n)]
