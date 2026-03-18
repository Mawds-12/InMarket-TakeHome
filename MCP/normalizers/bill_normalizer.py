# normalizers/bill_normalizer.py
#
# Converts raw Open States bill results into the internal Bill schema.
# Only the fields used downstream are extracted; all others are discarded.

from config import settings


def normalize(raw_results: list[dict]) -> list[dict]:
    """
    Normalize a list of Open States bill results.
    
    Args:
        raw_results: List of raw bill dicts from Open States API
        
    Returns:
        List of normalized bill dicts, limited by configured max
    """
    normalized = [_to_bill(r) for r in raw_results]
    
    return normalized[:settings.mcp_case_result_limit]


def _to_bill(raw: dict) -> dict:
    """
    Convert a single raw Open States result to internal Bill schema.
    
    Args:
        raw: Single bill dict from Open States API
        
    Returns:
        Normalized bill dict
    """
    # Extract sponsors - limit to first 5 to avoid bloat
    sponsorships = raw.get("sponsorships", [])
    sponsors = []
    for s in sponsorships[:5]:
        sponsor = {
            "name": s.get("name", "Unknown"),
            "primary": s.get("primary", False),
            "classification": s.get("classification", "")
        }
        # Add party if person object available
        person = s.get("person")
        if person:
            sponsor["party"] = person.get("party", "Unknown")
        sponsors.append(sponsor)
    
    return {
        "bill_id": raw.get("identifier", "Unknown"),
        "title": raw.get("title", ""),
        "state": raw.get("jurisdiction", {}).get("name", ""),
        "session": raw.get("session", {}).get("identifier", ""),
        "url": raw.get("openstates_url", ""),
        "latest_action": raw.get("latest_action_description", ""),
        "latest_action_date": raw.get("latest_action_date", ""),
        "status": raw.get("classification", []),
        "sponsors": sponsors
    }
