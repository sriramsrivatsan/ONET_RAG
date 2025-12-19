"""
Prompt templates for LLM interaction
"""
from typing import Dict, List, Any


class PromptTemplates:
    """Prompt templates for different query types"""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get system prompt for labor market analyst"""
        return """You are a Labor Market Data Analyst assistant specialized in analyzing ONET labor market data.

Your role is to:
1. Provide accurate, data-grounded insights about occupations, industries, tasks, and employment
2. Clearly distinguish between information directly from the dataset and any external knowledge
3. Present findings clearly with appropriate structure (tables, bullets, or prose as needed)
4. Cite specific data points when making claims
5. Be transparent about limitations and data gaps

CRITICAL RULES:
- Base all answers strictly on the provided data
- If you use ANY external knowledge or make inferences, EXPLICITLY label them in a separate "External / Inferred Data" section
- Never hallucinate statistics or facts not in the data
- If data is insufficient, clearly state what's missing
- When presenting numbers, always cite the source (e.g., "Based on Employment field...")

Your responses should be:
- Accurate and grounded in data
- Clear and well-structured
- Appropriately detailed
- Honest about uncertainties"""
    
    @staticmethod
    def format_retrieval_context(
        semantic_results: List[Dict[str, Any]],
        computational_results: Dict[str, Any]
    ) -> str:
        """Format retrieved context for LLM"""
        
        context_parts = []
        
        # Add semantic search results
        if semantic_results:
            context_parts.append("=== SEMANTIC SEARCH RESULTS ===\n")
            for i, result in enumerate(semantic_results[:10], 1):
                score = result.get('score', 0)
                text = result.get('text', '')[:500]  # Truncate long texts
                metadata = result.get('metadata', {})
                
                context_parts.append(f"\n[Document {i}] (Relevance: {score:.2f})")
                if metadata.get('onet_job_title'):
                    context_parts.append(f"Occupation: {metadata['onet_job_title']}")
                if metadata.get('industry_title'):
                    context_parts.append(f"Industry: {metadata['industry_title']}")
                context_parts.append(f"Content: {text}\n")
        
        # Add computational results
        if computational_results:
            context_parts.append("\n=== COMPUTATIONAL ANALYSIS ===\n")
            
            # Counts
            if 'counts' in computational_results:
                context_parts.append("\nCounts:")
                for key, value in computational_results['counts'].items():
                    context_parts.append(f"- {key}: {value:,}")
            
            # Totals
            if 'totals' in computational_results:
                context_parts.append("\nTotals:")
                for key, value in computational_results['totals'].items():
                    context_parts.append(f"- {key}: {value:,.2f}")
            
            # Averages
            if 'averages' in computational_results:
                context_parts.append("\nAverages:")
                for key, value in computational_results['averages'].items():
                    context_parts.append(f"- {key}: {value:,.2f}")
            
            # Grouped results
            if 'grouped' in computational_results:
                context_parts.append("\nGrouped Analysis:")
                for group_type, values in computational_results['grouped'].items():
                    context_parts.append(f"\n{group_type}:")
                    for name, val in list(values.items())[:10]:  # Top 10
                        context_parts.append(f"  - {name}: {val:,.2f}")
            
            # Top N
            if 'top_n' in computational_results:
                context_parts.append("\nTop Results:")
                for key, values in computational_results['top_n'].items():
                    context_parts.append(f"\n{key}:")
                    for name, val in values.items():
                        context_parts.append(f"  - {name}: {val:,.2f}")
        
        return '\n'.join(context_parts)
    
    @staticmethod
    def create_analysis_prompt(
        query: str,
        context: str,
        routing_info: Dict[str, Any]
    ) -> str:
        """Create complete analysis prompt"""
        
        intent = routing_info.get('intent', 'hybrid')
        
        prompt = f"""Based on the labor market data provided below, answer the following question:

QUESTION: {query}

QUERY TYPE: {intent.upper()}

DATA CONTEXT:
{context}

INSTRUCTIONS:
1. Answer the question using ONLY the data provided above
2. Be specific and cite relevant statistics
3. If you need to make inferences or use external knowledge, create a separate section labeled "External / Inferred Data"
4. If the data is insufficient to fully answer the question, clearly state what information is missing
5. Present your answer in a clear, structured format
6. Include tables or lists if they help clarity

ANSWER:"""
        
        return prompt
    
    @staticmethod
    def create_csv_generation_prompt(
        query: str,
        data_summary: str
    ) -> str:
        """Create prompt for CSV data generation"""
        
        return f"""Based on the query and data summary below, generate a structured dataset that can be exported to CSV.

QUERY: {query}

DATA SUMMARY:
{data_summary}

INSTRUCTIONS:
1. Identify the key dimensions and metrics requested
2. Structure the data in a tabular format with clear column headers
3. Provide actual data points from the analysis
4. Format numbers appropriately
5. Return ONLY the data in a format that can be parsed into CSV

Respond with a structured table format."""
    
    @staticmethod
    def create_digital_documents_prompt() -> str:
        """Specialized prompt for digital document queries"""
        
        return """Based on the labor market data, analyze which jobs involve creating digital documents.

DEFINITION: Digital document creation includes:
- Spreadsheets (Excel, Google Sheets)
- Word processing documents (Word, Google Docs)
- PDFs and formatted documents
- Photo and image creation/editing
- Video creation and editing
- Computer programs and code
- Presentations
- Any content created using a computer

EXCLUDE: Jobs that only READ or VIEW digital documents (e.g., order takers who just read forms)

Analyze:
1. Which occupations require digital document creation?
2. What specific tasks involve creating digital documents?
3. What is the total employment in these occupations?
4. How much time per week is spent on digital document tasks?
5. Which industries have high concentrations of digital document creators?

Provide specific data points and statistics."""
    
    @staticmethod
    def create_ai_agent_analysis_prompt() -> str:
        """Specialized prompt for AI agent solution analysis"""
        
        return """Analyze the potential impact of a customer service AI agent based on the labor market data.

AI AGENT CAPABILITIES:
- Automate customer interactions
- Deliver personalized experiences
- Understand customer needs
- Answer questions
- Resolve issues
- Recommend products and services
- Work across web, mobile, and point-of-sale
- Integrate with voice and video

Analyze:
1. Which occupations could benefit from this agent?
2. What specific tasks could the agent help with?
3. How much time per week is currently spent on these tasks?
4. What time savings could be achieved?
5. Which occupations could save the most time?
6. What is the potential dollar value of time savings?
7. What recommendations would encourage adoption?

Provide detailed analysis with specific numbers and calculations."""
