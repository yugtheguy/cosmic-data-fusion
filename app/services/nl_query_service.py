"""
Natural Language Query Parser Service
Converts plain English queries into structured database queries
"""
import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class NLQueryParser:
    """Parse natural language queries about astronomical data"""
    
    def __init__(self):
        """Load astronomical knowledge base"""
        knowledge_path = Path(__file__).parent.parent / "data" / "astronomical_knowledge.json"
        with open(knowledge_path, 'r') as f:
            self.knowledge = json.load(f)
    
    def parse(self, query: str) -> Dict:
        """
        Main entry point - parse a natural language query
        
        Args:
            query: Natural language question
            
        Returns:
            Dict with: intent, entities, filters, explanation, suggestions
        """
        query_lower = query.lower().strip()
        
        # Extract entities
        entities = {
            'constellations': self.extract_constellations(query_lower),
            'brightness': self.extract_brightness(query_lower),
            'motion': self.extract_motion(query_lower),
            'time': self.extract_time(query_lower),
            'count': self.extract_count(query_lower),
            'comparison': self.extract_comparison(query_lower),
            'location': self.extract_location(query_lower)
        }
        
        # Classify intent
        intent = self.classify_intent(query_lower, entities)
        
        # Build filters for database query
        filters = self.build_filters(entities)
        
        # Generate explanation
        explanation = self.generate_explanation(query, entities, intent)
        
        # Generate suggestions
        suggestions = self.generate_suggestions(intent, entities)
        
        return {
            'intent': intent,
            'entities': entities,
            'filters': filters,
            'explanation': explanation,
            'suggestions': suggestions,
            'confidence': self._calculate_confidence(entities)
        }
    
    def extract_constellations(self, query: str) -> List[Dict]:
        """Extract constellation references from query"""
        found = []
        
        for key, data in self.knowledge['constellations'].items():
            # Check main name
            if data['name'].lower() in query:
                found.append(data)
                continue
            
            # Check abbreviation
            if data['abbreviation'].lower() in query:
                found.append(data)
                continue
            
            # Check aliases
            if 'aliases' in data:
                for alias in data['aliases']:
                    if alias.lower() in query:
                        found.append(data)
                        break
        
        return found
    
    def extract_brightness(self, query: str) -> Optional[Dict]:
        """Extract brightness/magnitude constraints"""
        # Enhanced synonym matching
        brightness_synonyms = {
            'brightest': ['brightest', 'most bright', 'super bright', 'very bright'],
            'bright': ['bright', 'luminous', 'shining', 'brilliant'],
            'visible': ['visible', 'naked eye', 'unaided eye', 'can see'],
            'dim': ['dim', 'faint', 'weak'],
            'faint': ['faint', 'very dim', 'barely visible']
        }
        
        for key, threshold in self.knowledge['magnitude_thresholds'].items():
            # Check direct key match
            if key.replace('_', ' ') in query:
                return threshold
            
            # Check synonyms
            if key in brightness_synonyms:
                for synonym in brightness_synonyms[key]:
                    if synonym in query:
                        return threshold
        
        return None
    
    def extract_motion(self, query: str) -> Optional[Dict]:
        """Extract proper motion constraints"""
        # Enhanced motion keyword detection
        motion_patterns = {
            'fastest': ['fastest', 'highest proper motion', 'extreme motion', 'super fast'],
            'fast': ['fast', 'quick', 'rapid', 'high proper motion', 'speedy', 'swift'],
            'moving': ['moving', 'motion', 'traveling', 'drifting'],
            'slow': ['slow', 'sluggish', 'low proper motion'],
            'static': ['static', 'stationary', 'fixed', 'not moving']
        }
        
        for key, threshold in self.knowledge['proper_motion_thresholds'].items():
            if key.replace('_', ' ') in query:
                return threshold
            
            # Check pattern synonyms
            if key in motion_patterns:
                for pattern in motion_patterns[key]:
                    if pattern in query:
                        return threshold
        
        return None
    
    def extract_time(self, query: str) -> Optional[Dict]:
        """Extract temporal references"""
        # Check historical epochs
        for key, epoch_data in self.knowledge['historical_epochs'].items():
            for keyword in epoch_data['keywords']:
                if keyword in query:
                    return epoch_data
        
        # Check for year patterns (e.g., "2000 BC", "3000 AD")
        bc_match = re.search(r'(\d+)\s*(bc|bce)', query)
        if bc_match:
            year = int(bc_match.group(1))
            return {
                'epoch': -year,
                'description': f'{year} BC',
                'keywords': []
            }
        
        ad_match = re.search(r'(\d+)\s*(ad|ce)', query)
        if ad_match:
            year = int(ad_match.group(1))
            return {
                'epoch': year,
                'description': f'{year} AD',
                'keywords': []
            }
        
        # Check for "years ago"
        ago_match = re.search(r'(\d+)\s*years?\s*ago', query)
        if ago_match:
            years = int(ago_match.group(1))
            return {
                'epoch': 2024 - years,
                'description': f'{years} years ago',
                'keywords': []
            }
        
        return None
    
    def extract_count(self, query: str) -> Optional[int]:
        """Extract count/limit from query"""
        # Enhanced count extraction patterns
        patterns = [
            r'top\s+(\d+)',
            r'first\s+(\d+)',
            r'(\d+)\s+stars',
            r'show\s+(?:me\s+)?(\d+)',
            r'find\s+(\d+)',
            r'give\s+(?:me\s+)?(\d+)',
            r'list\s+(\d+)',
            r'closest\s+(\d+)',
            r'nearest\s+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        
        # Check for "how many" or count queries
        if any(phrase in query for phrase in ['how many', 'count', 'number of']):
            return 0  # Special flag for COUNT query
        
        return None
    
    def extract_comparison(self, query: str) -> Optional[List[str]]:
        """Extract objects being compared"""
        if not any(word in query for word in ['compare', 'versus', 'vs', 'difference']):
            return None
        
        # Try to find star names
        stars = []
        for key, star_data in self.knowledge['star_names'].items():
            if star_data['common_name'].lower() in query:
                stars.append(star_data['common_name'])
            
            if 'aliases' in star_data:
                for alias in star_data['aliases']:
                    if alias.lower() in query:
                        stars.append(star_data['common_name'])
                        break
        
        return stars if len(stars) >= 2 else None
    
    def extract_location(self, query: str) -> Optional[Dict]:
        """Extract location for visibility calculations"""
        for key, location in self.knowledge['city_locations'].items():
            if key.replace('_', ' ') in query:
                return location
        
        return None
    
    def classify_intent(self, query: str, entities: Dict) -> str:
        """Classify the user's intent"""
        # COMPARE intent - enhanced detection
        if entities['comparison'] or any(word in query for word in ['compare', 'versus', 'vs', 'difference between']):
            return 'COMPARE'
        
        # COUNT intent - enhanced detection
        if entities['count'] == 0 or any(phrase in query for phrase in ['how many', 'count', 'number of', 'total']):
            return 'COUNT'
        
        # TIME_QUERY intent - enhanced detection
        time_indicators = ['look like', 'was', 'were', 'will be', 'looked', 'appeared', 'ago', 'in the past', 'in the future']
        if entities['time'] and any(word in query for word in time_indicators):
            return 'TIME_QUERY'
        
        # EXPLAIN intent - enhanced detection
        explain_patterns = ['what is', 'what are', 'explain', 'tell me about', 'describe', 'define', 'meaning of']
        if any(pattern in query for pattern in explain_patterns):
            return 'EXPLAIN'
        
        # Default to SEARCH
        return 'SEARCH'
    
    def build_filters(self, entities: Dict) -> Dict:
        """Convert entities to database query filters"""
        filters = {}
        
        # Constellation filters (RA/Dec boundaries)
        if entities['constellations']:
            const = entities['constellations'][0]  # Use first constellation
            filters['ra_min'] = const['ra_min']
            filters['ra_max'] = const['ra_max']
            filters['dec_min'] = const['dec_min']
            filters['dec_max'] = const['dec_max']
        
        # Brightness filter
        if entities['brightness']:
            filters['max_magnitude'] = entities['brightness']['max_magnitude']
        
        # Motion filter
        if entities['motion']:
            filters['min_proper_motion'] = entities['motion']['min_pm']
        
        # Time filter
        if entities['time']:
            filters['epoch'] = entities['time']['epoch']
        
        # Count/limit
        if entities['count'] and entities['count'] > 0:
            filters['limit'] = entities['count']
        elif not entities['count']:
            filters['limit'] = 100  # Default limit
        
        return filters
    
    def generate_explanation(self, query: str, entities: Dict, intent: str) -> str:
        """Generate human-readable explanation of what we understood"""
        parts = []
        
        if intent == 'COMPARE':
            stars = entities['comparison']
            return f"Comparing {stars[0]} and {stars[1]}"
        
        if intent == 'COUNT':
            parts.append("Counting stars")
        else:
            parts.append("Searching for stars")
        
        if entities['brightness']:
            parts.append(f"with {entities['brightness']['description'].lower()}")
        
        if entities['motion']:
            parts.append(f"with {entities['motion']['description'].lower()}")
        
        if entities['constellations']:
            const_names = [c['name'] for c in entities['constellations']]
            parts.append(f"in {', '.join(const_names)}")
        
        if entities['time']:
            parts.append(f"at epoch {entities['time']['description']}")
        
        if entities['location']:
            parts.append(f"visible from specified location")
        
        if entities['count'] and entities['count'] > 0:
            parts.append(f"(top {entities['count']})")
        
        return " ".join(parts).capitalize()
    
    def generate_suggestions(self, intent: str, entities: Dict) -> List[str]:
        """Generate follow-up query suggestions"""
        suggestions = []
        
        if intent == 'SEARCH':
            if not entities['time']:
                suggestions.append("Try: 'in ancient Egypt'")
            if not entities['brightness']:
                suggestions.append("Try: 'bright stars'")
            if not entities['motion']:
                suggestions.append("Try: 'fast moving stars'")
        
        if intent == 'TIME_QUERY':
            suggestions.append("Try: 'Show animation from past to present'")
        
        return suggestions[:3]  # Max 3 suggestions
    
    def _calculate_confidence(self, entities: Dict) -> float:
        """Calculate confidence score (0-1) based on entities found"""
        # Start with base confidence
        score = 0.5  # Base score for any query
        
        # Add points for each entity type found
        if entities['constellations']:
            score += 0.2  # Strong signal
        
        if entities['brightness']:
            score += 0.15  # Good signal
        
        if entities['motion']:
            score += 0.1  # Moderate signal
        
        if entities['time']:
            score += 0.1  # Moderate signal
        
        if entities['count'] and entities['count'] > 0:
            score += 0.05  # Weak signal
        
        if entities['comparison']:
            score += 0.1  # Moderate signal
        
        if entities['location']:
            score += 0.1  # Moderate signal
        
        # Cap at 1.0
        return min(score, 1.0)
