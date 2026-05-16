"""Default research agenda for the Perplexity batch enrichment connector.

This is the list of questions Perplexity researches on a daily schedule.
Sam curates this list — the curation IS the moat. Add, remove, or modify
questions here. Each question produces a sourced research brief that gets
embedded into the RAG corpus.

Categories:
- daily_market: fresh every day, TTL 48h (stale market news hurts)
- weekly_analysis: deeper research, TTL 7 days
- monthly_deep_dive: thesis-level research, TTL 30 days

To add a new question: append a dict with query, category, freshness_class.
To override the system prompt for a specific question: add system_prompt key.
"""

RESEARCH_SYSTEM_PROMPT = """\
You are a financial research analyst producing investment research briefs \
for a knowledge base used by an AI financial advisor.

For each question:
- Provide a concise, factual summary (200-500 words)
- Focus on investment-relevant implications
- Include specific data points (percentages, prices, dates)
- Cite your sources
- Distinguish facts from analysis
- Note any uncertainty or conflicting information

Do NOT provide investment advice or recommend specific securities. \
Focus on education, analysis, and factual reporting.
"""

DEFAULT_RESEARCH_AGENDA = [
    # ── Daily Market Briefs (run daily, TTL 48h) ──
    {
        "query": "What are the key stock market developments today?",
        "category": "daily_market",
        "freshness_class": "daily",
        "ttl_hours": 48,
    },
    {
        "query": "What is the current state of Treasury yields and the yield curve?",
        "category": "daily_market",
        "freshness_class": "daily",
        "ttl_hours": 48,
    },
    {
        "query": "Summarize the latest Federal Reserve commentary and interest rate outlook",
        "category": "daily_market",
        "freshness_class": "daily",
        "ttl_hours": 48,
    },
    {
        "query": "What are the top-performing and worst-performing market sectors today?",
        "category": "daily_market",
        "freshness_class": "daily",
        "ttl_hours": 48,
    },
    {
        "query": "What is the current inflation data showing and how might it affect markets?",
        "category": "daily_market",
        "freshness_class": "daily",
        "ttl_hours": 48,
    },

    # ── Weekly Analysis (run daily but content is weekly scope, TTL 7d) ──
    {
        "query": "What is the current outlook for S&P 500 earnings this quarter?",
        "category": "weekly_analysis",
        "freshness_class": "weekly",
        "ttl_hours": 168,
    },
    {
        "query": "What are the key risks and opportunities in bond markets this week?",
        "category": "weekly_analysis",
        "freshness_class": "weekly",
        "ttl_hours": 168,
    },
    {
        "query": "How are international equity markets performing relative to US markets?",
        "category": "weekly_analysis",
        "freshness_class": "weekly",
        "ttl_hours": 168,
    },
    {
        "query": "What are the most significant economic indicators released this week?",
        "category": "weekly_analysis",
        "freshness_class": "weekly",
        "ttl_hours": 168,
    },
    {
        "query": "What geopolitical developments are affecting financial markets?",
        "category": "weekly_analysis",
        "freshness_class": "weekly",
        "ttl_hours": 168,
    },
]
