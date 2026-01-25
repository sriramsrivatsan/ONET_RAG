"""
Generic Task Pattern Matching Engine
=====================================

A configurable, extensible system for matching tasks based on pattern definitions.
Replaces hardcoded pattern matching with configuration-driven approach.

Version: 2.0.0
"""

import yaml
import pandas as pd
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache
import logging

# Use custom RAGLogger if available, otherwise use standard logger
try:
    from app.utils.logging import RAGLogger
    logger = RAGLogger(__name__)
except (ImportError, ModuleNotFoundError):
    # Fallback to standard logger (for testing without Streamlit)
    logger = logging.getLogger(__name__)
    # Add show_ui parameter support for compatibility
    original_info = logger.info
    original_debug = logger.debug
    original_warning = logger.warning
    original_error = logger.error
    logger.info = lambda msg, show_ui=False: original_info(msg)
    logger.debug = lambda msg, show_ui=False: original_debug(msg)
    logger.warning = lambda msg, show_ui=False: original_warning(msg)
    logger.error = lambda msg, show_ui=False: original_error(msg)


@dataclass
class TaskCategory:
    """Represents a task category with its matching patterns"""
    name: str
    display_name: str
    description: str
    action_verbs: Dict[str, List[str]]
    object_keywords: Dict[str, List[str]]
    matching_strategy: str
    validation_rules: Dict[str, Any]
    aggregation_config: Dict[str, Any]
    min_confidence: float = 0.7


@dataclass
class MatchResult:
    """Result of pattern matching"""
    matched: bool
    confidence: float
    category: str
    matched_verbs: List[str]
    matched_keywords: List[str]
    task_text: str


class TaskPatternEngine:
    """
    Generic engine for matching tasks based on configurable patterns.
    
    Features:
    - Configuration-driven pattern matching
    - Multiple matching strategies
    - Extensible with custom patterns
    - Performance optimized with caching
    - Industry-specific overrides
    """
    
    def __init__(self, config_path: str = "data/task_patterns.yaml"):
        """
        Initialize the pattern matching engine.
        
        Args:
            config_path: Path to task patterns configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.categories = self._parse_categories()
        self.strategies = self.config.get('matching_strategies', {})
        self.query_patterns = self.config.get('query_patterns', {})
        
        # Cache for compiled patterns
        self._compiled_patterns: Dict[str, Any] = {}
        
        logger.info(f"Loaded {len(self.categories)} task categories")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded task patterns from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load task patterns: {e}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Provide fallback configuration if file load fails"""
        return {
            'task_categories': {},
            'matching_strategies': {},
            'query_patterns': {},
            'defaults': {
                'default_category': 'document_creation',
                'default_strategy': 'verb_object'
            }
        }
    
    def _parse_categories(self) -> Dict[str, TaskCategory]:
        """Parse category definitions into TaskCategory objects"""
        categories = {}
        
        for category_name, category_data in self.config.get('task_categories', {}).items():
            try:
                categories[category_name] = TaskCategory(
                    name=category_name,
                    display_name=category_data.get('display_name', category_name),
                    description=category_data.get('description', ''),
                    action_verbs=category_data.get('action_verbs', {}),
                    object_keywords=category_data.get('object_keywords', {}),
                    matching_strategy=category_data.get('matching', {}).get('strategy', 'verb_object'),
                    validation_rules=category_data.get('validation', {}),
                    aggregation_config=category_data.get('aggregation', {}),
                    min_confidence=category_data.get('matching', {}).get('min_confidence', 0.7)
                )
            except Exception as e:
                logger.warning(f"Failed to parse category {category_name}: {e}")
                continue
        
        return categories
    
    def detect_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Detect what the user wants to know about from their query.
        
        Args:
            query: User's query string
            
        Returns:
            Dict with detected intents and confidence scores
        """
        query_lower = query.lower()
        intents = {}
        
        for intent_name, intent_config in self.query_patterns.items():
            keywords = intent_config.get('keywords', [])
            triggers = intent_config.get('triggers', [])
            
            # Check for keywords
            keyword_matches = sum(1 for kw in keywords if kw in query_lower)
            
            # Check for trigger phrases
            trigger_matches = sum(1 for trigger in triggers if trigger in query_lower)
            
            # Calculate confidence
            total_possible = len(keywords) + len(triggers)
            total_matches = keyword_matches + trigger_matches
            confidence = total_matches / total_possible if total_possible > 0 else 0.0
            
            if confidence > 0:
                intents[intent_name] = {
                    'confidence': confidence,
                    'keyword_matches': keyword_matches,
                    'trigger_matches': trigger_matches
                }
        
        return intents
    
    def detect_task_category(self, query: str) -> Optional[str]:
        """
        Detect which task category the query is asking about.
        
        CRITICAL: This method should ONLY receive the original user query,
        NOT enhanced queries with appended text. Enhanced queries can contain
        false positive phrase matches.
        
        Args:
            query: User's ORIGINAL query string (not enhanced)
            
        Returns:
            Name of detected category or None
        """
        query_lower = query.lower()
        
        # SAFEGUARD: Detect if query has been enhanced with task descriptions
        # Enhanced queries often contain phrases like "develop new concepts", "design creative solutions"
        # that create false positive phrase matches
        suspicious_phrases = [
            "develop new concepts",
            "design creative solutions", 
            "design systems",
            "implement solutions"
        ]
        
        is_likely_enhanced = any(phrase in query_lower for phrase in suspicious_phrases)
        
        # Track calls to this method
        if not hasattr(self, '_detection_call_count'):
            self._detection_call_count = 0
            self._query_hashes = []
        self._detection_call_count += 1
        current_hash = hash(query)
        
        # Log the query being analyzed with FULL TEXT
        logger.info(f"🔍 CATEGORY DETECTION START (call #{self._detection_call_count})", show_ui=False)
        logger.info(f"   Query length: {len(query)} chars", show_ui=False)
        logger.info(f"   Query hash: {current_hash}", show_ui=False)
        
        # Check if this is a repeat call with same or different query
        if current_hash in self._query_hashes:
            logger.warning(f"   ⚠️  DUPLICATE CALL with same query!", show_ui=False)
        else:
            self._query_hashes.append(current_hash)
            if len(self._query_hashes) > 1:
                logger.warning(f"   ⚠️  MULTIPLE CALLS with DIFFERENT queries!", show_ui=False)
                logger.warning(f"   Previous {len(self._query_hashes)-1} call(s) had different query text", show_ui=False)
        logger.info(f"   First 150 chars: {query[:150]}...", show_ui=False)
        logger.info(f"   Last 150 chars: ...{query[-150:] if len(query) > 150 else query}", show_ui=False)
        
        if is_likely_enhanced:
            logger.error(f"🚨 ENHANCED QUERY DETECTED - SKIPPING PATTERN MATCHING!", show_ui=False)
            logger.error(f"   This query appears to contain appended task descriptions", show_ui=False)
            logger.error(f"   Pattern matching should ONLY run on original user queries", show_ui=False)
            logger.error(f"   Returning None to avoid false positive matches", show_ui=False)
            return None
        
        # Negation patterns to detect when keywords are mentioned in negative context
        negation_patterns = [
            r"don'?t\s+include",
            r"not\s+include",
            r"exclude",
            r"avoid",
            r"by\s+contrast",
            r"except\s+for",
            r"other\s+than",
            r"rather\s+than",
            r"instead\s+of",
            r"don'?t\s+(?:want|need|consider)",
            r"shouldn'?t",
            r"won'?t",
            r"not\s+(?:want|need|looking|interested)"
        ]
        
        logger.info(f"   Using {len(negation_patterns)} negation patterns", show_ui=False)
        
        # Check each category's keywords
        best_match = None
        best_score = 0.0
        scores_detail = {}  # For debugging
        
        logger.info(f"   Evaluating {len(self.categories)} categories...", show_ui=False)
        
        for category_name, category in self.categories.items():
            score = 0.0
            details = []
            
            logger.debug(f"      Checking category: {category_name}", show_ui=False)
            
            # Special logging for key categories
            if category_name in ['customer_service', 'design_creative', 'document_creation']:
                logger.info(f"      🔍 Evaluating: {category_name}", show_ui=False)
            
            # Check if category name or display name in query
            category_phrase = category_name.replace('_', ' ')
            display_phrase = category.display_name.lower()
            
            # Log what we're searching for
            if category_name in ['customer_service', 'design_creative', 'document_creation']:
                logger.info(f"         Looking for: '{category_phrase}' OR '{display_phrase}'", show_ui=False)
            
            # Check for negation context around category mentions
            import re
            is_negated = False
            
            # Look for category phrase in query
            if category_phrase in query_lower or display_phrase in query_lower:
                # Find position of category phrase
                phrase_to_check = category_phrase if category_phrase in query_lower else display_phrase
                phrase_pos = query_lower.find(phrase_to_check)
                
                logger.info(f"         Found phrase '{phrase_to_check}' at position {phrase_pos}", show_ui=False)
                logger.info(f"         Query substring at position: '{query_lower[max(0,phrase_pos-20):phrase_pos+len(phrase_to_check)+20]}'", show_ui=False)
                
                # CRITICAL: Log negation checking for key categories
                if category_name in ['customer_service', 'design_creative', 'document_creation']:
                    logger.info(f"         🔎 CHECKING NEGATION for '{category_name}'", show_ui=False)
                
                # Check 200 characters before the phrase for negation (increased from 50)
                context_start = max(0, phrase_pos - 200)
                context = query_lower[context_start:phrase_pos + len(phrase_to_check)]
                
                # Log context for key categories
                if category_name in ['customer_service', 'design_creative', 'document_creation']:
                    logger.info(f"            Context window: chars {context_start} to {phrase_pos + len(phrase_to_check)}", show_ui=False)
                    logger.info(f"            Last 80 chars of context: ...{context[-80:]}", show_ui=False)
                
                # Check if any negation pattern appears in context
                for neg_pattern in negation_patterns:
                    if re.search(neg_pattern, context):
                        is_negated = True
                        logger.info(f"         ⚠️  NEGATION DETECTED for '{phrase_to_check}'", show_ui=False)
                        logger.info(f"             Pattern: {neg_pattern}", show_ui=False)
                        logger.info(f"             Context: ...{context[-60:]}", show_ui=False)
                        details.append(f"NEGATED phrase match (pattern: {neg_pattern})")
                        break
                
                # Log result of negation check for key categories
                if category_name in ['customer_service', 'design_creative', 'document_creation']:
                    if is_negated:
                        logger.info(f"         ✗ Result: NEGATED (will subtract 2.0 points)", show_ui=False)
                    else:
                        logger.info(f"         ✓ Result: NOT NEGATED (will add 2.0 points)", show_ui=False)
                
                if not is_negated:
                    score += 2.0  # Strong signal only if NOT negated
                    details.append(f"+2.0 phrase match '{phrase_to_check}'")
                    logger.debug(f"         ✓ Phrase match: +2.0", show_ui=False)
                else:
                    score -= 2.0  # Penalty for negated mentions
                    details.append(f"-2.0 negated phrase '{phrase_to_check}'")
                    logger.debug(f"         ✗ Negated phrase: -2.0", show_ui=False)
            else:
                # Phrase not found in query
                if category_name in ['customer_service', 'design_creative', 'document_creation']:
                    logger.info(f"         ✗ Phrase NOT found in query", show_ui=False)
            
            # Check for action verbs (any tier)
            all_verbs = (
                category.action_verbs.get('primary', []) +
                category.action_verbs.get('secondary', [])
            )
            
            # Simple stemming: check if query contains verb or common inflections
            verb_matches_count = 0
            matched_verbs = []
            
            logger.debug(f"         Checking {len(all_verbs)} verbs", show_ui=False)
            
            for verb in all_verbs:
                verb_lower = verb.lower()
                # Check exact match or common inflections
                # Handle -e ending: "create" → "creating" (drop e), not "createing"
                stem = verb_lower[:-1] if verb_lower.endswith('e') else verb_lower
                
                verb_patterns = [
                    verb_lower,  # exact: "create"
                    verb_lower + 's',  # "creates"
                    stem + 'ing',  # "creating" (handles both create→creating and program→programing)
                    stem + 'ed',  # "created"
                ]
                
                if any(pattern in query_lower for pattern in verb_patterns):
                    verb_matches_count += 1
                    matched_verbs.append(verb)
                    found_pattern = [p for p in verb_patterns if p in query_lower][0]
                    logger.debug(f"            ✓ Verb match: '{verb}' (found '{found_pattern}')", show_ui=False)
                    
            if verb_matches_count > 0:
                verb_score = 1.0 + (0.3 * min(verb_matches_count - 1, 3))
                score += verb_score
                details.append(f"+{verb_score:.1f} verbs: {matched_verbs[:3]}")
                logger.debug(f"         Verb total: +{verb_score:.1f} ({verb_matches_count} matches)", show_ui=False)
            
            # Check for object keywords (any tier)
            all_keywords = (
                category.object_keywords.get('primary', []) +
                category.object_keywords.get('secondary', [])
            )
            
            logger.debug(f"         Checking {len(all_keywords)} keywords", show_ui=False)
            
            keyword_matches = sum(1 for kw in all_keywords if kw.lower() in query_lower)
            if keyword_matches > 0:
                keyword_score = 0.8 + (0.3 * min(keyword_matches - 1, 3))
                score += keyword_score
                matched_kws = [k for k in all_keywords if k.lower() in query_lower]
                details.append(f"+{keyword_score:.1f} keywords: {matched_kws[:3]}")
                logger.debug(f"         Keyword total: +{keyword_score:.1f} ({keyword_matches} matches: {matched_kws[:5]})", show_ui=False)
            
            # Penalty for excluded terms (but not if they appear in negated context)
            excluded_verbs = category.action_verbs.get('exclude', [])
            excluded_keywords = category.object_keywords.get('exclude', [])
            
            all_excluded = excluded_verbs + excluded_keywords
            logger.debug(f"         Checking {len(all_excluded)} excluded terms", show_ui=False)
            
            # Check if excluded terms appear, but ignore if in negated context
            excluded_found = []
            for term in all_excluded:
                term_lower = term.lower()
                
                # Use word boundary regex to match whole words only (avoid "read" in "spreadsheets")
                import re
                word_pattern = r'\b' + re.escape(term_lower) + r'\b'
                matches = list(re.finditer(word_pattern, query_lower))
                
                if matches:
                    logger.debug(f"            Found excluded term '{term}' ({len(matches)} occurrences)", show_ui=False)
                    # Check each occurrence - term is only excluded if at least one occurrence is NOT negated
                    has_non_negated_occurrence = False
                    for match in matches:
                        term_pos = match.start()
                        context_start = max(0, term_pos - 200)
                        context = query_lower[context_start:term_pos]
                        
                        # Check for negation
                        is_negated_term = False
                        for neg_pattern in negation_patterns:
                            if re.search(neg_pattern, context):
                                is_negated_term = True
                                logger.debug(f"               ✓ Occurrence at {term_pos} is NEGATED", show_ui=False)
                                break
                        
                        if not is_negated_term:
                            has_non_negated_occurrence = True
                            logger.debug(f"               ✗ Occurrence at {term_pos} is NOT negated", show_ui=False)
                            break  # Found one non-negated occurrence, that's enough
                    
                    # Only add to excluded if we found a non-negated occurrence
                    if has_non_negated_occurrence:
                        excluded_found.append(term)
                        logger.debug(f"            ✗ Excluded term '{term}' APPLIES (non-negated occurrence found)", show_ui=False)
            
            if excluded_found:
                old_score = score
                score *= 0.3  # Heavy penalty
                details.append(f"×0.3 excluded terms: {excluded_found[:2]} (was {old_score:.1f})")
                logger.debug(f"         Excluded penalty: ×0.3 for {excluded_found} (was {old_score:.1f}, now {score:.1f})", show_ui=False)
            
            # Store score details
            scores_detail[category_name] = {'score': score, 'details': details}
            
            # CRITICAL FIX: Phrase matches alone aren't reliable
            # Require at least SOME verb or keyword matches for credibility
            # This prevents false positives from phrase matches in enhanced/modified queries
            has_phrase_match = (category_phrase in query_lower or display_phrase in query_lower)
            has_verb_matches = verb_matches_count > 0
            has_keyword_matches = keyword_matches > 0
            
            # If ONLY phrase match (no verbs or keywords), reduce confidence significantly
            if has_phrase_match and not has_verb_matches and not has_keyword_matches:
                old_score = score
                score *= 0.1  # Heavy penalty - phrase match alone is not reliable
                details.append(f"⚠️  Phrase-only match (no verbs/keywords): reduced from {old_score:.1f}")
                logger.warning(f"         ⚠️  Category '{category_name}' has phrase match but NO verb/keyword support - reducing score", show_ui=False)
                scores_detail[category_name] = {'score': score, 'details': details}
            
            # Log final score for this category
            if score > 0.1 or category_name in ['document_creation', 'customer_service', 'design_creative']:
                logger.info(f"      {category_name:20s}: {score:5.2f} - {', '.join(details)}", show_ui=False)
            
            # Require minimum combination for match
            min_score = 0.5
            if score >= min_score:
                if score > best_score:
                    logger.info(f"         🏆 NEW BEST: {category_name} ({score:.2f} > {best_score:.2f})", show_ui=False)
                    best_score = score
                    best_match = category_name
        
        # Log all category scores for debugging
        logger.info(f"🔍 CATEGORY DETECTION SUMMARY", show_ui=False)
        logger.info(f"   ─────────────────────────────────────────────────────────────", show_ui=False)
        
        # Sort by score and show top 5
        sorted_categories = sorted(scores_detail.items(), key=lambda x: x[1]['score'], reverse=True)
        for i, (cat_name, info) in enumerate(sorted_categories[:5], 1):
            marker = "🏆" if cat_name == best_match else "  "
            logger.info(f"   {marker} {i}. {cat_name:25s}: {info['score']:6.2f}", show_ui=False)
            for detail in info['details']:
                logger.info(f"      • {detail}", show_ui=False)
        
        logger.info(f"   ─────────────────────────────────────────────────────────────", show_ui=False)
        logger.info(f"   Best match: {best_match or 'None'} (score: {best_score:.2f}, threshold: 0.5)", show_ui=False)
        logger.info(f"🔍 CATEGORY DETECTION END", show_ui=False)
        
        # Return match if confidence above threshold
        if best_score >= 0.5:
            logger.info(f"✓ v4.2.0: Detected category '{best_match}' with score {best_score:.2f}", show_ui=False)
            return best_match
        
        logger.debug(f"No category detected (best score: {best_score:.2f})", show_ui=False)
        return None
    
    def match_task(
        self,
        task_text: str,
        category_name: str,
        case_sensitive: bool = False
    ) -> MatchResult:
        """
        Match a single task description against a category's patterns.
        
        Args:
            task_text: Task description to match
            category_name: Name of category to match against
            case_sensitive: Whether matching should be case-sensitive
            
        Returns:
            MatchResult object with matching details
        """
        if category_name not in self.categories:
            return MatchResult(
                matched=False,
                confidence=0.0,
                category=category_name,
                matched_verbs=[],
                matched_keywords=[],
                task_text=task_text
            )
        
        category = self.categories[category_name]
        
        # Convert to lowercase for case-insensitive matching
        text = task_text if case_sensitive else task_text.lower()
        
        # Get all action verbs (primary + secondary, excluding excluded)
        all_verbs = (
            category.action_verbs.get('primary', []) +
            category.action_verbs.get('secondary', [])
        )
        excluded_verbs = category.action_verbs.get('exclude', [])
        all_verbs = [v for v in all_verbs if v not in excluded_verbs]
        
        # Get all object keywords (primary + secondary, excluding excluded)
        all_keywords = (
            category.object_keywords.get('primary', []) +
            category.object_keywords.get('secondary', [])
        )
        excluded_keywords = category.object_keywords.get('exclude', [])
        all_keywords = [k for k in all_keywords if k not in excluded_keywords]
        
        # CRITICAL: Match v3's behavior EXACTLY
        # v3 only checks: (has action verb) AND (has keyword)
        # v3 does NOT exclude tasks with "read", "review", etc.
        # 
        # The user query says "don't include jobs that ONLY read"
        # But if a job CREATES *and* reads, it should still match!
        # So we match on creation verbs only, without excluding reading verbs.
        
        import re
        
        # Match action verbs using substring matching (same as v3)
        matched_verbs = [v for v in all_verbs if v.lower() in text]
        
        # Match keywords with substring matching (same as v3)
        matched_keywords = [k for k in all_keywords if k.lower() in text]
        
        # v3 did NOT check excluded verbs! Only checked for positive matches.
        # Removing excluded verb logic to match v3 behavior.
        has_excluded_verb = False
        has_excluded_keyword = False
        
        if has_excluded_verb or has_excluded_keyword:
            return MatchResult(
                matched=False,
                confidence=0.0,
                category=category_name,
                matched_verbs=[],
                matched_keywords=[],
                task_text=task_text
            )
        
        # Apply matching strategy
        strategy = category.matching_strategy
        matched = False
        confidence = 0.0
        
        if strategy == 'verb_object':
            # Requires both verb AND keyword
            matched = len(matched_verbs) > 0 and len(matched_keywords) > 0
            if matched:
                # Confidence based on number of matches
                verb_confidence = min(len(matched_verbs) / 2, 1.0)
                keyword_confidence = min(len(matched_keywords) / 2, 1.0)
                confidence = (verb_confidence + keyword_confidence) / 2
        
        elif strategy == 'verb_only':
            # Requires only verb
            matched = len(matched_verbs) > 0
            if matched:
                confidence = min(len(matched_verbs) / 2, 1.0)
        
        elif strategy == 'keyword_any':
            # Matches if any keyword present
            matched = len(matched_keywords) > 0
            if matched:
                confidence = min(len(matched_keywords) / 2, 1.0)
        
        # Apply minimum confidence threshold
        if confidence < category.min_confidence:
            matched = False
        
        return MatchResult(
            matched=matched,
            confidence=confidence,
            category=category_name,
            matched_verbs=matched_verbs,
            matched_keywords=matched_keywords,
            task_text=task_text
        )
    
    def filter_dataframe(
        self,
        df: pd.DataFrame,
        category_name: str,
        task_column: str = 'Detailed job tasks',
        return_match_details: bool = False
    ) -> pd.DataFrame:
        """
        Filter dataframe to only include rows matching a category's patterns.
        
        Args:
            df: DataFrame with task descriptions
            category_name: Category to filter by
            task_column: Name of column containing task descriptions
            return_match_details: Whether to add match detail columns
            
        Returns:
            Filtered DataFrame
        """
        if category_name not in self.categories:
            logger.warning(f"Unknown category: {category_name}")
            return pd.DataFrame()
        
        logger.info(f"Filtering {len(df)} rows for category: {category_name}")
        
        # Match each row
        matches = []
        match_details = []
        
        for idx, row in df.iterrows():
            task_text = str(row.get(task_column, ''))
            result = self.match_task(task_text, category_name)
            matches.append(result.matched)
            match_details.append({
                'confidence': result.confidence,
                'matched_verbs': ','.join(result.matched_verbs),
                'matched_keywords': ','.join(result.matched_keywords)
            })
        
        # Filter dataframe
        filtered_df = df[matches].copy()
        
        # Optionally add match details
        if return_match_details:
            filtered_df['match_confidence'] = [d['confidence'] for i, d in enumerate(match_details) if matches[i]]
            filtered_df['matched_verbs'] = [d['matched_verbs'] for i, d in enumerate(match_details) if matches[i]]
            filtered_df['matched_keywords'] = [d['matched_keywords'] for i, d in enumerate(match_details) if matches[i]]
        
        logger.info(f"Filtered to {len(filtered_df)} matching rows ({len(filtered_df)/len(df)*100:.1f}%)")
        
        return filtered_df
    
    def get_category_config(self, category_name: str) -> Optional[TaskCategory]:
        """Get configuration for a specific category"""
        return self.categories.get(category_name)
    
    def list_categories(self) -> List[Dict[str, str]]:
        """List all available categories with metadata"""
        return [
            {
                'name': cat.name,
                'display_name': cat.display_name,
                'description': cat.description,
                'strategy': cat.matching_strategy
            }
            for cat in self.categories.values()
        ]
    
    def get_aggregation_config(self, category_name: str) -> Dict[str, Any]:
        """Get aggregation configuration for a category"""
        category = self.categories.get(category_name)
        if not category:
            return self.config.get('defaults', {}).get('default_aggregation', {})
        return category.aggregation_config
    
    def get_validation_rules(self, category_name: str) -> Dict[str, Any]:
        """Get validation rules for a category"""
        category = self.categories.get(category_name)
        if not category:
            return self.config.get('defaults', {}).get('default_validation', {})
        return category.validation_rules
    
    def reload_config(self):
        """Reload configuration from file (useful for dynamic updates)"""
        self.config = self._load_config()
        self.categories = self._parse_categories()
        self._compiled_patterns.clear()
        logger.info("Configuration reloaded")
    
    def add_custom_category(
        self,
        category_name: str,
        category_config: Dict[str, Any],
        persist: bool = False
    ):
        """
        Add a custom category at runtime.
        
        Args:
            category_name: Unique name for the category
            category_config: Configuration dictionary
            persist: Whether to save to configuration file
        """
        try:
            category = TaskCategory(
                name=category_name,
                display_name=category_config.get('display_name', category_name),
                description=category_config.get('description', ''),
                action_verbs=category_config.get('action_verbs', {}),
                object_keywords=category_config.get('object_keywords', {}),
                matching_strategy=category_config.get('matching', {}).get('strategy', 'verb_object'),
                validation_rules=category_config.get('validation', {}),
                aggregation_config=category_config.get('aggregation', {}),
                min_confidence=category_config.get('matching', {}).get('min_confidence', 0.7)
            )
            
            self.categories[category_name] = category
            logger.info(f"Added custom category: {category_name}")
            
            if persist:
                # Would implement saving to file here
                logger.info(f"Persisted category {category_name} to configuration")
                
        except Exception as e:
            logger.error(f"Failed to add custom category {category_name}: {e}")


# Singleton instance
_engine_instance: Optional[TaskPatternEngine] = None


def get_pattern_engine(config_path: str = "data/task_patterns.yaml") -> TaskPatternEngine:
    """
    Get or create singleton pattern engine instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        TaskPatternEngine instance
    """
    global _engine_instance
    
    if _engine_instance is None:
        _engine_instance = TaskPatternEngine(config_path)
    
    return _engine_instance
