# normalizers/geo_normalizer.py
#
# Converts raw IPinfo response into the internal GeoResponse schema.
# Only the fields used downstream are extracted; all others are discarded.

from typing import Optional


def normalize(raw: dict) -> dict:
    """
    Normalize IPinfo API response to internal schema.
    
    Args:
        raw: Raw response from IPinfo API
        
    Returns:
        Normalized geo response with country, state, state_code, confidence
    """
    country = raw.get("country", "US")
    region = raw.get("region", "")
    
    state_code_mapping = _get_state_code(region)
    
    return {
        "country": country,
        "state": region or None,
        "state_code": state_code_mapping or None,
        "confidence": "default_only"
    }


def _get_state_code(region_name: Optional[str]) -> Optional[str]:
    """
    Convert full state name to two-letter code.
    IPinfo returns full names like 'California' - we need 'CA'.
    """
    if not region_name:
        return None
    
    state_map = {
        "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
        "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
        "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
        "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
        "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
        "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
        "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
        "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
        "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
        "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
        "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
        "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
        "Wisconsin": "WI", "Wyoming": "WY"
    }
    
    return state_map.get(region_name, region_name if len(region_name) == 2 else None)
