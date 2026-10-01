"""
India-only job location normalization.

This module converts inconsistent job-source locations into
a predictable structure that SmartHire can use for:

- India-only filtering
- city filtering
- remote filtering
- frontend display
- recommendation ranking

No external API is used here.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Optional


# =========================================================
# Result model
# =========================================================

@dataclass(frozen=True)
class NormalizedLocation:
    """
    Normalized representation of a job location.
    """

    country: Optional[str]
    city: Optional[str]
    region: Optional[str]
    display: str
    is_india: bool
    is_remote: bool
    is_valid: bool


# =========================================================
# India aliases
# =========================================================

INDIA_ALIASES = {
    "india",
    "ind",
    "bharat",
    "republic of india",
    "in",
}


# =========================================================
# Indian states / union territories
# =========================================================

INDIAN_REGIONS = {
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir",
    "jammu & kashmir": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    "chandigarh": "Chandigarh",
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "dadra and nagar haveli and daman and diu": (
        "Dadra and Nagar Haveli and Daman and Diu"
    ),
    "lakshadweep": "Lakshadweep",
}


# =========================================================
# Major Indian cities
# =========================================================

INDIAN_CITIES = {
    "bengaluru": ("Bengaluru", "Karnataka"),
    "bangalore": ("Bengaluru", "Karnataka"),

    "hyderabad": ("Hyderabad", "Telangana"),

    "chennai": ("Chennai", "Tamil Nadu"),
    "madras": ("Chennai", "Tamil Nadu"),

    "pune": ("Pune", "Maharashtra"),

    "mumbai": ("Mumbai", "Maharashtra"),
    "bombay": ("Mumbai", "Maharashtra"),

    "delhi": ("Delhi", "Delhi"),
    "new delhi": ("New Delhi", "Delhi"),

    "gurgaon": ("Gurugram", "Haryana"),
    "gurugram": ("Gurugram", "Haryana"),

    "noida": ("Noida", "Uttar Pradesh"),
    "greater noida": ("Greater Noida", "Uttar Pradesh"),

    "kolkata": ("Kolkata", "West Bengal"),
    "calcutta": ("Kolkata", "West Bengal"),

    "ahmedabad": ("Ahmedabad", "Gujarat"),

    "jaipur": ("Jaipur", "Rajasthan"),

    "kochi": ("Kochi", "Kerala"),
    "cochin": ("Kochi", "Kerala"),

    "thiruvananthapuram": (
        "Thiruvananthapuram",
        "Kerala",
    ),
    "trivandrum": (
        "Thiruvananthapuram",
        "Kerala",
    ),

    "coimbatore": ("Coimbatore", "Tamil Nadu"),

    "visakhapatnam": (
        "Visakhapatnam",
        "Andhra Pradesh",
    ),
    "vizag": (
        "Visakhapatnam",
        "Andhra Pradesh",
    ),

    "vijayawada": (
        "Vijayawada",
        "Andhra Pradesh",
    ),

    "tirupati": (
        "Tirupati",
        "Andhra Pradesh",
    ),

    "mysuru": ("Mysuru", "Karnataka"),
    "mysore": ("Mysuru", "Karnataka"),

    "mangaluru": ("Mangaluru", "Karnataka"),
    "mangalore": ("Mangaluru", "Karnataka"),

    "nagpur": ("Nagpur", "Maharashtra"),

    "nashik": ("Nashik", "Maharashtra"),

    "surat": ("Surat", "Gujarat"),

    "vadodara": ("Vadodara", "Gujarat"),
    "baroda": ("Vadodara", "Gujarat"),

    "lucknow": ("Lucknow", "Uttar Pradesh"),

    "kanpur": ("Kanpur", "Uttar Pradesh"),

    "patna": ("Patna", "Bihar"),

    "bhubaneswar": ("Bhubaneswar", "Odisha"),

    "indore": ("Indore", "Madhya Pradesh"),

    "bhopal": ("Bhopal", "Madhya Pradesh"),

    "chandigarh": ("Chandigarh", "Chandigarh"),

    "dehradun": ("Dehradun", "Uttarakhand"),

    "ranchi": ("Ranchi", "Jharkhand"),

    "guwahati": ("Guwahati", "Assam"),
}


# =========================================================
# Invalid / misleading location values
# =========================================================

INVALID_LOCATION_VALUES = {
    "united nations",
    "worldwide",
    "global",
    "anywhere",
    "international",
    "multiple locations",
    "various locations",
    "unknown",
    "n/a",
    "na",
    "not specified",
}


# =========================================================
# Foreign-country indicators
# =========================================================

FOREIGN_COUNTRIES = {
    "united states",
    "usa",
    "us",
    "u.s.",
    "united kingdom",
    "uk",
    "u.k.",
    "canada",
    "australia",
    "singapore",
    "germany",
    "france",
    "ireland",
    "netherlands",
    "japan",
    "china",
    "south korea",
    "switzerland",
    "spain",
    "italy",
    "poland",
    "brazil",
    "mexico",
    "new zealand",
    "united arab emirates",
    "uae",
    "dubai",
}


# =========================================================
# Utility functions
# =========================================================

def _clean(value: Optional[str]) -> str:
    """
    Normalize whitespace, punctuation and unicode.
    """

    if not value:
        return ""

    value = unicodedata.normalize("NFKC", str(value))

    value = value.replace("\n", " ")
    value = value.replace("\r", " ")
    value = value.replace("\t", " ")

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _lower(value: str) -> str:
    return value.casefold().strip()


def _contains_india(value: str) -> bool:
    """
    Detect explicit India references.
    """

    normalized = _lower(value)

    if normalized in INDIA_ALIASES:
        return True

    if re.search(r"\bindia\b", normalized):
        return True

    if re.search(r"\bभारत\b", normalized):
        return True

    return False


def _contains_foreign_country(value: str) -> bool:
    normalized = _lower(value)

    for country in FOREIGN_COUNTRIES:
        if re.search(
            rf"(?<![a-z]){re.escape(country)}(?![a-z])",
            normalized,
        ):
            return True

    return False


def _is_remote(value: str, remote_type: Optional[str]) -> bool:
    combined = f"{value} {remote_type or ''}".casefold()

    remote_terms = (
        "remote",
        "work from home",
        "wfh",
        "work-from-home",
    )

    return any(term in combined for term in remote_terms)


def _find_city(value: str) -> Optional[tuple[str, str]]:
    normalized = _lower(value)

    # Longest match first so "greater noida" is
    # checked before "noida".
    cities = sorted(
        INDIAN_CITIES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, result in cities:
        if re.search(
            rf"(?<![a-z]){re.escape(alias)}(?![a-z])",
            normalized,
        ):
            return result

    return None


def _find_region(value: str) -> Optional[str]:
    normalized = _lower(value)

    regions = sorted(
        INDIAN_REGIONS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, display_name in regions:
        if re.search(
            rf"(?<![a-z]){re.escape(alias)}(?![a-z])",
            normalized,
        ):
            return display_name

    return None


# =========================================================
# Main normalizer
# =========================================================

def normalize_location(
    raw_location: Optional[str],
    remote_type: Optional[str] = None,
) -> NormalizedLocation:
    """
    Normalize a job location.

    Examples:

        "Bangalore, Karnataka, India"
        -> Bengaluru, Karnataka, India

        "Hyderabad, India"
        -> Hyderabad, Telangana, India

        "Remote - India"
        -> India / Remote

        "United States"
        -> invalid / non-India

        "United Nations"
        -> invalid
    """

    raw = _clean(raw_location)

    remote = _is_remote(raw, remote_type)

    if not raw:
        return NormalizedLocation(
            country=None,
            city=None,
            region=None,
            display="",
            is_india=False,
            is_remote=remote,
            is_valid=False,
        )

    lowered = _lower(raw)

    # -----------------------------------------------------
    # Explicitly invalid values
    # -----------------------------------------------------

    if lowered in INVALID_LOCATION_VALUES:
        return NormalizedLocation(
            country=None,
            city=None,
            region=None,
            display="",
            is_india=False,
            is_remote=remote,
            is_valid=False,
        )

    # -----------------------------------------------------
    # Explicit foreign location
    # -----------------------------------------------------

    if _contains_foreign_country(raw) and not _contains_india(raw):
        return NormalizedLocation(
            country=None,
            city=None,
            region=None,
            display=raw,
            is_india=False,
            is_remote=remote,
            is_valid=False,
        )

    # -----------------------------------------------------
    # Detect India
    # -----------------------------------------------------

    india = _contains_india(raw)

    # A recognized Indian city or state is sufficient
    # evidence that this is an Indian job.
    city_result = _find_city(raw)
    region = _find_region(raw)

    if city_result:
        city, city_region = city_result

        if not region:
            region = city_region

        india = True

    # -----------------------------------------------------
    # If only India is specified
    # -----------------------------------------------------

    if india:
        if city_result:
            city = city_result[0]
        else:
            city = None

        if remote:
            if city:
                display = f"Remote — {city}, India"
            else:
                display = "Remote — India"
        elif city and region:
            display = f"{city}, {region}, India"
        elif city:
            display = f"{city}, India"
        elif region:
            display = f"{region}, India"
        else:
            display = "India"

        return NormalizedLocation(
            country="India",
            city=city,
            region=region,
            display=display,
            is_india=True,
            is_remote=remote,
            is_valid=True,
        )

    # -----------------------------------------------------
    # Unknown location
    #
    # We deliberately DO NOT assume it is India.
    # -----------------------------------------------------

    return NormalizedLocation(
        country=None,
        city=None,
        region=None,
        display=raw,
        is_india=False,
        is_remote=remote,
        is_valid=False,
    )


# =========================================================
# Convenience helper
# =========================================================

def is_india_location(
    raw_location: Optional[str],
    remote_type: Optional[str] = None,
) -> bool:
    """
    Return True only when the location can confidently
    be classified as India.
    """

    result = normalize_location(
        raw_location,
        remote_type,
    )

    return result.is_valid and result.is_india