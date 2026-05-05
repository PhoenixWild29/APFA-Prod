"""
APFA Advisor Evaluation Harness

Runs benchmark queries against /generate-advice and evaluates:
1. Concept coverage — does the response contain expected concepts?
2. Non-investment leak detection — mortgage/tax/insurance/loan language?
3. Grounding score — references specific data, not vague generalities?
4. Retrieval quality (recall@k) — did the retriever surface relevant docs?
5. Response quality — length, disclaimer, investment focus

Each query runs N trials (default 3) to control for LLM nondeterminism.
Results are saved to JSON for before/after comparison across runs.

Usage:
    # Against production (N=3 trials)
    python tests/eval_advisor.py --base-url https://apfa.secureai.dev \\
        --username admin --password <pw>

    # Quick single-trial run
    python tests/eval_advisor.py --base-url https://apfa.secureai.dev \\
        --username admin --password <pw> --trials 1

    # Against local backend
    python tests/eval_advisor.py --base-url http://localhost:8000 \\
        --username admin --password <pw>

Ship criteria (from CoWork review):
    - Temporal category: ≥+10% concept coverage vs baseline
    - All other categories: no regression beyond 3% (with N=3)
    - Non-investment leak count: must not increase vs baseline
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

# ── Benchmark Queries ──────────────────────────────────────────────
# Target: 8+ queries per category, ~80 total
# Each query has:
#   - query: the question to send
#   - expected_concepts: keywords/phrases that should appear in a good answer
#   - grounding_signal: regex patterns that indicate specific data references
#   - category: for grouping results

BENCHMARK_QUERIES = [
    # ── Fundamentals (10) ──
    {"query": "What are the key factors that affect interest rates?",
     "expected_concepts": ["federal reserve", "inflation", "monetary policy", "bond"],
     "grounding_signal": r"\d+%|\d+\.\d+%|basis point", "category": "fundamentals"},
    {"query": "Explain the difference between growth and value investing",
     "expected_concepts": ["growth", "value", "P/E", "earnings", "valuation"],
     "grounding_signal": r"P/E|price.to.earnings|ratio|multiple", "category": "fundamentals"},
    {"query": "What is asset allocation and why does it matter?",
     "expected_concepts": ["diversification", "risk", "stocks", "bonds", "allocation"],
     "grounding_signal": r"\d+%|60/40|portfolio", "category": "fundamentals"},
    {"query": "How do index funds compare to actively managed funds?",
     "expected_concepts": ["expense ratio", "passive", "benchmark", "S&P 500"],
     "grounding_signal": r"\d+%|basis point|expense", "category": "fundamentals"},
    {"query": "What is compound interest and how does it affect long-term investing?",
     "expected_concepts": ["compound", "time", "growth", "reinvest"],
     "grounding_signal": r"\$[\d,]+|\d+%|rule of 72", "category": "fundamentals"},
    {"query": "Explain the concept of risk-adjusted returns",
     "expected_concepts": ["risk", "return", "sharpe", "volatility"],
     "grounding_signal": r"sharpe|sortino|ratio|standard deviation", "category": "fundamentals"},
    {"query": "What is the efficient market hypothesis?",
     "expected_concepts": ["efficient", "market", "price", "information"],
     "grounding_signal": r"weak|semi.strong|strong|random walk", "category": "fundamentals"},
    {"query": "How do dividends work and why do companies pay them?",
     "expected_concepts": ["dividend", "shareholders", "income", "yield"],
     "grounding_signal": r"\d+%|yield|payout|quarterly", "category": "fundamentals"},
    {"query": "What is inflation and how does it impact investments?",
     "expected_concepts": ["inflation", "purchasing power", "real return", "hedge"],
     "grounding_signal": r"\d+%|CPI|real return|TIPS", "category": "fundamentals"},
    {"query": "Explain the relationship between risk and return in investing",
     "expected_concepts": ["risk", "return", "higher", "volatility", "premium"],
     "grounding_signal": r"premium|equity|bond|historical|\d+%", "category": "fundamentals"},

    # ── Markets (10) ──
    {"query": "What drives equity market valuations?",
     "expected_concepts": ["earnings", "interest rate", "sentiment", "valuation"],
     "grounding_signal": r"P/E|forward|multiple|yield", "category": "markets"},
    {"query": "How does the Federal Reserve's monetary policy impact different asset classes?",
     "expected_concepts": ["fed", "rate", "bonds", "equities", "inflation"],
     "grounding_signal": r"basis point|\d+%|tighten|ease", "category": "markets"},
    {"query": "What is the yield curve and what does an inversion signal?",
     "expected_concepts": ["yield curve", "inversion", "recession", "treasury"],
     "grounding_signal": r"2.year|10.year|spread|basis", "category": "markets"},
    {"query": "Explain market capitalization and stock classification",
     "expected_concepts": ["market cap", "large cap", "small cap", "mid cap"],
     "grounding_signal": r"\$[\d.]+ ?(billion|trillion|B|T)|Russell|S&P", "category": "markets"},
    {"query": "What are the main differences between stocks and bonds?",
     "expected_concepts": ["equity", "debt", "dividend", "interest", "risk"],
     "grounding_signal": r"yield|coupon|dividend|\d+%", "category": "markets"},
    {"query": "How do geopolitical events affect financial markets?",
     "expected_concepts": ["geopolitical", "uncertainty", "volatility", "risk"],
     "grounding_signal": r"oil|currency|flight to safety|VIX", "category": "markets"},
    {"query": "What is market volatility and how is it measured?",
     "expected_concepts": ["volatility", "VIX", "standard deviation", "risk"],
     "grounding_signal": r"VIX|\d+%|standard deviation|implied", "category": "markets"},
    {"query": "Explain how currency exchange rates impact international investments",
     "expected_concepts": ["currency", "exchange", "hedg", "international"],
     "grounding_signal": r"dollar|euro|hedge|unhedged|FX", "category": "markets"},
    {"query": "What causes stock market corrections and bear markets?",
     "expected_concepts": ["correction", "bear", "decline", "recovery"],
     "grounding_signal": r"10%|20%|historical|recession|recovery", "category": "markets"},
    {"query": "How do corporate earnings reports affect stock prices?",
     "expected_concepts": ["earnings", "EPS", "guidance", "revenue", "surprise"],
     "grounding_signal": r"EPS|beat|miss|guidance|quarter", "category": "markets"},

    # ── Portfolio Strategy (10) ──
    {"query": "Walk me through portfolio diversification strategies",
     "expected_concepts": ["diversif", "correlation", "asset class", "risk"],
     "grounding_signal": r"correlation|sector|international", "category": "portfolio"},
    {"query": "What is dollar-cost averaging and when should I use it?",
     "expected_concepts": ["dollar.cost", "averaging", "regular", "volatility"],
     "grounding_signal": r"\$[\d,]+|monthly|periodic", "category": "portfolio"},
    {"query": "How should I think about risk tolerance in my portfolio?",
     "expected_concepts": ["risk tolerance", "time horizon", "age", "volatility"],
     "grounding_signal": r"year|horizon|aggressive|conservative", "category": "portfolio"},
    {"query": "What is rebalancing and how often should I do it?",
     "expected_concepts": ["rebalanc", "target", "drift", "allocation"],
     "grounding_signal": r"quarterly|annual|threshold|\d+%", "category": "portfolio"},
    {"query": "Explain the concept of tax-loss harvesting",
     "expected_concepts": ["tax.loss", "harvest", "capital gain", "wash sale"],
     "grounding_signal": r"\$[\d,]+|30.day|offset", "category": "portfolio"},
    {"query": "What is the glide path concept in target-date funds?",
     "expected_concepts": ["glide path", "target.date", "equity", "bond", "retirement"],
     "grounding_signal": r"age|retirement|\d+%|equity allocation", "category": "portfolio"},
    {"query": "How do I build an income-generating portfolio?",
     "expected_concepts": ["income", "dividend", "bond", "yield", "distribution"],
     "grounding_signal": r"\d+%|yield|dividend|coupon", "category": "portfolio"},
    {"query": "What is factor investing and how does it work?",
     "expected_concepts": ["factor", "value", "momentum", "size", "quality"],
     "grounding_signal": r"Fama|French|factor|smart beta", "category": "portfolio"},
    {"query": "How should I allocate between domestic and international investments?",
     "expected_concepts": ["domestic", "international", "emerging", "developed"],
     "grounding_signal": r"\d+%|MSCI|developed|emerging", "category": "portfolio"},
    {"query": "What is the core-satellite portfolio strategy?",
     "expected_concepts": ["core", "satellite", "index", "active", "alpha"],
     "grounding_signal": r"core|satellite|index|alpha|\d+%", "category": "portfolio"},

    # ── Instruments (10) ──
    {"query": "What are ETFs and how do they differ from mutual funds?",
     "expected_concepts": ["ETF", "mutual fund", "trade", "expense", "tax"],
     "grounding_signal": r"expense ratio|intraday|NAV|\d+%", "category": "instruments"},
    {"query": "What are Treasury bonds and why are they considered safe?",
     "expected_concepts": ["treasury", "government", "risk.free", "yield"],
     "grounding_signal": r"T.bill|T.note|T.bond|\d+.year|yield", "category": "instruments"},
    {"query": "Explain REITs and their role in a portfolio",
     "expected_concepts": ["REIT", "real estate", "dividend", "income"],
     "grounding_signal": r"dividend|yield|\d+%|income", "category": "instruments"},
    {"query": "What are options and how do investors use them?",
     "expected_concepts": ["option", "call", "put", "strike", "premium"],
     "grounding_signal": r"strike|expir|premium|contract", "category": "instruments"},
    {"query": "What is a dividend reinvestment plan (DRIP)?",
     "expected_concepts": ["dividend", "reinvest", "compound", "shares"],
     "grounding_signal": r"compound|shares|automatic", "category": "instruments"},
    {"query": "Explain corporate bonds and their risk profile",
     "expected_concepts": ["corporate bond", "credit", "yield", "default"],
     "grounding_signal": r"investment grade|high yield|rating|spread", "category": "instruments"},
    {"query": "What are commodities and how do investors gain exposure?",
     "expected_concepts": ["commodity", "gold", "oil", "futures", "ETF"],
     "grounding_signal": r"gold|oil|futures|ETF|physical", "category": "instruments"},
    {"query": "How do money market funds work?",
     "expected_concepts": ["money market", "short.term", "liquid", "yield", "safe"],
     "grounding_signal": r"NAV|\$1|T.bill|yield|\d+%", "category": "instruments"},
    {"query": "What are convertible bonds?",
     "expected_concepts": ["convertible", "bond", "equity", "conversion", "hybrid"],
     "grounding_signal": r"conversion|ratio|premium|equity|upside", "category": "instruments"},
    {"query": "Explain the differences between growth ETFs and value ETFs",
     "expected_concepts": ["growth", "value", "ETF", "index", "style"],
     "grounding_signal": r"Russell|S&P|P/E|expense|\d+%", "category": "instruments"},

    # ── RAG Grounding (8) ──
    {"query": "What do you know about AI infrastructure investment opportunities?",
     "expected_concepts": ["AI", "infrastructure", "invest"],
     "grounding_signal": r"source|document|according|research", "category": "rag_grounding"},
    {"query": "Summarize the key themes from the investment research in your knowledge base",
     "expected_concepts": ["research", "theme", "investment"],
     "grounding_signal": r"document|source|knowledge base|corpus", "category": "rag_grounding"},
    {"query": "What investment documents have been analyzed in your system?",
     "expected_concepts": ["document", "research", "analysis"],
     "grounding_signal": r"source|document|uploaded|ingested|knowledge", "category": "rag_grounding"},
    {"query": "Based on the research you have access to, what sectors look promising?",
     "expected_concepts": ["sector", "research", "growth"],
     "grounding_signal": r"source|according|document|data", "category": "rag_grounding"},
    {"query": "What does your data say about portfolio construction best practices?",
     "expected_concepts": ["portfolio", "construct", "allocation"],
     "grounding_signal": r"source|research|document|according|data", "category": "rag_grounding"},
    {"query": "Can you reference any specific research about market trends?",
     "expected_concepts": ["research", "market", "trend"],
     "grounding_signal": r"source|document|according|cited|reference", "category": "rag_grounding"},
    {"query": "What financial regulations are covered in your knowledge base?",
     "expected_concepts": ["regulation", "compliance", "financial"],
     "grounding_signal": r"source|document|regulation|SEC|FINRA", "category": "rag_grounding"},
    {"query": "Summarize the investment thesis documents you have access to",
     "expected_concepts": ["thesis", "investment", "document"],
     "grounding_signal": r"source|document|thesis|research|according", "category": "rag_grounding"},

    # ── Temporal Freshness (10) ──
    {"query": "What is the latest market outlook?",
     "expected_concepts": ["market", "outlook", "current"],
     "grounding_signal": r"2026|recent|current|latest|today", "category": "temporal"},
    {"query": "What are current Treasury yields?",
     "expected_concepts": ["treasury", "yield", "current"],
     "grounding_signal": r"\d+\.\d+%|current|today|recent", "category": "temporal"},
    {"query": "How have equity markets performed recently?",
     "expected_concepts": ["equity", "market", "performance"],
     "grounding_signal": r"recent|2026|this year|quarter|month", "category": "temporal"},
    {"query": "What is the current state of inflation?",
     "expected_concepts": ["inflation", "CPI", "current", "rate"],
     "grounding_signal": r"\d+\.\d+%|current|2026|recent|CPI", "category": "temporal"},
    {"query": "What is the Fed's latest stance on interest rates?",
     "expected_concepts": ["fed", "interest rate", "policy", "recent"],
     "grounding_signal": r"2026|recent|latest|FOMC|meeting", "category": "temporal"},
    {"query": "How are tech stocks performing this year?",
     "expected_concepts": ["tech", "stock", "performance", "year"],
     "grounding_signal": r"2026|YTD|this year|NASDAQ|recent", "category": "temporal"},
    {"query": "What are the most recent economic indicators showing?",
     "expected_concepts": ["economic", "indicator", "recent", "data"],
     "grounding_signal": r"GDP|unemployment|CPI|recent|2026|latest", "category": "temporal"},
    {"query": "What happened in markets this quarter?",
     "expected_concepts": ["market", "quarter", "performance"],
     "grounding_signal": r"Q[1-4]|quarter|2026|recent|this", "category": "temporal"},
    {"query": "Are there any recent changes to SEC regulations affecting investors?",
     "expected_concepts": ["SEC", "regulation", "recent", "change"],
     "grounding_signal": r"2026|recent|new|updated|proposed", "category": "temporal"},
    {"query": "What is the current outlook for bond markets?",
     "expected_concepts": ["bond", "market", "outlook", "yield"],
     "grounding_signal": r"2026|current|yield|\d+%|recent", "category": "temporal"},

    # ── Boundary (refuse/redirect) (8) ──
    {"query": "What mortgage rate can I get with a 720 credit score?",
     "expected_concepts": ["investment", "consult", "mortgage advisor"],
     "grounding_signal": r"focus on investment|licensed|mortgage advisor|portfolio", "category": "boundary"},
    {"query": "How do I file my taxes for capital gains?",
     "expected_concepts": ["consult", "tax professional"],
     "grounding_signal": r"focus on investment|tax professional|CPA|portfolio", "category": "boundary"},
    {"query": "What insurance should I get for my rental property?",
     "expected_concepts": ["consult", "insurance"],
     "grounding_signal": r"focus on investment|insurance|professional|portfolio", "category": "boundary"},
    {"query": "Can you help me calculate my DTI ratio for a home loan?",
     "expected_concepts": ["investment", "consult", "mortgage"],
     "grounding_signal": r"focus on investment|licensed|lender|portfolio", "category": "boundary"},
    {"query": "What are FHA loan requirements?",
     "expected_concepts": ["investment", "consult", "mortgage"],
     "grounding_signal": r"focus on investment|licensed|mortgage|housing", "category": "boundary"},
    {"query": "Should I refinance my car loan?",
     "expected_concepts": ["investment", "consult"],
     "grounding_signal": r"focus on investment|financial advisor|portfolio", "category": "boundary"},
    {"query": "How much life insurance do I need?",
     "expected_concepts": ["consult", "insurance"],
     "grounding_signal": r"focus on investment|insurance professional|agent", "category": "boundary"},
    {"query": "What tax deductions can I claim for my home office?",
     "expected_concepts": ["consult", "tax"],
     "grounding_signal": r"focus on investment|tax professional|CPA|accountant", "category": "boundary"},

    # ── Edge Cases (8) ──
    {"query": "What is a good investment strategy for a 25-year-old?",
     "expected_concepts": ["time horizon", "risk", "growth", "allocation"],
     "grounding_signal": r"year|aggressive|equity|\d+%", "category": "edge_cases"},
    {"query": "Should I invest in individual stocks or index funds?",
     "expected_concepts": ["individual", "index", "diversif", "risk"],
     "grounding_signal": r"expense ratio|S&P|diversif", "category": "edge_cases"},
    {"query": "What happens to my investments during a recession?",
     "expected_concepts": ["recession", "decline", "recovery", "diversif"],
     "grounding_signal": r"historical|recovery|\d+%|year", "category": "edge_cases"},
    {"query": "How do I start investing with only $500?",
     "expected_concepts": ["start", "small", "ETF", "index"],
     "grounding_signal": r"\$500|\$[\d,]+|fractional|micro", "category": "edge_cases"},
    {"query": "What is the difference between a Roth IRA and a traditional IRA?",
     "expected_concepts": ["Roth", "traditional", "IRA", "tax"],
     "grounding_signal": r"\$[\d,]+|tax.deduct|tax.free|contribution", "category": "edge_cases"},
    {"query": "Is it better to pay off debt or invest?",
     "expected_concepts": ["debt", "invest", "interest", "return", "opportunity"],
     "grounding_signal": r"\d+%|interest rate|return|compare", "category": "edge_cases"},
    {"query": "How much should I have in an emergency fund before investing?",
     "expected_concepts": ["emergency", "fund", "months", "liquid", "invest"],
     "grounding_signal": r"3.6 months|6 months|\$[\d,]+|expenses", "category": "edge_cases"},
    {"query": "What is the impact of fees on long-term investment returns?",
     "expected_concepts": ["fee", "expense", "compound", "return", "long.term"],
     "grounding_signal": r"\d+%|basis point|compound|\$[\d,]+", "category": "edge_cases"},
]


# ── Non-Investment Leak Detection ──────────────────────────────────
# Generalized beyond mortgage to catch tax, insurance, loan content
# that shouldn't be primary framing in responses.

NON_INVESTMENT_PATTERNS = re.compile(
    r"\b("
    # Mortgage/loan
    r"mortgage rate|FHA loan|loan officer|DTI ratio|down payment|closing cost"
    r"|home loan|TILA|RESPA|ECOA|loan product|30.year fixed|refinanc.* (your|my) (mortgage|loan)"
    # Tax advice (not just mentioning taxes)
    r"|you should (claim|deduct|file)|tax deduction|Schedule [A-Z]|Form 1040"
    r"|itemize your|claim this deduction|tax bracket"
    # Insurance advice
    r"|you need .* insurance|insurance coverage|policy premium|deductible amount"
    r"|umbrella policy|term life"
    # Lending
    r"|apply for a loan|loan application|credit score.*(for|to get) a (loan|mortgage)"
    r")\b",
    re.IGNORECASE,
)


# ── Scoring ────────────────────────────────────────────────────────

def score_response(query_spec: dict, response_text: str) -> dict:
    """Score a single response against its benchmark spec."""
    text_lower = response_text.lower()
    scores = {}

    # 1. Concept coverage (0-100%)
    found = sum(
        1 for concept in query_spec["expected_concepts"]
        if re.search(concept, text_lower)
    )
    scores["concept_coverage"] = round(found / len(query_spec["expected_concepts"]) * 100, 1)

    # 2. Non-investment leak detection (generalized beyond mortgage)
    leak_hits = NON_INVESTMENT_PATTERNS.findall(response_text)
    scores["non_investment_leaks"] = leak_hits
    scores["leak_count"] = len(leak_hits)

    # 3. Grounding (references specific data, not vague)
    grounding_matches = re.findall(query_spec["grounding_signal"], response_text, re.IGNORECASE)
    scores["grounding_score"] = min(100, len(grounding_matches) * 20)

    # 4. Response length
    word_count = len(response_text.split())
    scores["word_count"] = word_count
    scores["length_ok"] = 50 < word_count < 2000

    # 5. Has educational disclaimer
    scores["has_disclaimer"] = (
        "educational purposes" in text_lower
        or "financial advisor" in text_lower
        or "consult a licensed" in text_lower
    )

    # 6. Overall pass/fail
    is_boundary = query_spec["category"] == "boundary"
    if is_boundary:
        # Boundary queries should redirect, not answer
        scores["pass"] = (
            scores["concept_coverage"] >= 20  # mentions consulting someone
            and scores["length_ok"]
        )
    else:
        scores["pass"] = (
            scores["concept_coverage"] >= 40
            and scores["leak_count"] == 0
            and scores["length_ok"]
        )

    return scores


# ── Runner ─────────────────────────────────────────────────────────

def get_auth_token(base_url: str, username: str, password: str) -> str:
    """Get a Bearer token from the /token endpoint."""
    resp = requests.post(
        f"{base_url}/token",
        json={"username": username, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def run_query(base_url: str, token: str, query: str, timeout: int = 60) -> dict:
    """Send a query to /generate-advice and return the response."""
    resp = requests.post(
        f"{base_url}/generate-advice",
        json={"query": query},
        headers={"Authorization": f"Bearer {token}"},
        timeout=timeout,
    )
    return {
        "status_code": resp.status_code,
        "body": resp.json() if resp.status_code == 200 else {"error": resp.text},
        "latency_ms": resp.elapsed.total_seconds() * 1000,
    }


def run_trial(base_url: str, token: str, spec: dict) -> dict:
    """Run a single query and score the response.

    Retries once on error (timeout, 500, rate limit). If both attempts
    fail, returns an error dict that is excluded from averaged scores.
    """
    for attempt in range(2):  # retry once
        try:
            resp = run_query(base_url, token, spec["query"])
            if resp["status_code"] >= 500:
                if attempt == 0:
                    time.sleep(3)
                    continue
                return {"pass": False, "error": f"HTTP {resp['status_code']}", "is_error": True}
            advice = resp["body"].get("advice", resp["body"].get("error", ""))
            scores = score_response(spec, advice)
            scores["latency_ms"] = resp["latency_ms"]
            scores["status_code"] = resp["status_code"]
            scores["response_preview"] = advice[:300]
            scores["is_error"] = False
            return scores
        except Exception as e:
            if attempt == 0:
                time.sleep(3)
                continue
            return {"pass": False, "error": str(e), "is_error": True}
    return {"pass": False, "error": "unreachable", "is_error": True}


def run_eval(base_url: str, token: str, num_trials: int = 3) -> dict:
    """Run all benchmark queries with N trials each."""
    results = []
    category_scores: dict[str, list] = {}

    for i, spec in enumerate(BENCHMARK_QUERIES):
        print(f"  [{i+1}/{len(BENCHMARK_QUERIES)}] {spec['query'][:55]}...", end=" ", flush=True)

        trial_results = []
        for trial in range(num_trials):
            trial_result = run_trial(base_url, token, spec)
            trial_results.append(trial_result)
            if trial < num_trials - 1:
                time.sleep(1)  # small delay between trials

        # Separate successful trials from errors
        valid_trials = [t for t in trial_results if not t.get("is_error")]
        error_count = len(trial_results) - len(valid_trials)

        if valid_trials:
            avg_concept = sum(t.get("concept_coverage", 0) for t in valid_trials) / len(valid_trials)
            avg_grounding = sum(t.get("grounding_score", 0) for t in valid_trials) / len(valid_trials)
            avg_latency = sum(t.get("latency_ms", 0) for t in valid_trials) / len(valid_trials)
            total_leaks = sum(t.get("leak_count", 0) for t in valid_trials)
            pass_count = sum(1 for t in valid_trials if t.get("pass"))
        else:
            avg_concept = 0
            avg_grounding = 0
            avg_latency = 0
            total_leaks = 0
            pass_count = 0

        valid_count = len(valid_trials) or 1  # avoid div by zero

        aggregated = {
            "query": spec["query"],
            "category": spec["category"],
            "num_trials": num_trials,
            "valid_trials": len(valid_trials),
            "error_count": error_count,
            # Continuous scores (for tuning — small deltas visible)
            "avg_concept_coverage": round(avg_concept, 1),
            "avg_grounding_score": round(avg_grounding, 1),
            "avg_latency_ms": round(avg_latency, 0),
            "total_leak_count": total_leaks,
            # Binary scores (for ship criteria — majority pass)
            "pass_count": pass_count,
            "pass_rate": round(pass_count / valid_count * 100, 1),
            "pass": pass_count > len(valid_trials) // 2 if valid_trials else False,
            "trials": trial_results,
        }

        status = "PASS" if aggregated["pass"] else ("ERR" if error_count == num_trials else "FAIL")
        print(f"{status} (concepts={avg_concept:.0f}%, leaks={total_leaks}, errors={error_count})")

        results.append(aggregated)
        category_scores.setdefault(spec["category"], []).append(aggregated)

        time.sleep(1)

    # Category summaries
    category_summary = {}
    for cat, cat_results in category_scores.items():
        passed = sum(1 for r in cat_results if r["pass"])
        category_summary[cat] = {
            "total": len(cat_results),
            "passed": passed,
            "pass_rate": round(passed / len(cat_results) * 100, 1),
            "avg_concept_coverage": round(
                sum(r["avg_concept_coverage"] for r in cat_results) / len(cat_results), 1
            ),
            "avg_grounding_score": round(
                sum(r["avg_grounding_score"] for r in cat_results) / len(cat_results), 1
            ),
            "avg_latency_ms": round(
                sum(r["avg_latency_ms"] for r in cat_results) / len(cat_results), 0
            ),
            "total_leaks": sum(r["total_leak_count"] for r in cat_results),
        }

    total_pass = sum(1 for r in results if r["pass"])
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "num_trials": num_trials,
        "total_queries": len(BENCHMARK_QUERIES),
        "passed": total_pass,
        "failed": len(BENCHMARK_QUERIES) - total_pass,
        "pass_rate": round(total_pass / len(BENCHMARK_QUERIES) * 100, 1),
        "total_leaks": sum(r["total_leak_count"] for r in results),
        "category_summary": category_summary,
        "ship_criteria": {
            "temporal_improvement_target": ">=+10% concept coverage vs baseline",
            "regression_threshold": "<=3% drop in any non-temporal category",
            "leak_threshold": "must not increase vs baseline",
        },
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="APFA Advisor Evaluation Harness")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default=os.environ.get("APFA_ADMIN_PASSWORD", ""))
    parser.add_argument("--trials", type=int, default=3, help="Number of trials per query (default: 3)")
    parser.add_argument("--output-dir", default="tests/eval_results")
    args = parser.parse_args()

    if not args.password:
        print("ERROR: --password required (or set APFA_ADMIN_PASSWORD env var)")
        sys.exit(1)

    print(f"APFA Advisor Evaluation")
    print(f"  Target: {args.base_url}")
    print(f"  Queries: {len(BENCHMARK_QUERIES)}")
    print(f"  Trials per query: {args.trials}")
    print(f"  Total API calls: {len(BENCHMARK_QUERIES) * args.trials}")
    print()

    # Auth
    print("Authenticating...", end=" ")
    token = get_auth_token(args.base_url, args.username, args.password)
    print("OK")
    print()

    # Run
    print("Running benchmark queries:")
    report = run_eval(args.base_url, token, num_trials=args.trials)

    # Summary
    print()
    print(f"{'='*60}")
    print(f"RESULTS: {report['passed']}/{report['total_queries']} passed ({report['pass_rate']}%)")
    print(f"Total non-investment leaks: {report['total_leaks']}")
    print()
    for cat, summary in report["category_summary"].items():
        print(f"  {cat:20s}: {summary['passed']}/{summary['total']} ({summary['pass_rate']}%) "
              f"concepts={summary['avg_concept_coverage']}% "
              f"grounding={summary['avg_grounding_score']}% "
              f"leaks={summary['total_leaks']} "
              f"latency={summary['avg_latency_ms']}ms")
    print(f"{'='*60}")

    # Save
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"eval_{timestamp}.json"
    output_file.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nResults saved to {output_file}")
    print(f"Commit this file as baseline: git add {output_file}")


if __name__ == "__main__":
    main()
