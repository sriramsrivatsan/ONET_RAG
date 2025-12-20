"""
Labor Market Data Dictionary Loader and Enrichment Module
Provides canonical term mapping, semantic enhancement, and data quality improvements
"""
import yaml
import os
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from app.utils.logging import logger


class LaborMarketDictionary:
    """Loads and provides access to the labor market data dictionary"""
    
    def __init__(self, dictionary_path: str = None):
        if dictionary_path is None:
            # Try multiple possible locations for the dictionary file
            possible_paths = [
                # Default: project_root/data/labor_market_dictionary.yaml
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    'data',
                    'labor_market_dictionary.yaml'
                ),
                # Fallback 1: relative to current working directory
                os.path.join(os.getcwd(), 'data', 'labor_market_dictionary.yaml'),
                # Fallback 2: relative to app directory
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    'data',
                    'labor_market_dictionary.yaml'
                ),
                # Fallback 3: in same directory as this file
                os.path.join(
                    os.path.dirname(__file__),
                    'labor_market_dictionary.yaml'
                )
            ]
            
            # Find the first path that exists
            dictionary_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    dictionary_path = path
                    break
            
            # If none found, use the default (will error later with helpful message)
            if dictionary_path is None:
                dictionary_path = possible_paths[0]
        
        self.dictionary_path = dictionary_path
        self.dictionary = None
        self._industry_lookup = {}
        self._occupation_lookup = {}
        self._skill_lookup = {}
        self._activity_verbs = {}
        
        self.load_dictionary()
    
    def load_dictionary(self) -> bool:
        """Load the YAML data dictionary"""
        try:
            # Log the path we're trying to load from
            abs_path = os.path.abspath(self.dictionary_path)
            logger.debug(f"Loading dictionary from: {abs_path}", show_ui=False)
            
            with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                self.dictionary = yaml.safe_load(f)
            
            # Build lookup indices
            self._build_indices()
            
            logger.info(f"✓ Loaded labor market dictionary", show_ui=True)
            return True
            
        except FileNotFoundError:
            abs_path = os.path.abspath(self.dictionary_path)
            cwd = os.getcwd()
            logger.error(f"Dictionary file not found!", show_ui=True)
            logger.error(f"  Looking for: {abs_path}", show_ui=True)
            logger.error(f"  Current dir: {cwd}", show_ui=True)
            logger.error(f"  Please ensure data/labor_market_dictionary.yaml exists in project root", show_ui=True)
            return False
        except Exception as e:
            logger.error(f"Error loading dictionary: {str(e)}", show_ui=True)
            return False
    
    def _build_indices(self):
        """Build lookup indices for fast access"""
        
        # Build industry lookup (canonical name + synonyms)
        if 'industries' in self.dictionary and 'sectors' in self.dictionary['industries']:
            for sector in self.dictionary['industries']['sectors']:
                canonical = sector['canonical']
                
                # Add canonical name
                self._industry_lookup[canonical.lower()] = sector
                
                # Add synonyms
                for synonym in sector.get('synonyms', []):
                    self._industry_lookup[synonym.lower()] = sector
                
                # Add keywords
                for keyword in sector.get('keywords', []):
                    if keyword.lower() not in self._industry_lookup:
                        self._industry_lookup[keyword.lower()] = sector
        
        # Build occupation lookup
        if 'occupations' in self.dictionary and 'major_groups' in self.dictionary['occupations']:
            for group in self.dictionary['occupations']['major_groups']:
                canonical = group['canonical']
                
                # Add canonical name
                self._occupation_lookup[canonical.lower()] = group
                
                # Add synonyms
                for synonym in group.get('synonyms', []):
                    self._occupation_lookup[synonym.lower()] = group
        
        # Build activity verb mapping
        if 'work_activities' in self.dictionary and 'categories' in self.dictionary['work_activities']:
            for category in self.dictionary['work_activities']['categories']:
                for verb_group in category.get('canonical_verbs', []):
                    if isinstance(verb_group, dict):
                        for canonical, synonyms in verb_group.items():
                            self._activity_verbs[canonical] = synonyms
                            for synonym in synonyms:
                                if synonym.lower() not in self._activity_verbs:
                                    self._activity_verbs[synonym.lower()] = canonical
        
        # Build skill lookup
        if 'task_skill_mappings' in self.dictionary:
            for category_name, skills in self.dictionary['task_skill_mappings'].items():
                if isinstance(skills, list):
                    for skill in skills:
                        if isinstance(skill, dict) and 'skill' in skill:
                            skill_name = skill['skill']
                            self._skill_lookup[skill_name.lower()] = skill
                            
                            # Add canonical terms
                            for term in skill.get('canonical_terms', []):
                                self._skill_lookup[term.lower()] = skill
        
        logger.info(f"Built indices: {len(self._industry_lookup)} industries, "
                   f"{len(self._occupation_lookup)} occupations, "
                   f"{len(self._skill_lookup)} skills", show_ui=False)
    
    def canonicalize_industry(self, industry_text: str, threshold: float = 0.85) -> Dict[str, Any]:
        """
        Map industry text to canonical form with fuzzy matching
        
        Args:
            industry_text: Raw industry text
            threshold: Fuzzy matching threshold (0-1)
            
        Returns:
            Dict with canonical name, match score, and sector info
        """
        if not industry_text or pd.isna(industry_text):
            return {'canonical': None, 'match_score': 0, 'sector_info': None}
        
        industry_lower = industry_text.lower().strip()
        
        # Exact match
        if industry_lower in self._industry_lookup:
            sector = self._industry_lookup[industry_lower]
            return {
                'canonical': sector['canonical'],
                'match_score': 1.0,
                'sector_info': sector,
                'naics_code': sector.get('naics_code')
            }
        
        # Fuzzy match
        best_match = None
        best_score = 0
        
        for key, sector in self._industry_lookup.items():
            score = fuzz.ratio(industry_lower, key) / 100.0
            if score > best_score and score >= threshold:
                best_score = score
                best_match = sector
        
        if best_match:
            return {
                'canonical': best_match['canonical'],
                'match_score': best_score,
                'sector_info': best_match,
                'naics_code': best_match.get('naics_code')
            }
        
        # No match - return original
        return {
            'canonical': industry_text,
            'match_score': 0,
            'sector_info': None,
            'naics_code': None
        }
    
    def extract_skills_from_tasks(self, task_text: str) -> List[Dict[str, Any]]:
        """
        Extract skills implied by task descriptions
        
        Args:
            task_text: Task description text
            
        Returns:
            List of skill dictionaries with confidence scores
        """
        if not task_text or pd.isna(task_text):
            return []
        
        task_lower = task_text.lower()
        found_skills = []
        
        # Check all skills in dictionary
        for skill_name, skill_data in self._skill_lookup.items():
            # Check if any related tasks match
            for related_task in skill_data.get('related_tasks', []):
                if related_task.lower() in task_lower:
                    confidence = 0.9  # High confidence for task match
                    found_skills.append({
                        'skill': skill_data.get('skill', skill_name),
                        'confidence': confidence,
                        'matched_task': related_task,
                        'category': self._get_skill_category(skill_data.get('skill', skill_name))
                    })
                    break
        
        # Remove duplicates
        seen = set()
        unique_skills = []
        for skill in found_skills:
            if skill['skill'] not in seen:
                seen.add(skill['skill'])
                unique_skills.append(skill)
        
        return unique_skills
    
    def extract_canonical_activities(self, activity_text: str) -> List[str]:
        """
        Extract and canonicalize work activities
        
        Args:
            activity_text: Raw activity description
            
        Returns:
            List of canonical activity verbs
        """
        if not activity_text or pd.isna(activity_text):
            return []
        
        activity_lower = activity_text.lower()
        canonical_activities = []
        
        # Find matching verbs
        for verb, data in self._activity_verbs.items():
            if isinstance(data, list):
                # This is a canonical verb with synonyms
                for synonym in data:
                    if synonym.lower() in activity_lower:
                        if verb not in canonical_activities:
                            canonical_activities.append(verb)
                        break
            elif isinstance(data, str):
                # This is a synonym pointing to canonical
                if verb in activity_lower:
                    if data not in canonical_activities:
                        canonical_activities.append(data)
        
        return canonical_activities
    
    def get_occupation_metadata(self, occupation_title: str) -> Dict[str, Any]:
        """
        Get metadata for an occupation
        
        Args:
            occupation_title: Occupation title text
            
        Returns:
            Dict with occupation metadata
        """
        if not occupation_title or pd.isna(occupation_title):
            return {}
        
        occupation_lower = occupation_title.lower().strip()
        
        # Try exact match
        if occupation_lower in self._occupation_lookup:
            return self._occupation_lookup[occupation_lower]
        
        # Try fuzzy match
        best_match = None
        best_score = 0
        threshold = 0.75
        
        for key, occupation in self._occupation_lookup.items():
            score = fuzz.ratio(occupation_lower, key) / 100.0
            if score > best_score and score >= threshold:
                best_score = score
                best_match = occupation
        
        return best_match if best_match else {}
    
    def _get_skill_category(self, skill_name: str) -> str:
        """Determine skill category"""
        if not 'supplementary' in self.dictionary:
            return 'Unknown'
        
        skill_categories = self.dictionary['supplementary'].get('skill_categories', [])
        
        for category in skill_categories:
            if skill_name in category.get('skills', []):
                return category['category']
        
        return 'Unknown'
    
    def get_wage_band(self, hourly_wage: float) -> str:
        """
        Classify wage into bands
        
        Args:
            hourly_wage: Hourly wage value
            
        Returns:
            Wage band label
        """
        if pd.isna(hourly_wage) or hourly_wage <= 0:
            return 'Unknown'
        
        if 'supplementary' not in self.dictionary:
            return 'Unknown'
        
        wage_bands = self.dictionary['supplementary'].get('wage_bands', [])
        
        for band in wage_bands:
            range_min, range_max = band['range']
            if range_min <= hourly_wage < range_max:
                return band['band']
        
        return 'Executive Level'  # Above highest band
    
    def get_task_importance_level(self, importance_score: float) -> str:
        """
        Classify task importance
        
        Args:
            importance_score: Numeric importance score
            
        Returns:
            Importance level label
        """
        if pd.isna(importance_score):
            return 'Unknown'
        
        if 'supplementary' not in self.dictionary:
            return 'Unknown'
        
        importance_levels = self.dictionary['supplementary'].get('task_importance', [])
        
        for level in importance_levels:
            score_min, score_max = level['score_range']
            if score_min <= importance_score < score_max:
                return level['level']
        
        return 'Unknown'
    
    def enhance_query(self, query: str) -> Dict[str, Any]:
        """
        Enhance a user query with dictionary knowledge
        
        Args:
            query: User query text
            
        Returns:
            Dict with query enhancements
        """
        enhancements = {
            'original_query': query,
            'expanded_terms': [],
            'suggested_filters': [],
            'canonical_terms': []
        }
        
        query_lower = query.lower()
        
        # Find mentioned industries
        for industry_key, sector in self._industry_lookup.items():
            if industry_key in query_lower:
                enhancements['expanded_terms'].append({
                    'type': 'industry',
                    'original': industry_key,
                    'canonical': sector['canonical'],
                    'synonyms': sector.get('synonyms', [])
                })
        
        # Find mentioned skills
        for skill_key, skill_data in self._skill_lookup.items():
            if skill_key in query_lower:
                enhancements['expanded_terms'].append({
                    'type': 'skill',
                    'original': skill_key,
                    'canonical': skill_data.get('skill', skill_key),
                    'related_tasks': skill_data.get('related_tasks', [])
                })
        
        return enhancements


class DataEnricher:
    """Enriches labor market data using the data dictionary"""
    
    def __init__(self, dictionary: LaborMarketDictionary):
        self.dictionary = dictionary
    
    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich a dataframe with canonical terms and derived fields
        
        Args:
            df: Input dataframe
            
        Returns:
            Enriched dataframe with additional columns
        """
        logger.info("Starting data enrichment with data dictionary", show_ui=True)
        
        df_enriched = df.copy()
        
        # Canonicalize industries
        if 'Industry title' in df_enriched.columns:
            logger.info("Canonicalizing industry names", show_ui=True)
            industry_data = df_enriched['Industry title'].apply(
                lambda x: self.dictionary.canonicalize_industry(x)
            )
            df_enriched['Industry_Canonical'] = industry_data.apply(lambda x: x['canonical'])
            df_enriched['Industry_Match_Score'] = industry_data.apply(lambda x: x['match_score'])
            df_enriched['NAICS_Code'] = industry_data.apply(lambda x: x.get('naics_code'))
        
        # Extract skills from tasks
        if 'Detailed job tasks' in df_enriched.columns:
            logger.info("Extracting skills from task descriptions", show_ui=True)
            df_enriched['Extracted_Skills'] = df_enriched['Detailed job tasks'].apply(
                lambda x: self.dictionary.extract_skills_from_tasks(x)
            )
            df_enriched['Skill_Count'] = df_enriched['Extracted_Skills'].apply(len)
        
        # Extract canonical activities
        if 'Detailed work activities' in df_enriched.columns:
            logger.info("Canonicalizing work activities", show_ui=True)
            df_enriched['Canonical_Activities'] = df_enriched['Detailed work activities'].apply(
                lambda x: self.dictionary.extract_canonical_activities(x)
            )
            df_enriched['Activity_Count'] = df_enriched['Canonical_Activities'].apply(len)
        
        # Add occupation metadata
        if 'ONET job title' in df_enriched.columns:
            logger.info("Adding occupation metadata", show_ui=True)
            occupation_meta = df_enriched['ONET job title'].apply(
                lambda x: self.dictionary.get_occupation_metadata(x)
            )
            df_enriched['Occupation_Major_Group'] = occupation_meta.apply(
                lambda x: x.get('canonical', 'Unknown')
            )
            df_enriched['Occupation_SOC_Code'] = occupation_meta.apply(
                lambda x: x.get('code', 'Unknown')
            )
            df_enriched['Required_Education'] = occupation_meta.apply(
                lambda x: x.get('education_level', 'Unknown')
            )
        
        # Add wage bands
        if 'Hourly wage' in df_enriched.columns:
            logger.info("Classifying wage bands", show_ui=True)
            df_enriched['Wage_Band'] = df_enriched['Hourly wage'].apply(
                lambda x: self.dictionary.get_wage_band(x)
            )
        
        # Add task importance levels
        if 'Task importance' in df_enriched.columns:
            logger.info("Classifying task importance levels", show_ui=True)
            df_enriched['Task_Importance_Level'] = df_enriched['Task importance'].apply(
                lambda x: self.dictionary.get_task_importance_level(x)
            )
        
        logger.info(f"✓ Data enrichment complete. Added {len(df_enriched.columns) - len(df.columns)} new columns", 
                   show_ui=True)
        
        return df_enriched
    
    def get_enrichment_summary(self, df_enriched: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics about the enrichment
        
        Args:
            df_enriched: Enriched dataframe
            
        Returns:
            Summary statistics dictionary
        """
        summary = {}
        
        # Industry canonicalization stats
        if 'Industry_Match_Score' in df_enriched.columns:
            summary['industry_canonicalization'] = {
                'perfect_matches': (df_enriched['Industry_Match_Score'] == 1.0).sum(),
                'fuzzy_matches': ((df_enriched['Industry_Match_Score'] < 1.0) & 
                                 (df_enriched['Industry_Match_Score'] > 0)).sum(),
                'no_matches': (df_enriched['Industry_Match_Score'] == 0).sum(),
                'avg_match_score': df_enriched['Industry_Match_Score'].mean()
            }
        
        # Skill extraction stats
        if 'Skill_Count' in df_enriched.columns:
            summary['skill_extraction'] = {
                'total_skills_extracted': df_enriched['Skill_Count'].sum(),
                'avg_skills_per_row': df_enriched['Skill_Count'].mean(),
                'rows_with_skills': (df_enriched['Skill_Count'] > 0).sum()
            }
        
        # Activity canonicalization stats
        if 'Activity_Count' in df_enriched.columns:
            summary['activity_canonicalization'] = {
                'total_activities': df_enriched['Activity_Count'].sum(),
                'avg_activities_per_row': df_enriched['Activity_Count'].mean()
            }
        
        return summary


# Convenience functions
def load_dictionary() -> LaborMarketDictionary:
    """Load the labor market dictionary"""
    return LaborMarketDictionary()


def enrich_data(df: pd.DataFrame, dictionary: LaborMarketDictionary = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Enrich dataframe with data dictionary
    
    Args:
        df: Input dataframe
        dictionary: Optional pre-loaded dictionary
        
    Returns:
        Tuple of (enriched_df, summary_stats)
    """
    if dictionary is None:
        dictionary = load_dictionary()
    
    enricher = DataEnricher(dictionary)
    df_enriched = enricher.enrich_dataframe(df)
    summary = enricher.get_enrichment_summary(df_enriched)
    
    return df_enriched, summary
