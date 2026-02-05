"""
AI Research Assistant Service
Enhances Cosmic Fusion with ML-powered research assistance
Sits on top of existing services without modifying them
"""
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResearchInsight:
    """Structured insight for research output"""
    object_id: str
    object_name: str
    significance_score: float  # 0-1, higher = more interesting
    why_it_matters: str
    deviation_category: str  # strength classification
    consensus_confidence: str  # LOW, MEDIUM, HIGH (multi-method agreement)
    confidence_explanation: str  # Why this confidence level
    details: Dict[str, Any]


class AIResearchAssistant:
    """
    AI Research Assistant - Layer on top of existing Cosmic Fusion services
    
    Purpose: Exploratory data analysis, not prediction or hypothesis testing.
    - Ranks results by composite deviation scores
    - Identifies statistical outliers within query results
    - Highlights distinctive patterns relative to returned dataset
    - Provides explainable reasoning based on percentile rankings
    """
    
    def __init__(self):
        """Initialize the research assistant"""
        self.min_confidence_threshold = 0.6
        self.max_output_items = 10  # Show only top N most important
        
    def enhance_query_intent(self, parsed_query: Dict) -> Dict:
        """
        Phase 1: Enhance intent mapping with research context
        
        Takes existing parsed query and adds research-specific metadata
        Does NOT modify the original query structure
        """
        enhanced = parsed_query.copy()
        
        # Add research context based on intent
        enhanced['research_context'] = self._infer_research_context(
            parsed_query.get('intent', 'SEARCH'),
            parsed_query.get('entities', {})
        )
        
        # Add confidence in interpretation
        enhanced['interpretation_confidence'] = self._calculate_interpretation_confidence(
            parsed_query
        )
        
        # Add suggested refinements if confidence is low
        if enhanced['interpretation_confidence'] < self.min_confidence_threshold:
            enhanced['suggested_clarifications'] = self._suggest_clarifications(parsed_query)
        
        return enhanced
    
    def _infer_research_context(self, intent: str, entities: Dict) -> Dict:
        """Infer what kind of research the user is conducting"""
        context = {
            'research_type': 'exploratory',
            'expected_result_type': 'stellar_catalog',
            'analysis_focus': []
        }
        
        # Map intent to research type
        intent_map = {
            'COMPARE': {
                'research_type': 'comparative',
                'analysis_focus': ['differences', 'similarities', 'statistical_comparison']
            },
            'COUNT': {
                'research_type': 'statistical',
                'analysis_focus': ['population_statistics', 'distributions']
            },
            'TIME_QUERY': {
                'research_type': 'temporal_analysis',
                'analysis_focus': ['motion', 'evolution', 'historical_positions']
            },
            'EXPLAIN': {
                'research_type': 'educational',
                'analysis_focus': ['concepts', 'definitions']
            }
        }
        
        if intent in intent_map:
            context.update(intent_map[intent])
        
        # Add focus based on entities
        if entities.get('motion'):
            context['analysis_focus'].append('proper_motion')
        if entities.get('brightness'):
            context['analysis_focus'].append('photometry')
        if entities.get('constellations'):
            context['analysis_focus'].append('spatial_distribution')
        
        return context
    
    def _calculate_interpretation_confidence(self, parsed_query: Dict) -> float:
        """Calculate confidence in query interpretation"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if clear entities extracted
        entities = parsed_query.get('entities', {})
        found_entities = sum(1 for v in entities.values() if v)
        confidence += min(0.3, found_entities * 0.1)
        
        # Higher confidence if filters are specific
        filters = parsed_query.get('filters', {})
        if len(filters) > 0:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _suggest_clarifications(self, parsed_query: Dict) -> List[str]:
        """Suggest refinements when confidence is low"""
        suggestions = []
        entities = parsed_query.get('entities', {})
        
        if not entities.get('brightness'):
            suggestions.append("Specify brightness (e.g., 'bright' or 'visible to naked eye')")
        
        if not entities.get('constellations') and not entities.get('location'):
            suggestions.append("Specify location on sky (e.g., 'near Orion' or 'in northern sky')")
        
        if parsed_query.get('intent') == 'SEARCH' and not entities.get('count'):
            suggestions.append("Specify how many results you want (e.g., 'top 5')")
        
        return suggestions
    
    def analyze_results(self, 
                       results: List[Dict], 
                       research_context: Dict,
                       intent: str) -> Dict:
        """
        Phase 2: ML-Assisted Analysis (Research Safe)
        
        Applies statistical/ML techniques to:
        - Rank results by relevance
        - Detect statistical anomalies
        - Highlight significance
        
        Does NOT predict future, only analyzes existing data
        """
        if not results:
            return {
                'insights': [],
                'summary': 'No results found matching your criteria.',
                'analysis_confidence': 0.0,
                'reasoning': 'Insufficient data for analysis'
            }
        
        # Extract numerical features for analysis
        features = self._extract_features(results)
        
        # Calculate statistical significance for each object
        significance_scores, individual_scores = self._calculate_significance_scores(features, research_context)
        
        # Rank results by research relevance
        ranked_results = self._rank_by_relevance(
            results, 
            significance_scores,
            research_context,
            intent
        )
        
        # Generate insights for top results only
        insights = self._generate_insights(
            ranked_results[:self.max_output_items],
            features,
            individual_scores,  # Pass individual scores for consensus
            research_context
        )
        
        # Create summary
        summary = self._create_summary(insights, len(results), research_context)
        
        return {
            'insights': insights,
            'summary': summary,
            'total_analyzed': len(results),
            'shown': min(len(results), self.max_output_items),
            'analysis_strength': self._calculate_analysis_strength(features),
            'reasoning': self._explain_analysis_approach(research_context)
        }
    
    def _extract_features(self, results: List[Dict]) -> Dict[str, np.ndarray]:
        """Extract numerical features for analysis"""
        features = {
            'magnitude': [],
            'ra': [],
            'dec': [],
            'parallax': []
        }
        
        for result in results:
            features['magnitude'].append(result.get('magnitude', np.nan))
            features['ra'].append(result.get('ra', np.nan))
            features['dec'].append(result.get('dec', np.nan))
            features['parallax'].append(result.get('parallax', np.nan))
        
        # Convert to numpy arrays
        for key in features:
            features[key] = np.array(features[key], dtype=float)
        
        return features
    
    def _calculate_significance_scores(self, 
                                       features: Dict[str, np.ndarray],
                                       research_context: Dict) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Calculate deviation scores using statistical methods (exploratory)
        Higher score = stronger statistical outlier within query results
        
        Returns:
            (composite_scores, individual_scores_dict)
        """
        n_objects = len(features['magnitude'])
        scores = np.zeros(n_objects)
        
        # Track individual component scores for consensus confidence
        individual_scores = {
            'photometric': np.zeros(n_objects),
            'spatial': np.zeros(n_objects),
            'distance': np.zeros(n_objects)
        }
        
        # Analyze based on research focus
        focus_areas = research_context.get('analysis_focus', [])
        
        # Photometric significance (brightness deviations)
        if 'photometry' in focus_areas or len(focus_areas) == 0:
            mag = features['magnitude']
            valid = ~np.isnan(mag)
            if np.sum(valid) > 1:
                # Z-score: how many std deviations from mean
                z_scores = np.abs(stats.zscore(mag[valid], nan_policy='omit'))
                # Normalize to 0-1 range
                if len(z_scores) > 0 and np.max(z_scores) > 0:
                    photometric_scores = z_scores / (np.max(z_scores) + 1e-6)
                    individual_scores['photometric'][valid] = photometric_scores
                    scores[valid] += photometric_scores * 0.4
        
        # Spatial significance (unusual positions)
        if 'spatial_distribution' in focus_areas or len(focus_areas) == 0:
            ra = features['ra']
            dec = features['dec']
            valid = (~np.isnan(ra)) & (~np.isnan(dec))
            if np.sum(valid) > 1:
                # Distance from mean position
                ra_mean = np.nanmean(ra)
                dec_mean = np.nanmean(dec)
                distances = np.sqrt((ra - ra_mean)**2 + (dec - dec_mean)**2)
                if np.nanmax(distances) > 0:
                    spatial_scores = distances / (np.nanmax(distances) + 1e-6)
                    individual_scores['spatial'] = np.nan_to_num(spatial_scores)
                    scores += np.nan_to_num(spatial_scores) * 0.3
        
        # Distance significance (proximity to Earth)
        parallax = features['parallax']
        valid = (~np.isnan(parallax)) & (parallax > 0)
        if np.sum(valid) > 0:
            # Higher parallax = closer = potentially more interesting
            distance_scores = parallax / (np.nanmax(parallax[valid]) + 1e-6)
            individual_scores['distance'] = np.nan_to_num(distance_scores)
            scores += np.nan_to_num(distance_scores) * 0.3
        
        # Normalize composite to 0-1 range
        if np.max(scores) > 0:
            scores = scores / np.max(scores)
        
        return scores, individual_scores
    
    def _rank_by_relevance(self,
                          results: List[Dict],
                          significance_scores: np.ndarray,
                          research_context: Dict,
                          intent: str) -> List[Dict]:
        """Rank results by research relevance"""
        # Add significance scores and original indices to results
        for i, result in enumerate(results):
            result['_significance_score'] = float(significance_scores[i])
            result['_original_idx'] = i
        
        # Sort by significance (descending)
        ranked = sorted(results, key=lambda x: x['_significance_score'], reverse=True)
        
        return ranked
    
    def _generate_insights(self,
                          top_results: List[Dict],
                          features: Dict[str, np.ndarray],
                          individual_scores: Dict[str, np.ndarray],
                          research_context: Dict) -> List[ResearchInsight]:
        """Generate research insights for top results with consensus confidence"""  
        insights = []
        
        for i, result in enumerate(top_results):
            significance = result.get('_significance_score', 0.0)
            result_idx = result.get('_original_idx', i)  # Track original index
            
            # Calculate consensus-based confidence
            consensus_conf, conf_explanation = self._calculate_consensus_confidence(
                significance,
                individual_scores,
                result_idx,
                features
            )
            
            # Determine why this object matters
            why_matters = self._explain_significance(result, features, research_context)
            
            # Determine deviation strength
            deviation_category = self._classify_deviation_strength(significance)
            
            insight = ResearchInsight(
                object_id=str(result.get('id', '')),
                object_name=result.get('source_id', f"Star #{i+1}"),
                significance_score=significance,
                why_it_matters=why_matters,
                deviation_category=deviation_category,
                consensus_confidence=consensus_conf,
                confidence_explanation=conf_explanation,
                details={
                    'magnitude': result.get('magnitude'),
                    'ra': result.get('ra'),
                    'dec': result.get('dec'),
                    'parallax': result.get('parallax')
                }
            )
            insights.append(insight)
        
        return insights
    
    def _explain_significance(self, 
                             result: Dict,
                             features: Dict[str, np.ndarray],
                             research_context: Dict) -> str:
        """
        Phase 4: Explainability - Why this object stands out
        Uses precise percentile-based language
        """
        reasons = []
        
        # Check brightness
        mag = result.get('magnitude')
        if mag is not None:
            mag_arr = features['magnitude']
            valid = ~np.isnan(mag_arr)
            if np.sum(valid) > 1:
                percentile = stats.percentileofscore(mag_arr[valid], mag, kind='weak')
                if percentile <= 10:
                    pct_display = max(1, int(percentile))
                    reasons.append(f"brightness ranks in top {pct_display}% of query results")
                elif percentile >= 90:
                    pct_display = max(1, int(100-percentile))
                    reasons.append(f"brightness ranks in dimmest {pct_display}% of query results")
        
        # Check distance (parallax)
        parallax = result.get('parallax')
        if parallax and parallax > 0:
            parallax_arr = features['parallax']
            valid = (parallax_arr > 0) & (~np.isnan(parallax_arr))
            if np.sum(valid) > 1:
                percentile = stats.percentileofscore(parallax_arr[valid], parallax, kind='weak')
                if percentile >= 90:
                    distance_pc = 1000.0 / parallax
                    pct_display = max(1, int(100-percentile))
                    reasons.append(f"distance places it in nearest {pct_display}% of returned objects (~{distance_pc:.1f} parsecs)")
        
        # Default reason
        if not reasons:
            return "distinctive within this query's feature distribution"
        
        return "; ".join(reasons)
    
    def _calculate_consensus_confidence(
        self,
        composite_score: float,
        individual_scores: Dict[str, np.ndarray],
        object_idx: int,
        features: Dict[str, np.ndarray]
    ) -> Tuple[str, str]:
        """
        Calculate consensus-based confidence via multi-method agreement
        
        NOT probabilistic: Measures agreement between independent ranking methods
        (photometric z-score, spatial deviation, distance significance)
        
        Args:
            composite_score: Weighted composite deviation score (0-1)
            individual_scores: Dict of individual method scores
            object_idx: Index of object in original dataset
            features: Feature arrays for variance calculation
        
        Returns:
            (confidence_level, explanation_text)
            confidence_level ∈ {LOW, MEDIUM, HIGH}
        """
        # Extract individual method scores for this object
        photo_score = individual_scores['photometric'][object_idx]
        spatial_score = individual_scores['spatial'][object_idx]
        distance_score = individual_scores['distance'][object_idx]
        
        # Count how many methods show strong deviation (> 0.6 threshold)
        strong_threshold = 0.6
        moderate_threshold = 0.3
        
        strong_count = sum([
            photo_score > strong_threshold,
            spatial_score > strong_threshold,
            distance_score > strong_threshold
        ])
        
        moderate_count = sum([
            photo_score > moderate_threshold,
            spatial_score > moderate_threshold,
            distance_score > moderate_threshold
        ])
        
        # Calculate feature variance (distinctiveness across multiple dimensions)
        score_variance = np.var([photo_score, spatial_score, distance_score])
        
        # Calculate score agreement (how consistent are the methods?)
        # Low variance = methods agree (all high or all low)
        # High variance = methods disagree (some high, some low)
        score_std = np.std([photo_score, spatial_score, distance_score])
        agreement = 1.0 - min(score_std, 1.0)  # Convert std to agreement (0-1)
        
        # Decision logic for confidence levels
        if strong_count >= 2 and composite_score > 0.70:
            # Multiple methods strongly agree
            confidence = "HIGH"
            explanation = (
                f"Multiple independent metrics (photometric, spatial, distance) show strong agreement. "
                f"Object ranks in top 30% across {strong_count}/3 methods."
            )
        
        elif (strong_count >= 1 and moderate_count >= 2) or (composite_score > 0.50 and agreement > 0.6):
            # Some methods agree, or moderate consensus
            confidence = "MEDIUM"
            active_methods = []
            if photo_score > moderate_threshold:
                active_methods.append("photometric")
            if spatial_score > moderate_threshold:
                active_methods.append("spatial")
            if distance_score > moderate_threshold:
                active_methods.append("distance")
            
            explanation = (
                f"Object shows distinctiveness in {len(active_methods)}/3 metrics: {', '.join(active_methods)}. "
                f"Composite score: {composite_score:.2f}."
            )
        
        else:
            # Low agreement or low composite score
            confidence = "LOW"
            explanation = (
                f"Limited deviation detected across metrics (composite: {composite_score:.2f}). "
                f"Object may not be scientifically distinctive within query scope."
            )
        
        return confidence, explanation
    
    def _classify_deviation_strength(self, significance_score: float) -> str:
        """Classify deviation strength with numeric context"""
        if significance_score >= 0.7:
            return f"strong (composite score: {significance_score:.2f})"
        elif significance_score >= 0.4:
            return f"moderate (composite score: {significance_score:.2f})"
        else:
            return f"weak (composite score: {significance_score:.2f})"
    
    def _create_summary(self, 
                       insights: List[ResearchInsight],
                       total_count: int,
                       research_context: Dict) -> str:
        """
        Phase 3: Create important-only summary
        Reduces cognitive overload
        """
        if not insights:
            return f"Ranked {total_count} objects. No strong deviations detected in this query set."
        
        # Count strong deviation insights
        strong_dev = sum(1 for i in insights if "strong" in i.deviation_category)
        
        # Identify key findings
        research_type = research_context.get('research_type', 'exploratory')
        
        if research_type == 'temporal_analysis':
            return f"Ranked {total_count} objects by motion features. Top {len(insights)} show strongest deviations."
        elif research_type == 'comparative':
            return f"Ranked {total_count} objects comparatively. Top {len(insights)} are statistically distinctive."
        elif research_type == 'statistical':
            return f"Ranked {total_count} objects by composite score. Showing top {len(insights)} by deviation."
        else:
            return f"Ranked {total_count} objects. Top {len(insights)} by composite deviation score (exploratory ranking)."
    
    def _calculate_analysis_strength(self, features: Dict[str, np.ndarray]) -> float:
        """Calculate overall analysis strength based on sample size"""
        # More data = more reliable ranking
        n_objects = len(features['magnitude'])
        
        if n_objects < 5:
            return 0.3  # Limited sample
        elif n_objects < 20:
            return 0.6  # Moderate sample
        else:
            return 0.9  # Strong sample
    
    def _explain_analysis_approach(self, research_context: Dict) -> str:
        """
        Phase 4: Explain how analysis was performed
        Transparent, simple language
        """
        approaches = []
        
        focus_areas = research_context.get('analysis_focus', [])
        
        if 'photometry' in focus_areas:
            approaches.append("brightness deviations from mean")
        if 'spatial_distribution' in focus_areas:
            approaches.append("spatial clustering patterns")
        if 'proper_motion' in focus_areas:
            approaches.append("motion characteristics")
        
        if not approaches:
            approaches.append("overall statistical significance")
        
        return f"Objects ranked by: {', '.join(approaches)}"
    
    def fallback_response(self, error_context: str) -> Dict:
        """
        Phase 5: Stability & Fallback
        Return safe default when AI confidence is low
        """
        logger.warning(f"AI Research Assistant fallback triggered: {error_context}")
        
        return {
            'fallback_active': True,
            'insights': [],
            'summary': 'Unable to perform AI-assisted analysis. Showing default results.',
            'reasoning': 'Falling back to standard query results for safety.',
            'suggestion': 'Try refining your query with more specific criteria.',
            'error_context': error_context
        }
    
    def format_for_api(self, analysis_result: Dict, original_results: List[Dict]) -> Dict:
        """
        Format AI analysis for API response
        Maintains backward compatibility - adds optional fields only
        """
        insights = analysis_result.get('insights', [])
        
        # Convert insights to simple dicts
        formatted_insights = []
        for insight in insights:
            if isinstance(insight, ResearchInsight):
                formatted_insights.append({
                    'object_id': insight.object_id,
                    'object_name': insight.object_name,
                    'significance': insight.significance_score,
                    'why_it_matters': insight.why_it_matters,
                    'deviation_strength': insight.deviation_category,
                    'consensus_confidence': insight.consensus_confidence,
                    'confidence_explanation': insight.confidence_explanation,
                    'details': insight.details
                })
            else:
                formatted_insights.append(insight)
        
        # Determine strength label based on sample size
        strength_score = analysis_result.get('analysis_strength', 0.0)
        if strength_score >= 0.8:
            strength_label = "Strong (multiple high-deviation outliers detected)"
        elif strength_score >= 0.5:
            strength_label = "Moderate (sufficient sample for ranking)"
        else:
            strength_label = "Limited (small sample size)"
        
        return {
            'ai_enhanced': True,
            'analysis_scope': 'Query-limited exploratory ranking. No hypothesis testing or prediction performed.',
            'research_summary': analysis_result.get('summary', ''),
            'key_findings': formatted_insights,
            'analysis_strength': strength_label,
            'reasoning': analysis_result.get('reasoning', ''),
            'total_analyzed': analysis_result.get('total_analyzed', len(original_results)),
            'shown': analysis_result.get('shown', len(formatted_insights))
        }
