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
    
    def _validate_and_correct_totals(self, answer: str, retrieval_results: Dict[str, Any]) -> str:
        """
        Validate and correct occupation/industry summary totals in LLM response
        
        Problem: LLM sometimes ignores instructions and shows wrong totals
        Solution: Find and replace incorrect totals with correct ones from computational_results
        """
        computational_results = retrieval_results.get('computational_results', {})
        
        # Check if this is a summary with a grand total (occupation, industry, or task query)
        if 'total_employment' not in computational_results:
            logger.debug("No total_employment in computational_results - skipping validation", show_ui=False)
            return answer  # No correction needed
        
        correct_total = computational_results['total_employment']
        logger.info(f"🔍 Validating totals - correct total from data: {correct_total:.2f}k", show_ui=False)
        
        # v4.8.8 FIX: Determine query type based on ACTUAL DATA returned, not just metadata
        # Priority: Check for actual data structures first (occupation_employment, industry_employment)
        # Then fall back to metadata fields (total_occupations, total_tasks, total_industries)
        
        is_occupation = False
        is_industry = False
        is_task = False
        count = 0
        entity_type = "items"
        
        # Check for occupation employment data (highest priority for occupation queries)
        if 'occupation_employment' in computational_results:
            occ_data = computational_results['occupation_employment']
            if isinstance(occ_data, pd.DataFrame) and not occ_data.empty:
                is_occupation = True
                count = len(occ_data)
                entity_type = "occupations"
                logger.debug(f"Detected occupation query from occupation_employment data: {count} rows", show_ui=False)
        
        # Check for industry employment data (highest priority for industry queries)
        elif 'industry_employment' in computational_results:
            ind_data = computational_results['industry_employment']
            if isinstance(ind_data, pd.DataFrame) and not ind_data.empty:
                is_industry = True
                count = len(ind_data)
                entity_type = "industries"
                logger.debug(f"Detected industry query from industry_employment data: {count} rows", show_ui=False)
        
        # Check for industry proportions data
        elif 'industry_proportions' in computational_results:
            ind_prop = computational_results['industry_proportions']
            if isinstance(ind_prop, dict) and 'industries' in ind_prop:
                is_industry = True
                count = len(ind_prop['industries']) if isinstance(ind_prop['industries'], list) else ind_prop.get('total_industries', 0)
                entity_type = "industries"
                logger.debug(f"Detected industry query from industry_proportions data: {count} items", show_ui=False)
        
        # Fall back to metadata fields (less reliable)
        elif 'total_tasks' in computational_results:
            is_task = True
            count = computational_results['total_tasks']
            entity_type = "tasks"
            logger.debug(f"Detected task query from total_tasks metadata: {count} tasks", show_ui=False)
        
        elif 'total_occupations' in computational_results:
            is_occupation = True
            count = computational_results['total_occupations']
            entity_type = "occupations"
            logger.debug(f"Detected occupation query from total_occupations metadata: {count} occupations", show_ui=False)
        
        elif 'total_industries' in computational_results:
            is_industry = True
            count = computational_results['total_industries']
            entity_type = "industries"
            logger.debug(f"Detected industry query from total_industries metadata: {count} industries", show_ui=False)
        
        # v4.8.8: If still no type detected, skip validation
        if not (is_occupation or is_industry or is_task):
            logger.debug("Not a recognized summary type - skipping validation", show_ui=False)
            return answer
        
        logger.info(f"🔍 Validating {entity_type} summary with {count} {entity_type}", show_ui=False)
        
        # Pattern to find total employment lines (various formats)
        import re
        
        # Patterns the LLM might use for totals
        patterns = [
            (r'Total Employment:?\s*[\*\*]*([0-9,]+\.?\d*)\s*thousand\s*workers?\s*\(?.*?\)?\s*across\s*(\d+)\s*' + entity_type, 'full'),
            (r'Total Employment:?\s*[\*\*]*([0-9,]+\.?\d*)\s*thousand\s*workers?', 'basic'),
            (r'Total Employment:?\s*[\*\*]*([0-9,]+\.?\d*)\s*thousand', 'short'),
            (r'Total:?\s*[\*\*]*([0-9,]+\.?\d*)\s*thousand\s*workers?', 'total_basic'),
            (r'Total:?\s*[\*\*]*([0-9,]+\.?\d*)\s*k', 'total_k'),
        ]
        
        # Check if answer contains a total line
        found_incorrect_total = False
        reported_total = None
        matched_pattern = None
        
        for pattern, pattern_name in patterns:
            match = re.search(pattern, answer, re.IGNORECASE)
            if match:
                reported_total_str = match.group(1).replace(',', '')
                try:
                    reported_total = float(reported_total_str)
                    matched_pattern = pattern
                    
                    logger.info(f"🔍 Found total in LLM output (pattern: {pattern_name}): {reported_total:.2f}k", show_ui=False)
                    
                    # Allow small rounding differences (±0.1%)
                    diff_pct = abs(reported_total - correct_total) / correct_total * 100
                    diff_abs = abs(reported_total - correct_total)
                    
                    if diff_pct > 0.1:  # More than 0.1% difference = wrong
                        found_incorrect_total = True
                        logger.warning(
                            f"🚨 LLM REPORTED WRONG TOTAL: {reported_total:.2f}k (correct: {correct_total:.2f}k, "
                            f"difference: {diff_abs:.2f}k = {diff_pct:.1f}%)",
                            show_ui=True
                        )
                        break
                    else:
                        logger.info(f"✅ Total is correct (difference: {diff_pct:.3f}%)", show_ui=False)
                        return answer  # Total is correct, no need to fix
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing total from pattern {pattern_name}: {e}", show_ui=False)
                    continue
        
        if reported_total is None:
            logger.warning(f"⚠️ No total found in LLM output - will append correct total", show_ui=False)
        
        if found_incorrect_total or reported_total is None:
            # Create correct total line
            correct_line = f"Total Employment: {correct_total:,.2f} thousand workers across {count} {entity_type}"
            
            if found_incorrect_total and matched_pattern:
                # Try to replace the incorrect total line
                answer = re.sub(matched_pattern, correct_line, answer, count=1, flags=re.IGNORECASE)
                logger.info(f"✅ CORRECTED TOTAL: Replaced {reported_total:.2f}k with {correct_total:.2f}k", show_ui=True)
            else:
                # Append correct total
                answer += f"\n\n**{correct_line}**"
                logger.info(f"✅ APPENDED CORRECT TOTAL: {correct_total:.2f}k across {count} {entity_type}", show_ui=True)
        
        return answer
    
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
            
            # DYNAMIC TOKEN ALLOCATION: Determine max_tokens based on query type and result size
            # Task-level queries need more tokens for comprehensive tables
            max_tokens = config.LLM_MAX_TOKENS  # Default: 4000
            
            query_lower = query.lower()
            is_task_query = any(phrase in query_lower for phrase in [
                'specific tasks', 'what tasks', 'which tasks', 'task descriptions',
                'tasks that', 'tasks involve', 'list tasks', 'show tasks', 'describe tasks'
            ])
            
            # Check result size
            semantic_results_count = len(retrieval_results.get('semantic_results', []))
            
            if is_task_query:
                # Task queries with many results need higher token limit
                if semantic_results_count > 50:
                    max_tokens = config.LLM_MAX_TOKENS_TASK_QUERY  # 8000 for large task tables
                    logger.info(f"📊 Task query with {semantic_results_count} results: Using max_tokens={max_tokens}", show_ui=False)
                elif semantic_results_count > 20:
                    max_tokens = 6000  # Medium task tables
                    logger.info(f"📊 Task query with {semantic_results_count} results: Using max_tokens={max_tokens}", show_ui=False)
                else:
                    max_tokens = config.LLM_MAX_TOKENS  # Small task queries: 4000
            elif semantic_results_count > 30:
                # Occupation queries with many results
                max_tokens = config.LLM_MAX_TOKENS_OCCUPATION_QUERY  # 4000
                logger.info(f"📊 Occupation query with {semantic_results_count} results: Using max_tokens={max_tokens}", show_ui=False)
            
            # Call OpenAI API with dynamic token allocation
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.templates.get_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=max_tokens  # Dynamic based on query type and result size
            )
            
            answer = response.choices[0].message.content
            
            # Handle case where content is None
            if answer is None:
                logger.warning("OpenAI returned None content", show_ui=False)
                return "I apologize, but I wasn't able to generate a response. Please try again."
            
            # ARITHMETIC VALIDATION: Validate LLM output against ground truth
            if 'arithmetic_validator' in retrieval_results:
                validator = retrieval_results['arithmetic_validator']
                
                # Get expected values from computational results
                expected_values = {}
                for key, value in retrieval_results['computational_results'].items():
                    if key.endswith('_verified'):
                        expected_values[key] = value
                
                # Validate LLM output
                discrepancies = validator.validate_llm_output(
                    llm_text=answer,
                    expected_values=expected_values
                )
                
                # Store discrepancies for UI display
                retrieval_results['arithmetic_discrepancies'] = discrepancies
                
                if discrepancies:
                    logger.warning(
                        f"⚠️ ARITHMETIC DISCREPANCIES DETECTED: {len(discrepancies)} error(s) found",
                        show_ui=True
                    )
                    
                    # Log each discrepancy
                    for disc in discrepancies:
                        logger.warning(
                            f"  - {disc.operation.upper()} ({disc.severity}): "
                            f"Computed={disc.computed_value:.2f}, LLM={disc.llm_value:.2f}, "
                            f"Diff={disc.difference_pct:.1f}%",
                            show_ui=False
                        )
                else:
                    logger.info("✅ ARITHMETIC VALIDATION: All values verified correct", show_ui=False)
            
            # LEGACY: Also run old validation for backwards compatibility
            # This will be deprecated once full arithmetic validation is proven
            answer = self._validate_and_correct_totals(answer, retrieval_results)
            
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
        
        # NEW v4.8.8: Initialize universal CSV generator
        from app.llm.csv_generator import UniversalCSVGenerator
        self.csv_generator = UniversalCSVGenerator()
        logger.info("✓ v4.8.8: Universal CSV generator initialized", show_ui=False)
        
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
        
        # Step 1: Retrieve relevant data
        # Use enhanced query for vector search, but pass original for pattern matching
        # CRITICAL: Pattern matching should ONLY run on original user queries
        retrieval_results = self.retriever.retrieve(
            enhanced_query, 
            k=k_results,
            original_query=query  # Pass original query for pattern matching
        )
        
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
        
        # Step 4: Generate CSV data - NEW v4.8.8: UNIVERSAL for ALL queries
        # OLD: Conditional logic, csv_data was None for most queries
        # NEW: Always generate CSV using 3-tier strategy
        
        csv_data = self.csv_generator.generate(
            query=query,
            semantic_results=retrieval_results.get('semantic_results', []),
            computational_results=retrieval_results.get('computational_results', {}),
            routing_info=routing_info
        )
        
        # Validate CSV was generated (should NEVER be None with fallback)
        if csv_data is None or csv_data.empty:
            logger.error(
                "⚠️ BUG: CSV generation returned None/empty - this should not happen with fallback!",
                show_ui=False
            )
            # Emergency fallback
            csv_data = pd.DataFrame({
                'Query': [query],
                'Error': ['CSV generation failed unexpectedly'],
                'Timestamp': [pd.Timestamp.now().isoformat()]
            })
        
        logger.info(
            f"✅ v4.8.8: CSV ready - {len(csv_data)} rows × {len(csv_data.columns)} columns",
            show_ui=False
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
