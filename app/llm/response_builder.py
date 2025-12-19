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
    """High-level query processor that coordinates all components"""
    
    def __init__(
        self,
        response_builder: ResponseBuilder,
        retriever,  # HybridRetriever
        dataframe: pd.DataFrame
    ):
        self.response_builder = response_builder
        self.retriever = retriever
        self.dataframe = dataframe
    
    def process_query(
        self,
        query: str,
        k_results: int = 10
    ) -> Dict[str, Any]:
        """
        Main query processing function
        
        Returns:
            Complete response with answer and metadata
        """
        
        # Step 1: Retrieve relevant data
        retrieval_results = self.retriever.retrieve(query, k=k_results)
        
        # Step 2: Get routing info
        routing_info = retrieval_results.get('routing_info', {})
        
        # Step 3: Generate response
        answer = self.response_builder.generate_response(
            query=query,
            retrieval_results=retrieval_results,
            routing_info=routing_info
        )
        
        # Step 4: Generate CSV if requested
        csv_data = None
        if routing_info.get('strategy', {}).get('export_csv'):
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
