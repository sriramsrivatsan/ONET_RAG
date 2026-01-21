"""
OpenAI integration and response building
"""
from openai import OpenAI
from typing import Dict, List, Any, Optional
import pandas as pd
import streamlit as st

from app.llm.prompt_templates import PromptTemplates
from app.utils.logging import logger
from app.utils.config import config


class ResponseBuilder:
    """Builds responses using OpenAI LLM"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.templates = PromptTemplates()
    
    def generate_response(
        self,
        query: str,
        retrieval_results: Dict[str, Any],
        routing_info: Dict[str, Any]
    ) -> str:
        """Generate response using LLM"""
        
        try:
            # Format context from retrieval results
            context = self.templates.format_retrieval_context(
                semantic_results=retrieval_results.get('semantic_results', []),
                computational_results=retrieval_results.get('computational_results', {})
            )
            
            # Create prompt
            user_prompt = self.templates.create_analysis_prompt(
                query=query,
                context=context,
                routing_info=routing_info
            )
            
            # Call OpenAI API with new client
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.templates.get_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS
            )
            
            answer = response.choices[0].message.content
            
            # Handle case where content is None
            if answer is None:
                logger.warning("OpenAI returned None content", show_ui=False)
                return "I apologize, but I wasn't able to generate a response. Please try again."
            
            logger.debug(f"Generated response: {len(answer)} characters")
            
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}", show_ui=True)
            return f"Error generating response: {str(e)}"
    
    def generate_enhanced_response(
        self,
        query: str,
        context: str = "",
        use_web_search: bool = False
    ) -> str:
        """Generate enhanced response with optional web search
        
        Args:
            query: The enhancement query/prompt
            context: Optional context to include
            use_web_search: Whether to enable web search (requires Claude API)
            
        Returns:
            Enhanced response text
        """
        
        try:
            # Build messages
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant specialized in labor market analysis and workforce intelligence."},
                {"role": "user", "content": query}
            ]
            
            # Add context if provided
            if context:
                messages.insert(1, {"role": "system", "content": f"Context: {context}"})
            
            # Call OpenAI API
            # Note: OpenAI doesn't have built-in web search, so we'll provide comprehensive responses
            # based on training data and general knowledge
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=0.7,  # Slightly higher for creative enhancement
                max_tokens=1500  # More tokens for comprehensive enhancement
            )
            
            answer = response.choices[0].message.content
            
            if answer is None:
                logger.warning("OpenAI returned None for enhancement", show_ui=False)
                return "Unable to generate enhanced response. Please try again."
            
            logger.info("Generated enhanced response successfully")
            
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced response: {str(e)}", show_ui=True)
            return f"Error generating enhanced response: {str(e)}"
    
    def generate_csv_data(
        self,
        query: str,
        dataframe: pd.DataFrame,
        routing_info: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
        """Generate CSV data based on query"""
        
        try:
            # Create summary of data
            data_summary = self._create_data_summary(dataframe, routing_info)
            
            # Create prompt
            prompt = self.templates.create_csv_generation_prompt(
                query=query,
                data_summary=data_summary
            )
            
            # For now, return the filtered dataframe directly
            # In production, you might want LLM to format it
            return dataframe
            
        except Exception as e:
            logger.error(f"Failed to generate CSV: {str(e)}", show_ui=True)
            return None
    
    def _create_data_summary(
        self,
        df: pd.DataFrame,
        routing_info: Dict[str, Any]
    ) -> str:
        """Create a summary of the dataframe for LLM"""
        
        summary_parts = []
        
        summary_parts.append(f"Total rows: {len(df)}")
        summary_parts.append(f"Columns: {', '.join(df.columns.tolist())}")
        
        # Key statistics
        if 'Employment' in df.columns:
            summary_parts.append(f"Total employment: {df['Employment'].sum():,.0f}")
        
        if 'Industry title' in df.columns:
            top_industries = df['Industry title'].value_counts().head(5)
            summary_parts.append(f"Top industries: {', '.join(top_industries.index.tolist())}")
        
        if 'ONET job title' in df.columns:
            summary_parts.append(f"Unique occupations: {df['ONET job title'].nunique()}")
        
        return '\n'.join(summary_parts)
    
    def enhance_cluster_labels(
        self,
        cluster_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Use LLM to generate better cluster labels"""
        
        enhanced_labels = {}
        
        try:
            for cluster_type, data in cluster_data.items():
                cluster_labels = data.get('cluster_labels', {})
                
                for cluster_id, label in cluster_labels.items():
                    # Create prompt to enhance label
                    prompt = f"""Given this cluster label from labor market data:

Cluster: {label}

Generate a concise, descriptive label (3-5 words) that captures the essence of this cluster.
Respond with ONLY the enhanced label, nothing else."""
                    
                    try:
                        response = self.client.chat.completions.create(
                            model=config.LLM_MODEL,
                            messages=[
                                {"role": "system", "content": "You are a labor market data analyst."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                            max_tokens=50
                        )
                        
                        enhanced_label = response.choices[0].message.content.strip()
                        enhanced_labels[f"{cluster_type}_{cluster_id}"] = enhanced_label
                        
                    except:
                        enhanced_labels[f"{cluster_type}_{cluster_id}"] = label
            
            return enhanced_labels
            
        except Exception as e:
            logger.error(f"Failed to enhance cluster labels: {str(e)}", show_ui=False)
            return {}


class QueryProcessor:
    """High-level query processor that coordinates all components with dictionary enhancement"""
    
    def __init__(
        self,
        response_builder: ResponseBuilder,
        retriever,  # HybridRetriever
        dataframe: pd.DataFrame,
        dictionary=None  # LaborMarketDictionary (optional)
    ):
        self.response_builder = response_builder
        self.retriever = retriever
        self.dataframe = dataframe
        self.dictionary = dictionary
        
        # Load dictionary if not provided
        if self.dictionary is None:
            try:
                from app.ingestion.dictionary_enrichment import LaborMarketDictionary
                self.dictionary = LaborMarketDictionary()
                logger.info("✓ Query processor loaded data dictionary", show_ui=False)
            except Exception as e:
                logger.warning(f"Could not load data dictionary for queries: {str(e)}", show_ui=False)
    
    def process_query(
        self,
        query: str,
        k_results: int = 10
    ) -> Dict[str, Any]:
        """
        Main query processing function with dictionary-based query enhancement
        
        Returns:
            Complete response with answer and metadata
        """
        
        # Step 0: Enhance query with dictionary knowledge
        enhanced_query = query
        query_enhancements = {}
        
        if self.dictionary:
            try:
                query_enhancements = self.dictionary.enhance_query(query)
                
                # Add expanded terms to query context
                if query_enhancements.get('expanded_terms'):
                    expanded_terms = []
                    for term in query_enhancements['expanded_terms']:
                        if term['type'] == 'industry':
                            expanded_terms.extend(term.get('synonyms', []))
                        elif term['type'] == 'skill':
                            expanded_terms.extend([t.lower() for t in term.get('related_tasks', [])])
                    
                    if expanded_terms:
                        enhanced_query = query + " " + " ".join(expanded_terms[:5])  # Add top 5 expanded terms
                        logger.debug(f"Enhanced query with {len(expanded_terms)} terms", show_ui=False)
                
            except Exception as e:
                logger.warning(f"Query enhancement failed: {str(e)}", show_ui=False)
        
        # Step 1: Retrieve relevant data (use enhanced query)
        retrieval_results = self.retriever.retrieve(enhanced_query, k=k_results)
        
        # Add original query to results
        retrieval_results['original_query'] = query
        retrieval_results['enhanced_query'] = enhanced_query
        retrieval_results['query_enhancements'] = query_enhancements
        
        # Step 2: Get routing info
        routing_info = retrieval_results.get('routing_info', {})
        
        # Step 3: Generate response
        answer = self.response_builder.generate_response(
            query=query,
            retrieval_results=retrieval_results,
            routing_info=routing_info
        )
        
        # Step 4: Generate CSV data
        csv_data = None
        
        # Check if query requests industry grouping
        query_lower = query.lower()
        query_wants_industry = (
            'by industry' in query_lower or 
            'per industry' in query_lower or
            ('csv' in query_lower and 'industry' in query_lower and 'industries' in query_lower)
        )
        
        # Check if query wants savings analysis
        query_wants_savings = any(phrase in query_lower for phrase in [
            'saving', 'save', 'roi', 'dollar', 'cost'
        ])
        
        # Priority 1: Savings analysis (if requested)
        if query_wants_savings and retrieval_results.get('computational_results', {}).get('savings_analysis'):
            savings_df = pd.DataFrame(retrieval_results['computational_results']['savings_analysis'])
            csv_data = savings_df
            logger.info(f"Using savings_analysis for CSV ({len(csv_data)} occupations)", show_ui=False)
        # Priority 2: Industry employment
        elif query_wants_industry:
            if retrieval_results.get('computational_results', {}).get('industry_employment') is not None:
                csv_data = retrieval_results['computational_results']['industry_employment']
                logger.info(f"Using industry_employment for CSV ({len(csv_data)} industries)", show_ui=False)
            elif retrieval_results.get('computational_results', {}).get('industry_proportions') is not None:
                ind_props = retrieval_results['computational_results']['industry_proportions']
                if 'industries' in ind_props:
                    csv_data = pd.DataFrame(ind_props['industries'])
                    logger.info(f"Using industry_proportions for CSV ({len(csv_data)} industries)", show_ui=False)
        # Priority 3: Occupation employment
        else:
            if retrieval_results.get('computational_results', {}).get('occupation_employment') is not None:
                csv_data = retrieval_results['computational_results']['occupation_employment']
                logger.info(f"Using occupation_employment for CSV ({len(csv_data)} occupations)", show_ui=False)
            elif routing_info.get('strategy', {}).get('export_csv'):
                filtered_df = retrieval_results.get('filtered_dataframe')
                if filtered_df is not None and not filtered_df.empty:
                    csv_data = self.response_builder.generate_csv_data(
                        query=query,
                        dataframe=filtered_df,
                        routing_info=routing_info
                    )
        
        # Package response
        response = {
            'answer': answer,
            'query': query,
            'routing_info': routing_info,
            'metadata': {
                'semantic_results_count': len(retrieval_results.get('semantic_results', [])),
                'computational_results': retrieval_results.get('computational_results', {}),
                'filtered_rows': len(retrieval_results.get('filtered_dataframe', [])) if retrieval_results.get('filtered_dataframe') is not None else 0
            },
            'csv_data': csv_data,
            'retrieval_results': retrieval_results  # For debugging
        }
        
        return response
