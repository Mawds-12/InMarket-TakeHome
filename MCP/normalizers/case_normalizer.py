# normalizers/case_normalizer.py
#
# Converts raw CourtListener opinion results into the internal Case schema.
# Only the fields used downstream are extracted; all others are discarded.

from typing import Optional
from config import settings


def normalize(raw_results: list[dict]) -> list[dict]:
    """
    Normalize a list of CourtListener case results.
    
    Args:
        raw_results: List of raw case dicts from CourtListener API
        
    Returns:
        List of normalized case dicts, limited by configured max
    """
    normalized = [_to_case(r) for r in raw_results]
    
    sorted_results = sorted(normalized, key=lambda c: c["raw_score"], reverse=True)
    
    return sorted_results[:settings.mcp_case_result_limit]


def _to_case(raw: dict) -> dict:
    """
    Convert a single raw CourtListener result to internal Case schema.
    
    Args:
        raw: Single case dict from CourtListener API
        
    Returns:
        Normalized case dict
    """
    citations = raw.get("citation", [])
    citation = citations[0] if citations else None
    
    return {
        "case_name": raw.get("caseName", "Unknown Case"),
        "court": raw.get("court", ""),
        "date": raw.get("dateFiled", ""),
        "citation": citation,
        "snippet": raw.get("snippet", ""),
        "url": raw.get("absolute_url", ""),
        "raw_score": float(raw.get("score", 0.0))
    }
