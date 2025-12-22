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

AVAILABLE DATA FIELDS:
The dataset has been enriched with a comprehensive labor market data dictionary that includes:
- Industry_Canonical: Standardized industry names (NAICS-based)
- Extracted_Skills: Skills automatically extracted from job task descriptions
- Skill_Count: Number of distinct skills identified for each occupation
- Canonical_Activities: Standardized work activity verbs
- Occupation_Major_Group: SOC-based occupation categories
- Wage_Band: Wage classifications (Entry/Mid/Senior/Executive Level)
- Task_Importance_Level: Task importance categories
- Required_Education: Typical education level required

DATASET STRUCTURE:
- Each row represents ONE TASK for an occupation
- To count tasks per occupation, count the number of rows for that occupation
- The "Task Count Analysis" section provides this information when available

IMPORTANT: When asked "What jobs..." or "Which occupations..." questions:
- If you see "OCCUPATION PATTERN MATCHING ANALYSIS" in the context, list ALL occupations shown
- DO NOT just pick the first occupation - list at least the top 10-15 as ranked
- Format as a clear numbered list with percentages/counts from the analysis
- Include the matching task count and percentage for each occupation
- Provide examples when available

IMPORTANT: When asked about skills or skill diversity:
- Use the Skill_Count field to identify occupations with diverse skill sets
- Reference the Extracted_Skills field for specific skill requirements
- The skill data comes from automated analysis of task descriptions using a labor market ontology

IMPORTANT: When asked about task counts or which occupations have the most tasks:
- Use the task_analysis section which counts rows (tasks) per occupation
- Each row is a task, so counting rows per occupation gives task counts
- The data IS available through the task count analysis

CRITICAL RULES:
- Base all answers strictly on the provided data
- If you use ANY external knowledge or make inferences, EXPLICITLY label them in a separate "External / Inferred Data" section
- Never hallucinate statistics or facts not in the data
- If data is insufficient, clearly state what's missing
- When presenting numbers, always cite the source (e.g., "Based on Employment field..." or "Based on Skill_Count field...")
- For skill-related queries, ALWAYS check if Skill_Count or Extracted_Skills data is provided

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
                
                # Add enriched fields if available
                if metadata.get('industry_canonical'):
                    context_parts.append(f"Canonical Industry: {metadata['industry_canonical']}")
                if metadata.get('occupation_major_group'):
                    context_parts.append(f"Occupation Group: {metadata['occupation_major_group']}")
                if metadata.get('skill_count'):
                    context_parts.append(f"Skill Count: {metadata['skill_count']} distinct skills")
                if metadata.get('extracted_skills'):
                    context_parts.append(f"Identified Skills: {metadata['extracted_skills']}")
                if metadata.get('wage_band'):
                    context_parts.append(f"Wage Band: {metadata['wage_band']}")
                
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
            
            # Skill Analysis (from data dictionary enrichment)
            if 'skill_analysis' in computational_results:
                context_parts.append("\n=== SKILL DIVERSITY ANALYSIS (from Data Dictionary) ===")
                skill_data = computational_results['skill_analysis']
                
                context_parts.append(f"\nOverall Statistics:")
                context_parts.append(f"- Total occupations analyzed: {skill_data.get('total_occupations', 0):,}")
                context_parts.append(f"- Occupations with identified skills: {skill_data.get('occupations_with_skills', 0):,}")
                context_parts.append(f"- Average skills per occupation: {skill_data.get('avg_skills_per_occupation', 0):.1f}")
                context_parts.append(f"- Maximum skills in any occupation: {skill_data.get('max_skills_in_occupation', 0):.0f}")
                
                if 'top_diverse_occupations' in skill_data:
                    context_parts.append(f"\nTop 20 Occupations by Skill Diversity (based on Skill_Count):")
                    for occupation, skill_count in list(skill_data['top_diverse_occupations'].items())[:20]:
                        context_parts.append(f"  - {occupation}: {skill_count:.0f} distinct skills")
                
                if 'industries_by_avg_skills' in skill_data:
                    context_parts.append(f"\nIndustries by Average Skill Requirements:")
                    for industry, avg_skills in list(skill_data['industries_by_avg_skills'].items())[:10]:
                        context_parts.append(f"  - {industry}: {avg_skills:.1f} avg skills")
            
            # Task Analysis (task counts per occupation)
            if 'task_analysis' in computational_results:
                context_parts.append("\n=== TASK COUNT ANALYSIS ===")
                task_data = computational_results['task_analysis']
                
                context_parts.append(f"\nDataset Structure:")
                context_parts.append(f"- Total tasks in dataset: {task_data.get('total_tasks', 0):,}")
                context_parts.append(f"- Total occupations: {task_data.get('total_occupations', 0):,}")
                context_parts.append(f"- Average tasks per occupation: {task_data.get('avg_tasks_per_occupation', 0):.1f}")
                context_parts.append(f"- Maximum tasks for any occupation: {task_data.get('max_tasks_for_occupation', 0):,}")
                context_parts.append(f"- Minimum tasks for any occupation: {task_data.get('min_tasks_for_occupation', 0):,}")
                
                context_parts.append(f"\nNOTE: Each row in the dataset represents one task. The number of tasks per occupation")
                context_parts.append(f"is determined by counting how many rows (tasks) belong to each occupation.")
                
                if 'top_occupations_by_task_count' in task_data:
                    context_parts.append(f"\nTop 20 Occupations by Number of Tasks:")
                    for occupation, task_count in list(task_data['top_occupations_by_task_count'].items())[:20]:
                        context_parts.append(f"  - {occupation}: {task_count:,} tasks")
                
                if 'top_industries_by_task_count' in task_data:
                    context_parts.append(f"\nTop Industries by Total Task Count:")
                    for industry, task_count in list(task_data['top_industries_by_task_count'].items())[:10]:
                        context_parts.append(f"  - {industry}: {task_count:,} tasks")
            
            # Occupation Pattern Analysis (for "what jobs" queries)
            if 'occupation_pattern_analysis' in computational_results:
                context_parts.append("\n=== OCCUPATION PATTERN MATCHING ANALYSIS ===")
                pattern_data = computational_results['occupation_pattern_analysis']
                
                context_parts.append(f"\nQuery Pattern Analysis:")
                context_parts.append(f"- Total occupations analyzed: {pattern_data.get('total_occupations_analyzed', 0)}")
                context_parts.append(f"- Occupations with matching tasks: {pattern_data.get('occupations_with_matches', 0)}")
                context_parts.append(f"- Match criteria: Contains action verbs AND object keywords")
                
                context_parts.append(f"\nAction verbs searched: {', '.join(pattern_data.get('action_verbs_used', [])[:8])}...")
                context_parts.append(f"Object keywords searched: {', '.join(pattern_data.get('object_keywords_used', [])[:8])}...")
                
                if 'top_occupations' in pattern_data:
                    context_parts.append(f"\nTOP OCCUPATIONS RANKED BY MATCHING TASKS:")
                    context_parts.append(f"(Showing occupations where tasks match the pattern)")
                    context_parts.append(f"")
                    
                    for rank, (occupation, scores) in enumerate(pattern_data['top_occupations'], 1):
                        context_parts.append(
                            f"{rank}. {occupation}"
                        )
                        context_parts.append(
                            f"   - Matching tasks: {scores['matching_tasks']}/{scores['total_tasks']} "
                            f"({scores['percentage']:.1f}%)"
                        )
                        if scores.get('examples'):
                            context_parts.append(f"   - Example tasks:")
                            for example in scores['examples'][:2]:
                                context_parts.append(f"      • {example}")
                    
                    context_parts.append(f"\nIMPORTANT: List ALL {len(pattern_data['top_occupations'])} occupations shown above, ")
                    context_parts.append(f"not just the first one. These are ranked by the percentage of matching tasks.")
        
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
