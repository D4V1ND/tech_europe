"""Tavily-powered real-time research: fill gaps a technical drawing leaves open.

Drawings are frequently under-dimensioned -- a named part series with no wall thickness, a
thread callout with no pitch, a material with no listed properties. This module queries
Tavily's live web search to look up the real-world standard value and its source, so an
incomplete extraction can be augmented with a sourced suggestion.

It is intentionally standalone and advisory: nothing in the core extract -> generate ->
validate pipeline depends on it. The UI calls it on demand.

Auth: set TAVILY_API_KEY in the environment (.env). Get a key at https://tavily.com.
"""
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

_TAVILY_URL = "https://api.tavily.com/search"


class TavilyError(RuntimeError):
    pass


def _search(query: str, *, max_results: int = 5) -> dict:
    """Call the Tavily search API and return the raw JSON (answer + results)."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise TavilyError("TAVILY_API_KEY is not set -- add it to your .env")
    resp = requests.post(_TAVILY_URL, json={
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": max_results,
    }, timeout=30)
    if resp.status_code != 200:
        raise TavilyError(f"Tavily returned {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def _first_number(text: str) -> float | None:
    """Pull the most likely numeric value from Tavily's answer -- prefer one with a mm
    unit, else the first number that looks like a dimension."""
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*mm", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"\d+(?:\.\d+)?", text)
    return float(m.group(0)) if m else None


# Nicer, field-specific phrasings; everything else falls back to a generic query.
_FIELD_QUERIES = {
    "thickness": "standard wall/plate thickness in mm",
    "diameter": "standard diameter in mm",
    "hole_diameter": "standard mounting hole diameter in mm",
    "thread_pitch": "standard thread pitch in mm",
    "fillet": "typical fillet radius in mm",
}


def research_field(spec, field: str) -> dict:
    """Look up a standard value for `field` given the part's context (from spec.notes),
    and return a suggestion shaped for the frontend TavilyQuestion card."""
    context = (getattr(spec, "notes", None) or "").strip() or "a mechanical part"
    aspect = _FIELD_QUERIES.get(field, f"typical {field.replace('_', ' ')} in mm")
    query = f"What is the {aspect} for {context}? Give the standard engineering value."

    data = _search(query)
    answer = data.get("answer") or ""
    results = data.get("results") or []
    source_url = results[0]["url"] if results else ""

    return {
        "field": field,
        "question": answer or f"Tavily found no direct value for {field}.",
        "tavily_suggestion": _first_number(answer),
        "source_url": source_url,
        "sources": [
            {"title": r.get("title", ""), "url": r.get("url", "")}
            for r in results[:5]
        ],
    }


def research_query(query: str) -> dict:
    """Free-form research about the part; returns Tavily's answer plus its sources."""
    data = _search(query)
    return {
        "answer": data.get("answer") or "No answer found.",
        "sources": [
            {"title": r.get("title", ""), "url": r.get("url", "")}
            for r in (data.get("results") or [])[:5]
        ],
    }


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "standard wall thickness for an aluminium 6061 mounting bracket"
    out = research_query(q)
    print("ANSWER:", out["answer"], "\n")
    for s in out["sources"]:
        print(" -", s["title"], "->", s["url"])
