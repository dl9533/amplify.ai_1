"""BLS Supersector to NAICS Sector mappings.

Based on U.S. Bureau of Labor Statistics industry classification system.
NAICS = North American Industry Classification System (2-digit sector codes).

Reference: https://www.bls.gov/iag/tgs/iag_index_naics.htm
"""

from typing import TypedDict


class NaicsSector(TypedDict):
    """A 2-digit NAICS sector."""

    code: str
    label: str


class Supersector(TypedDict):
    """A BLS supersector containing one or more NAICS sectors."""

    code: str
    label: str
    sectors: list[NaicsSector]


SUPERSECTORS: list[Supersector] = [
    {
        "code": "NATURAL_RESOURCES",
        "label": "Natural Resources & Mining",
        "sectors": [
            {"code": "11", "label": "Agriculture, Forestry, Fishing & Hunting"},
            {"code": "21", "label": "Mining, Quarrying & Oil/Gas Extraction"},
        ],
    },
    {
        "code": "CONSTRUCTION",
        "label": "Construction",
        "sectors": [
            {"code": "23", "label": "Construction"},
        ],
    },
    {
        "code": "MANUFACTURING",
        "label": "Manufacturing",
        "sectors": [
            {"code": "31", "label": "Manufacturing - Food, Beverage & Textile"},
            {"code": "32", "label": "Manufacturing - Wood, Paper, Chemical & Plastics"},
            {"code": "33", "label": "Manufacturing - Metal, Machinery & Electronics"},
        ],
    },
    {
        "code": "TRADE_TRANSPORT_UTILITIES",
        "label": "Trade, Transportation & Utilities",
        "sectors": [
            {"code": "22", "label": "Utilities"},
            {"code": "42", "label": "Wholesale Trade"},
            {"code": "44", "label": "Retail Trade - Motor Vehicles, Furniture & Electronics"},
            {"code": "45", "label": "Retail Trade - Sporting Goods & General Merchandise"},
            {"code": "48", "label": "Transportation"},
            {"code": "49", "label": "Warehousing & Postal Services"},
        ],
    },
    {
        "code": "INFORMATION",
        "label": "Information",
        "sectors": [
            {"code": "51", "label": "Information"},
        ],
    },
    {
        "code": "FINANCIAL_ACTIVITIES",
        "label": "Financial Activities",
        "sectors": [
            {"code": "52", "label": "Finance & Insurance"},
            {"code": "53", "label": "Real Estate & Rental/Leasing"},
        ],
    },
    {
        "code": "PROFESSIONAL_BUSINESS",
        "label": "Professional & Business Services",
        "sectors": [
            {"code": "54", "label": "Professional, Scientific & Technical Services"},
            {"code": "55", "label": "Management of Companies & Enterprises"},
            {"code": "56", "label": "Administrative & Support Services"},
        ],
    },
    {
        "code": "EDUCATION_HEALTH",
        "label": "Education & Health Services",
        "sectors": [
            {"code": "61", "label": "Educational Services"},
            {"code": "62", "label": "Health Care & Social Assistance"},
        ],
    },
    {
        "code": "LEISURE_HOSPITALITY",
        "label": "Leisure & Hospitality",
        "sectors": [
            {"code": "71", "label": "Arts, Entertainment & Recreation"},
            {"code": "72", "label": "Accommodation & Food Services"},
        ],
    },
    {
        "code": "OTHER_SERVICES",
        "label": "Other Services",
        "sectors": [
            {"code": "81", "label": "Other Services (except Public Administration)"},
        ],
    },
    {
        "code": "GOVERNMENT",
        "label": "Government",
        "sectors": [
            {"code": "92", "label": "Public Administration"},
        ],
    },
]


def get_supersector_for_naics(naics_code: str) -> Supersector | None:
    """Find the supersector containing a given NAICS sector code."""
    for supersector in SUPERSECTORS:
        for sector in supersector["sectors"]:
            if sector["code"] == naics_code:
                return supersector
    return None


def get_sector_label(naics_code: str) -> str | None:
    """Get the label for a NAICS sector code."""
    for supersector in SUPERSECTORS:
        for sector in supersector["sectors"]:
            if sector["code"] == naics_code:
                return sector["label"]
    return None


def get_all_naics_codes() -> list[str]:
    """Get all valid 2-digit NAICS sector codes."""
    codes = []
    for supersector in SUPERSECTORS:
        for sector in supersector["sectors"]:
            codes.append(sector["code"])
    return codes


# Flat list of all sectors for validation
VALID_NAICS_SECTORS = get_all_naics_codes()
