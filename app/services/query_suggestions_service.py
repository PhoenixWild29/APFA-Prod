"""
Query suggestions service

Provides intelligent query completions and financial terminology assistance
for investment research and personal finance.
"""

from typing import Any, Dict, List

# Financial terminology database — investment-focused
FINANCIAL_TERMS = {
    "p/e ratio": {
        "definition": "Price-to-Earnings ratio — a stock's price divided by its earnings per share",
        "usage": "What is a good P/E ratio for tech stocks?",
        "related": ["valuation", "earnings", "forward P/E"],
    },
    "dividend yield": {
        "definition": "Annual dividend payment divided by the stock price, expressed as a percentage",
        "usage": "What dividend yield should I look for in income investing?",
        "related": ["income investing", "payout ratio", "dividend growth"],
    },
    "asset allocation": {
        "definition": "The strategy of dividing investments among different asset classes like stocks, bonds, and cash",
        "usage": "What asset allocation is appropriate for my age?",
        "related": ["diversification", "rebalancing", "risk tolerance"],
    },
    "index fund": {
        "definition": "A fund that tracks a market index like the S&P 500, offering broad market exposure at low cost",
        "usage": "Should I invest in index funds or actively managed funds?",
        "related": ["ETF", "passive investing", "expense ratio"],
    },
    "compound interest": {
        "definition": "Interest calculated on the initial principal and also on accumulated interest from previous periods",
        "usage": "How does compound interest affect long-term investing?",
        "related": ["time value of money", "growth rate", "rule of 72"],
    },
}

# Investment-focused query templates
QUERY_TEMPLATES = [
    "What is the outlook for {topic}?",
    "How should I think about {topic}?",
    "Compare {topic} performance over the last year",
    "What are the risks of investing in {topic}?",
    "How does {topic} fit into a diversified portfolio?",
    "What factors drive {topic} returns?",
    "Is now a good time to invest in {topic}?",
    "What are the tax implications of {topic}?",
    "Explain {topic} for a beginner",
    "What is the historical performance of {topic}?",
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

    # 1. Query completions — match against templates
    topics = [
        "S&P 500 index funds",
        "international equities",
        "bond funds",
        "real estate investment trusts",
        "growth stocks",
        "dividend stocks",
        "treasury bonds",
        "emerging markets",
    ]

    for template in QUERY_TEMPLATES:
        for topic in topics:
            query = template.format(topic=topic)

            # Check if partial query matches beginning of template
            if (
                partial_lower
                and query.lower().startswith(partial_lower)
                and len(partial_lower) >= 3
            ):
                suggestions.append(
                    {
                        "query": query,
                        "type": "completion",
                        "score": len(partial_lower) / len(query),
                    }
                )

    # 2. Term definitions — match financial terms
    for term, info in FINANCIAL_TERMS.items():
        if partial_lower and (
            partial_lower in term or term.startswith(partial_lower)
        ):
            suggestions.append(
                {
                    "query": info["usage"],
                    "type": "term_suggestion",
                    "definition": info["definition"],
                    "related": info["related"],
                    "score": 0.8,
                }
            )

    # 3. Sort by score and limit
    suggestions.sort(key=lambda x: x["score"], reverse=True)
    return suggestions[:10]
