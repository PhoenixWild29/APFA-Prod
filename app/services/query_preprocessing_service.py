"""
Query preprocessing service

Enhances raw queries through:
- Text normalization
- Entity extraction (amounts, rates, loan types, time periods)
- Context enhancement
- Intent classification
"""
import re
import time
from typing import List, Dict, Any


# Loan type patterns
LOAN_TYPES = {
    'mortgage': ['mortgage', 'home loan', 'housing loan'],
    'auto_loan': ['auto loan', 'car loan', 'vehicle loan'],
    'personal_loan': ['personal loan', 'unsecured loan'],
    'student_loan': ['student loan', 'education loan'],
    'business_loan': ['business loan', 'commercial loan']
}

# Intent patterns
INTENT_PATTERNS = {
    'loan_inquiry': ['what is', 'explain', 'tell me about', 'how does', 'what are'],
    'rate_comparison': ['compare', 'best rate', 'lowest rate', 'better rate', 'cheaper'],
    'eligibility_check': ['eligible', 'qualify', 'can i get', 'approved', 'credit score'],
    'general_advice': ['should i', 'recommend', 'advice', 'help', 'guidance']
}


def normalize_text(query: str) -> str:
    """
    Normalize query text
    
    Handles:
    - Currency symbols → standardized format
    - Percentage formats → decimal
    - Abbreviations → full terms
    - Colloquial terms → standard financial terms
    """
    normalized = query.strip()
    
    # Currency normalization
    normalized = re.sub(r'\$\s*(\d+)', r'\1 dollars', normalized)
    normalized = re.sub(r'(\d+)k\b', r'\1000', normalized, flags=re.IGNORECASE)
    
    # Percentage normalization
    normalized = re.sub(r'(\d+\.?\d*)\s*%', r'\1 percent', normalized)
    
    # Common abbreviations
    normalized = re.sub(r'\bAPR\b', 'annual percentage rate', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bFHA\b', 'federal housing administration', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bVA\b', 'veterans affairs', normalized, flags=re.IGNORECASE)
    
    return normalized


def extract_entities(query: str) -> List[Dict[str, Any]]:
    """
    Extract financial entities from query
    
    Returns:
        List of extracted entities with confidence scores
    """
    entities = []
    
    # Extract amounts
    amount_patterns = [
        (r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 1.0),
        (r'(\d+(?:,\d{3})*)\s*dollars?', 0.95),
        (r'(\d+)k\b', 0.9)
    ]
    
    for pattern, confidence in amount_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            value = match.group(1).replace(',', '')
            if 'k' in match.group(0).lower():
                value = str(int(value) * 1000)
            
            entities.append({
                'entity_type': 'amount',
                'value': match.group(0),
                'normalized_value': f"${value}",
                'confidence_score': confidence
            })
    
    # Extract rates
    rate_patterns = [
        (r'(\d+\.?\d*)\s*%', 1.0),
        (r'(\d+\.?\d*)\s*percent', 0.95)
    ]
    
    for pattern, confidence in rate_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            value = match.group(1)
            entities.append({
                'entity_type': 'rate',
                'value': match.group(0),
                'normalized_value': f"{value}%",
                'confidence_score': confidence
            })
    
    # Extract loan types
    query_lower = query.lower()
    for loan_type, keywords in LOAN_TYPES.items():
        for keyword in keywords:
            if keyword in query_lower:
                entities.append({
                    'entity_type': 'loan_type',
                    'value': keyword,
                    'normalized_value': loan_type,
                    'confidence_score': 0.9
                })
                break
    
    # Extract time periods
    time_patterns = [
        (r'(\d+)\s*years?', 1.0),
        (r'(\d+)\s*months?', 1.0),
        (r'(\d+)\s*(?:yr|mo)\b', 0.85)
    ]
    
    for pattern, confidence in time_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            entities.append({
                'entity_type': 'time_period',
                'value': match.group(0),
                'normalized_value': match.group(0),
                'confidence_score': confidence
            })
    
    return entities


def infer_user_intent(query: str) -> str:
    """
    Infer user intent from query
    
    Returns:
        Intent category
    """
    query_lower = query.lower()
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if pattern in query_lower:
                return intent
    
    return 'unknown'


def generate_context_tags(query: str, entities: List[Dict[str, Any]]) -> List[str]:
    """
    Generate financial context tags
    
    Returns:
        List of context tags
    """
    tags = []
    
    # Add tags based on entities
    entity_types = {e['entity_type'] for e in entities}
    
    if 'amount' in entity_types:
        tags.append('loan_amount_specified')
    if 'rate' in entity_types:
        tags.append('interest_rate_focused')
    if 'loan_type' in entity_types:
        tags.append('specific_loan_type')
    if 'time_period' in entity_types:
        tags.append('term_length_specified')
    
    # Add tags based on query content
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['credit', 'score', 'rating']):
        tags.append('credit_related')
    if any(word in query_lower for word in ['payment', 'monthly', 'installment']):
        tags.append('payment_focused')
    if any(word in query_lower for word in ['refinance', 'refi']):
        tags.append('refinancing_query')
    
    return tags


def preprocess_query(raw_query: str) -> Dict[str, Any]:
    """
    Preprocess raw query with comprehensive enhancements
    
    Args:
        raw_query: Raw user query
    
    Returns:
        dict: Preprocessed query data
    """
    start_time = time.time()
    
    # Handle empty or invalid queries
    if not raw_query or not raw_query.strip():
        return {
            'original_query': raw_query,
            'normalized_query': '',
            'extracted_entities': [],
            'user_intent_category': 'unknown',
            'context_tags': [],
            'processing_metadata': {
                'original_length': len(raw_query) if raw_query else 0,
                'normalized_length': 0,
                'entities_found': 0,
                'processing_time_ms': (time.time() - start_time) * 1000
            }
        }
    
    # Normalize text
    normalized_query = normalize_text(raw_query)
    
    # Extract entities
    entities = extract_entities(raw_query)
    
    # Infer intent
    user_intent = infer_user_intent(raw_query)
    
    # Generate context tags
    context_tags = generate_context_tags(raw_query, entities)
    
    processing_time_ms = (time.time() - start_time) * 1000
    
    return {
        'original_query': raw_query,
        'normalized_query': normalized_query,
        'extracted_entities': entities,
        'user_intent_category': user_intent,
        'context_tags': context_tags,
        'processing_metadata': {
            'original_length': len(raw_query),
            'normalized_length': len(normalized_query),
            'entities_found': len(entities),
            'processing_time_ms': processing_time_ms
        }
    }

