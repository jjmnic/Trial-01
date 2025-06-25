import spacy
import re
import csv
from typing import Dict, List, Optional, Tuple

class NLUProcessor:
    """Natural Language Understanding processor for extracting entities and intents from user queries."""
    
    def __init__(self, csv_path=None):
        """Initialize the NLU processor with spaCy model and custom patterns."""
        self.nlp = spacy.load("en_core_web_sm")
        
        # Load states and divisions from the dataset
        self.states = set()
        self.divisions = set()
        if csv_path:
            self._load_location_entities_from_csv(csv_path)
        else:
            self._load_default_location_entities()
        
        # Intent patterns
        self.intent_patterns = {
            'count_schemes': [
                r'how many schemes?',
                r'count.*schemes?',
                r'number.*schemes?',
                r'total.*schemes?'
            ],
            'cost_analysis': [
                r'cost.*year',
                r'expenditure.*year',
                r'budget.*year',
                r'spending.*year'
            ],
            'scheme_types': [
                r'scheme.*type',
                r'type.*scheme',
                r'categories.*scheme'
            ],
            'progress_analysis': [
                r'progress',
                r'completion',
                r'status'
            ],
            'scheme_info': []
        }
    
    def _load_location_entities_from_csv(self, csv_path):
        """Load unique states and divisions from the CSV file."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Handle both possible column names
                    state = row.get('State Name', row.get('state_name', '')).strip()
                    division = row.get('Division Name', row.get('division_name', '')).strip()
                    
                    if state and state.lower() not in ['state name', 'nan', '']:
                        self.states.add(state.lower())
                    
                    if division and division.lower() not in ['division name', 'nan', '']:
                        self.divisions.add(division.lower())
                        
            print(f"DEBUG: Loaded {len(self.states)} states and {len(self.divisions)} divisions from CSV")
        except Exception as e:
            print(f"Error loading locations from CSV: {e}")
            self._load_default_location_entities()
    
    def _load_default_location_entities(self):
        """Load default location entities (fallback)."""
        # States from the actual data
        self.states.update([
            'andaman and nicobar islands',
            'andhra pradesh', 
            'haryana',
            'madhya pradesh'
        ])
        
        # Common divisions from the actual data
        self.divisions.update([
            'adoni', 'agar', 'alirajpur', 'amalapuram', 'ambala', 'anakapalli',
            'ananthapuramu', 'anuppur', 'ashok nagar', 'balaghat', 'baptla',
            'barwani', 'betul', 'bhimavaram', 'bhind', 'bhopal', 'campbell bay',
            'car nicobar', 'chhatarpur', 'chhindwara', 'chittoor', 'damoh',
            'datia', 'dewas', 'dhar', 'diglipur', 'dindori', 'eluru', 'gudur',
            'guna', 'guntur', 'gwalior', 'harda', 'hoshangabad', 'indore',
            'jabalpur', 'jhabua', 'kadapa', 'kakinada', 'kamorta', 'katni',
            'khandwa', 'khargone', 'khurai', 'kurnool', 'machilipatnam',
            'madanapalli', 'mandla', 'mandsour', 'mauganj', 'mayabun',
            'morena', 'nandyal', 'narasaraopet', 'narsinghpur', 'neemuch',
            'nellore', 'niwari', 'ongole', 'paderu', 'palasa', 'panna',
            'parasia', 'paravathipuram manyam', 'podili', 'port blair',
            'pulivendula', 'puttaparthy', 'raisen', 'rajahmundry',
            'rajamehendravaram', 'rajgarh', 'rangat', 'ratlam', 'rayachoti',
            'rewa', 'sagar', 'sardarpur', 'satna', 'sehore', 'seoni',
            'shahdol', 'shajapur', 'sheopur', 'shivpuri', 'sidhi',
            'singrouli', 'srikakulam', 'tikamgarh', 'tirupathi', 'ujjain',
            'umaria', 'vidisha', 'vijayawada', 'visakhapatanm',
            'vizianagaram', 'wimberlygunj', 'ysr kadapa'
        ])
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract location entities (states and divisions) from the query."""
        query_lower = query.lower()
        entities = {
            'states': [],
            'divisions': [],
            'locations': [],  # Generic locations that could be either
            'schemes': [] # New entity type for schemes
        }
        
        # Process with spaCy for general entity recognition
        doc = self.nlp(query)
        
        # Extract GPE (Geopolitical entities) from spaCy
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                location = ent.text.lower()
                entities['locations'].append(location)
        
        # Handle common abbreviations and variations FIRST (more specific)
        abbreviation_variations = {
            'mp': 'madhya pradesh',
            'ap': 'andhra pradesh',
            'hr': 'haryana',
            'a&n': 'andaman and nicobar islands',
            'andaman': 'andaman and nicobar islands',
            'nicobar': 'andaman and nicobar islands',
            'sbm': 'swachh bharat mission',
            'jjm': 'jal jeevan mission'
        }
        
        # Check abbreviations first to avoid conflicts
        for abbrev, full_name in abbreviation_variations.items():
            # Use word boundaries to avoid matching substrings
            if re.search(r'\b' + abbrev + r'\b', query_lower):
                if full_name == 'swachh bharat mission':
                    if 'swachh bharat mission' not in entities['schemes']:
                        entities['schemes'].append('swachh bharat mission')
                elif full_name == 'jal jeevan mission':
                    if 'jal jeevan mission' not in entities['schemes']:
                        entities['schemes'].append('jal jeevan mission')
                elif full_name in self.states:
                    if full_name not in entities['states']:
                        entities['states'].append(full_name)
        
        # Only check for full state names if no abbreviations were found
        if not entities['states']:
            # Sort states by length (longest first) to match longer names first
            sorted_states = sorted(self.states, key=len, reverse=True)
            for state in sorted_states:
                if state in query_lower:
                    entities['states'].append(state)
                    break  # Only match the first (longest) state found
        
        # Check for divisions (only if no states found to avoid conflicts)
        if not entities['states']:
            sorted_divisions = sorted(self.divisions, key=len, reverse=True)
            for division in sorted_divisions:
                if division in query_lower:
                    entities['divisions'].append(division)
                    break  # Only match the first (longest) division found
        
        return entities
    
    def classify_intent(self, query: str, entities: Dict[str, List[str]]) -> str:
        """Classify the intent of the user query."""
        query_lower = query.lower()
        
        # Check for scheme_info intent first if specific scheme entities are found
        if entities.get("schemes") and len(entities["schemes"]) > 0:
            return "scheme_info"

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        # Default fallback
        if any(word in query_lower for word in ['visualize', 'show', 'chart', 'graph']):
            return 'visualization'
        
        return 'general_query'
    
    def parse_query(self, query: str) -> Dict:
        """Parse the user query and extract intent and entities."""
        entities = self.extract_entities(query)
        intent = self.classify_intent(query, entities)
        
        return {
            'intent': intent,
            'entities': entities,
            'original_query': query
        }
    
    def build_location_filter(self, entities: Dict[str, List[str]]) -> Tuple[str, List]:
        """Build SQL WHERE clause and parameters for location filtering."""
        conditions = []
        params = []
        
        if entities['states']:
            # Use the first state found
            state = entities['states'][0]
            # Try both possible column names with case-insensitive matching
            conditions.append("(LOWER(\"State Name\") = ? OR LOWER(state_name) = ?)")
            params.extend([state.lower(), state.lower()])
        
        if entities['divisions']:
            # Use the first division found
            division = entities['divisions'][0]
            # Try both possible column names with case-insensitive matching
            conditions.append("(LOWER(\"Division Name\") = ? OR LOWER(division_name) = ?)")
            params.extend([division.lower(), division.lower()])
        
        # If we have generic locations, try to match them
        if entities["locations"] and not entities["states"] and not entities["divisions"]:
            location = entities["locations"][0].lower()
            # Check if it's a known state or division
            if location in self.states:
                conditions.append("(LOWER(\"State Name\") = ? OR LOWER(state_name) = ?)")
                params.extend([location, location])
            elif location in self.divisions:
                conditions.append("(LOWER(\"Division Name\") = ? OR LOWER(division_name) = ?)")
                params.extend([location, location])
        
        if entities["schemes"]:
            # For scheme-specific queries, we might not need a location filter
            # or we might need to adjust the intent classification to handle them.
            # For now, we'll just return an empty filter.
            pass
        
        where_clause = " AND ".join(conditions) if conditions else ""
        return where_clause, params

