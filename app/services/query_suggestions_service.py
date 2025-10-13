"""
Query suggestions service

Provides intelligent query completions and financial terminology assistance
"""
from typing import List, Dict, Any


# Financial terminology database
FINANCIAL_TERMS = {
    "apr": {
        "definition": "Annual Percentage Rate - the yearly cost of a loan including interest and fees",
        "usage": "What is a good APR for a mortgage?",
        "related": ["interest rate", "loan cost", "finance charge"]
    },
    "mortgage": {
        "definition": "A loan used to purchase real estate, secured by the property itself",
        "usage": "How do I qualify for a mortgage?",
        "related": ["home loan", "property financing", "down payment"]
    },
    "refinance": {
        "definition": "Replacing an existing loan with a new loan, often to get better terms",
        "usage": "Should I refinance my mortgage?",
        "related": ["loan modification", "rate reduction", "cash-out refinance"]
    },
    "credit score": {
        "definition": "A numerical representation of creditworthiness, typically ranging from 300-850",
        "usage": "What credit score do I need for a loan?",
        "related": ["FICO score", "credit rating", "credit history"]
    },
    "down payment": {
        "definition": "The upfront payment made when purchasing a home or vehicle",
        "usage": "How much down payment do I need?",
        "related": ["equity", "initial payment", "deposit"]
    }
}

# Common loan-related query templates
QUERY_TEMPLATES = [
    "What is the best interest rate for {loan_type}?",
    "How do I qualify for a {loan_type}?",
    "Compare {loan_type} rates",
    "What are the requirements for {loan_type}?",
    "Should I refinance my {loan_type}?",
    "What credit score is needed for {loan_type}?",
    "How much down payment for {loan_type}?",
    "What are {loan_type} closing costs?",
    "Calculate {loan_type} monthly payment",
    "Is {loan_type} right for me?"
]


def generate_query_suggestions(partial_query: str) -> List[Dict[str, Any]]:
    """
    Generate intelligent query suggestions
    
    Args:
        partial_query: User's partial input
    
    Returns:
        List of suggestions with scores and explanations
    """
    suggestions = []
    partial_lower = partial_query.lower().strip()
    
    # 1. Query completions - match against templates
    loan_types = ["mortgage", "auto loan", "personal loan", "student loan", "home equity loan"]
    
    for template in QUERY_TEMPLATES:
        for loan_type in loan_types:
            query = template.format(loan_type=loan_type)
            
            # Check if partial query matches beginning of template
            if query.lower().startswith(partial_lower) or partial_lower in query.lower():
                # Calculate relevance score
                if query.lower().startswith(partial_lower):
                    score = 95.0
                elif partial_lower in query.lower()[:len(partial_lower) + 10]:
                    score = 85.0
                else:
                    score = 70.0
                
                suggestions.append({
                    "completed_query": query,
                    "relevance_score": score,
                    "suggestion_type": "completion",
                    "explanation": f"Common question about {loan_type}"
                })
    
    # 2. Financial terminology assistance
    for term, info in FINANCIAL_TERMS.items():
        if partial_lower in term or term in partial_lower:
            suggestions.append({
                "completed_query": info["usage"],
                "relevance_score": 90.0,
                "suggestion_type": "terminology",
                "explanation": f"{term.upper()}: {info['definition']}"
            })
    
    # 3. Related topics
    if "rate" in partial_lower or "interest" in partial_lower:
        suggestions.append({
            "completed_query": "Compare current mortgage interest rates",
            "relevance_score": 85.0,
            "suggestion_type": "related_topic",
            "explanation": "Interest rates vary by loan type and market conditions"
        })
        suggestions.append({
            "completed_query": "How do interest rates affect my monthly payment?",
            "relevance_score": 82.0,
            "suggestion_type": "related_topic",
            "explanation": "Understanding the impact of rates on affordability"
        })
    
    if "loan" in partial_lower:
        suggestions.append({
            "completed_query": "What are the different types of loans available?",
            "relevance_score": 80.0,
            "suggestion_type": "related_topic",
            "explanation": "Overview of loan products and their purposes"
        })
    
    # Deduplicate and rank
    unique_suggestions = {s["completed_query"]: s for s in suggestions}
    ranked_suggestions = sorted(
        unique_suggestions.values(),
        key=lambda x: x["relevance_score"],
        reverse=True
    )
    
    # Limit to top 10
    return ranked_suggestions[:10]

