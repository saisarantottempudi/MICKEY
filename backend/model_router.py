"""
Multi-model routing: sends simple queries to fast 3B model, complex ones to 8B.
Classification based on query characteristics — no LLM call needed for routing.
"""

import re

# Simple queries: greetings, single-word answers, basic math, yes/no questions
SIMPLE_PATTERNS = [
    r"^(hi|hello|hey|yo|sup|good morning|good night|thanks|thank you|bye|goodbye)\b",
    r"^what (time|day|date) is it",
    r"^(yes|no|ok|okay|sure|got it|cool|nice)\b",
    r"^\d+\s*[+\-*/]\s*\d+",  # basic math
    r"^(who|what|where|when) (is|are|was|were) \w+\??$",  # simple factual
    r"^(define|meaning of|what does .+ mean)",
    r"^(translate|convert|how do you say)",
]

# Complex queries: multi-step reasoning, code, analysis, system commands
COMPLEX_INDICATORS = [
    "explain", "analyze", "compare", "summarize", "write code", "debug",
    "help me", "how do i", "step by step", "pros and cons",
    "open", "close", "launch", "quit", "read file", "list dir", "calendar", "system info",
    "open_app", "close_app", "read_file", "list_dir", "system_info",
    "remember", "correct", "wrong", "mistake",
    "pomodoro", "timer", "note", "save note",
]

SIMPLE_MODEL = "llama3.2:latest"  # 3B — fast
COMPLEX_MODEL = "hermes3:8b"      # 8B — smart, tool-calling


def classify_query(query: str) -> str:
    """Return 'simple' or 'complex' based on query analysis."""
    lower = query.lower().strip()

    # Short queries (<15 chars) are usually simple
    if len(lower) < 15 and not any(ind in lower for ind in COMPLEX_INDICATORS):
        return "simple"

    # Check simple patterns
    for pattern in SIMPLE_PATTERNS:
        if re.search(pattern, lower):
            return "simple"

    # Check complex indicators
    for indicator in COMPLEX_INDICATORS:
        if indicator in lower:
            return "complex"

    # Long queries (>100 chars) tend to be complex
    if len(lower) > 100:
        return "complex"

    # Default: complex (safer — uses smarter model)
    return "complex"


def get_model_for_query(query: str) -> str:
    """Return the appropriate model name for this query."""
    complexity = classify_query(query)
    return SIMPLE_MODEL if complexity == "simple" else COMPLEX_MODEL


def get_routing_info(query: str) -> dict:
    """Get full routing info for debugging/display."""
    complexity = classify_query(query)
    model = SIMPLE_MODEL if complexity == "simple" else COMPLEX_MODEL
    return {
        "query": query[:50],
        "complexity": complexity,
        "model": model,
    }
