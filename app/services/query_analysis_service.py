"""
Query analysis service with linguistic processing
"""
import time
import re
from typing import Dict, Any, List
from textblob import TextBlob


def analyze_linguistic_features(query: str) -> Dict[str, Any]:
    """Analyze linguistic features of query"""
    blob = TextBlob(query)
    
    # Sentence structure
    sentences = blob.sentences
    structure = "complex" if len(sentences) > 1 or len(query.split(',')) > 2 else "simple"
    
    # Readability (Flesch Reading Ease approximation)
    words = len(query.split())
    sentences_count = max(len(sentences), 1)
    avg_words_per_sentence = words / sentences_count
    
    # Simple readability score (higher = easier)
    readability = max(0, min(100, 100 - (avg_words_per_sentence * 2)))
    
    # Financial terminology density
    financial_terms = ['loan', 'mortgage', 'interest', 'rate', 'apr', 'credit', 'refinance', 
                       'payment', 'debt', 'equity', 'principal', 'term', 'closing']
    query_lower = query.lower()
    financial_word_count = sum(1 for term in financial_terms if term in query_lower)
    density = min(1.0, financial_word_count / max(words, 1))
    
    # Grammatical complexity
    complexity = 1
    if ',' in query:
        complexity += 2
    if any(word in query_lower for word in ['however', 'although', 'because', 'therefore']):
        complexity += 2
    if len(sentences) > 1:
        complexity += 2
    complexity = min(10, complexity)
    
    return {
        "sentence_structure": structure,
        "readability_score": readability,
        "financial_terminology_density": density,
        "grammatical_complexity": complexity
    }


def classify_query_intent(query: str) -> Dict[str, Any]:
    """Classify user intent"""
    query_lower = query.lower()
    
    # Intent patterns
    intent_patterns = {
        'loan_application': ['apply', 'application', 'get a loan', 'need a loan'],
        'rate_inquiry': ['rate', 'interest', 'apr', 'percentage', 'cost'],
        'eligibility_check': ['eligible', 'qualify', 'can i get', 'approved'],
        'comparison_request': ['compare', 'better', 'best', 'difference between'],
        'general_advice': ['should i', 'advice', 'recommend', 'help', 'what is']
    }
    
    intent_scores = {}
    for intent, patterns in intent_patterns.items():
        score = sum(1 for pattern in patterns if pattern in query_lower)
        if score > 0:
            intent_scores[intent] = score
    
    # Determine primary intent
    if intent_scores:
        primary_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(1.0, intent_scores[primary_intent] / 3.0)
    else:
        primary_intent = 'general_advice'
        confidence = 0.5
    
    # Secondary intents
    secondary = [intent for intent, score in intent_scores.items() 
                 if intent != primary_intent and score > 0]
    
    return {
        "primary_intent": primary_intent,
        "confidence_score": confidence,
        "secondary_intents": secondary
    }


def extract_financial_entities(query: str) -> List[Dict[str, Any]]:
    """Extract financial entities with positions"""
    entities = []
    
    # Monetary amounts
    for match in re.finditer(r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', query):
        entities.append({
            "entity_type": "monetary_amount",
            "value": match.group(0),
            "position_start": match.start(),
            "position_end": match.end(),
            "confidence_score": 1.0
        })
    
    # Percentages
    for match in re.finditer(r'(\d+\.?\d*)\s*%', query):
        entities.append({
            "entity_type": "percentage",
            "value": match.group(0),
            "position_start": match.start(),
            "position_end": match.end(),
            "confidence_score": 1.0
        })
    
    # Time periods
    for match in re.finditer(r'(\d+)\s*(year|month|day)s?', query, re.IGNORECASE):
        entities.append({
            "entity_type": "time_period",
            "value": match.group(0),
            "position_start": match.start(),
            "position_end": match.end(),
            "confidence_score": 0.95
        })
    
    # Loan types
    loan_types = ['mortgage', 'auto loan', 'personal loan', 'student loan', 'home equity']
    for loan_type in loan_types:
        if loan_type in query.lower():
            pos = query.lower().find(loan_type)
            entities.append({
                "entity_type": "loan_type",
                "value": loan_type,
                "position_start": pos,
                "position_end": pos + len(loan_type),
                "confidence_score": 0.9
            })
    
    # Credit terms
    credit_terms = ['credit score', 'fico', 'credit rating', 'credit history']
    for term in credit_terms:
        if term in query.lower():
            pos = query.lower().find(term)
            entities.append({
                "entity_type": "credit_term",
                "value": term,
                "position_start": pos,
                "position_end": pos + len(term),
                "confidence_score": 0.9
            })
    
    return entities


def assess_query_complexity(query: str, entities: List[Dict], intent: Dict) -> Dict[str, Any]:
    """Assess query complexity"""
    # Vocabulary complexity
    words = query.split()
    avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
    vocab_complexity = min(10, int(avg_word_length / 2))
    
    # Multi-part questions
    question_marks = query.count('?')
    commas = query.count(',')
    multi_part = question_marks + (commas // 2)
    
    # Required domain knowledge
    domain_knowledge = 3  # baseline
    if len(entities) > 3:
        domain_knowledge += 2
    if intent.get("confidence_score", 0) < 0.7:
        domain_knowledge += 1
    domain_knowledge = min(10, domain_knowledge)
    
    # Overall complexity
    complexity_score = min(10, (vocab_complexity + multi_part + domain_knowledge) // 3)
    
    return {
        "complexity_score": complexity_score,
        "vocabulary_complexity": vocab_complexity,
        "multi_part_questions": multi_part,
        "required_domain_knowledge": domain_knowledge
    }


def analyze_query_comprehensive(query: str) -> Dict[str, Any]:
    """Perform comprehensive query analysis"""
    start_time = time.time()
    
    # Linguistic analysis
    linguistic = analyze_linguistic_features(query)
    
    # Intent classification
    intent = classify_query_intent(query)
    
    # Entity extraction
    entities = extract_financial_entities(query)
    
    # Complexity assessment
    complexity = assess_query_complexity(query, entities, intent)
    
    # Processing recommendations
    processing_recs = {
        "optimal_routing": "retriever → analyzer → orchestrator",
        "required_data_sources": ["loan_compliance_docs", "rate_database", "eligibility_rules"],
        "estimated_processing_time_ms": 185.0 + (complexity["complexity_score"] * 20)
    }
    
    # Suggested improvements
    suggestions = []
    if linguistic["readability_score"] < 50:
        suggestions.append("Consider simplifying your query for better results")
    if len(entities) == 0:
        suggestions.append("Include specific details (amounts, rates, loan types) for more accurate advice")
    if intent["confidence_score"] < 0.7:
        suggestions.append("Clarify your question to help us provide better assistance")
    
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "query_text": query,
        "linguistic_analysis": linguistic,
        "intent_classification": intent,
        "entity_extraction": entities,
        "complexity_assessment": complexity,
        "processing_recommendations": processing_recs,
        "metadata": {
            "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "processing_time_ms": processing_time,
            "confidence_scores": {
                "linguistic": 0.9,
                "intent": intent["confidence_score"],
                "entity_extraction": 0.85,
                "complexity": 0.8
            },
            "suggested_improvements": suggestions
        }
    }

