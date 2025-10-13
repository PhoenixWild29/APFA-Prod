"""
Query validation service

Provides comprehensive query validation including:
- Profanity detection
- Financial relevance scoring
- Content safety analysis
- Formatting validation
"""
import re
from typing import Dict, Any, List
from profanity_check import predict_prob
import time


# Financial keywords for relevance scoring
FINANCIAL_KEYWORDS = {
    'high_relevance': ['loan', 'mortgage', 'interest', 'credit', 'debt', 'finance', 'payment', 'apr', 'refinance', 'equity'],
    'medium_relevance': ['money', 'bank', 'savings', 'investment', 'budget', 'account', 'rate', 'term', 'principal'],
    'low_relevance': ['financial', 'advisor', 'planning', 'advice', 'help', 'question', 'information']
}


def calculate_financial_relevance_score(query: str) -> float:
    """
    Calculate financial relevance score (0-100)
    
    Args:
        query: Query text
    
    Returns:
        float: Relevance score (0-100)
    """
    query_lower = query.lower()
    score = 0.0
    
    # High relevance keywords (10 points each, max 50)
    high_count = sum(1 for keyword in FINANCIAL_KEYWORDS['high_relevance'] if keyword in query_lower)
    score += min(high_count * 10, 50)
    
    # Medium relevance keywords (5 points each, max 30)
    medium_count = sum(1 for keyword in FINANCIAL_KEYWORDS['medium_relevance'] if keyword in query_lower)
    score += min(medium_count * 5, 30)
    
    # Low relevance keywords (2 points each, max 20)
    low_count = sum(1 for keyword in FINANCIAL_KEYWORDS['low_relevance'] if keyword in query_lower)
    score += min(low_count * 2, 20)
    
    return min(score, 100.0)


def validate_query_comprehensive(query: str) -> Dict[str, Any]:
    """
    Perform comprehensive query validation
    
    Args:
        query: Query text to validate
    
    Returns:
        dict: Validation results with detailed feedback
    """
    start_time = time.time()
    
    validation_failures = []
    suggested_improvements = []
    explanatory_messages = []
    
    # 1. Profanity detection
    profanity_prob = predict_prob([query])[0]
    profanity_detected = profanity_prob > 0.5
    
    if profanity_detected:
        validation_failures.append("Profanity or inappropriate language detected")
        suggested_improvements.append("Please rephrase your query using professional language")
        explanatory_messages.append(f"Profanity detection confidence: {profanity_prob:.2%}")
    
    # 2. Financial relevance scoring
    financial_relevance_score = calculate_financial_relevance_score(query)
    is_financially_relevant = financial_relevance_score >= 30.0
    
    if not is_financially_relevant:
        validation_failures.append("Query has low financial relevance")
        suggested_improvements.append("Include specific financial terms (e.g., loan, mortgage, interest rate)")
        explanatory_messages.append(f"Financial relevance score: {financial_relevance_score:.1f}/100")
    else:
        explanatory_messages.append(f"Financial relevance score: {financial_relevance_score:.1f}/100 - Good")
    
    # 3. Content safety analysis
    has_html = bool(re.search(r'<[^>]+>', query))
    has_script = bool(re.search(r'<script|javascript:', query, re.IGNORECASE))
    is_content_safe = not (has_html or has_script or profanity_detected)
    
    if has_html or has_script:
        validation_failures.append("Query contains potentially unsafe HTML or script content")
        suggested_improvements.append("Remove HTML tags and scripts from your query")
        explanatory_messages.append("HTML/script injection detected")
    
    # 4. Formatting validation
    is_too_short = len(query.strip()) < 10
    is_too_long = len(query) > 500
    has_valid_chars = bool(re.search(r'[a-zA-Z]', query))
    is_properly_formatted = not is_too_short and not is_too_long and has_valid_chars
    
    if is_too_short:
        validation_failures.append("Query is too short (minimum 10 characters)")
        suggested_improvements.append("Provide more details in your query")
    
    if is_too_long:
        validation_failures.append("Query is too long (maximum 500 characters)")
        suggested_improvements.append("Shorten your query to focus on the main question")
    
    if not has_valid_chars:
        validation_failures.append("Query contains no valid alphabetic characters")
        suggested_improvements.append("Include descriptive text in your query")
    
    # Overall validation
    is_valid = (
        not profanity_detected and
        is_financially_relevant and
        is_content_safe and
        is_properly_formatted
    )
    
    # Confidence score
    confidence_score = 0.9 if is_valid else 0.6
    
    validation_time_ms = (time.time() - start_time) * 1000
    
    return {
        "is_valid": is_valid,
        "profanity_detected": profanity_detected,
        "is_financially_relevant": is_financially_relevant,
        "is_content_safe": is_content_safe,
        "is_properly_formatted": is_properly_formatted,
        "financial_relevance_score": financial_relevance_score,
        "confidence_score": confidence_score,
        "validation_failures": validation_failures,
        "suggested_improvements": suggested_improvements,
        "explanatory_messages": explanatory_messages,
        "validation_time_ms": validation_time_ms
    }

