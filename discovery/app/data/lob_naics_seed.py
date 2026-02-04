"""Curated LOB to NAICS code mappings.

These mappings cover common Lines of Business in enterprise organizations.
NAICS codes are from the North American Industry Classification System.
"""

LOB_NAICS_MAPPINGS = [
    # Banking & Financial Services
    {"lob_pattern": "retail banking", "naics_codes": ["522110"]},
    {"lob_pattern": "commercial banking", "naics_codes": ["522110"]},
    {"lob_pattern": "investment banking", "naics_codes": ["523110"]},
    {"lob_pattern": "wealth management", "naics_codes": ["523930"]},
    {"lob_pattern": "private banking", "naics_codes": ["522110", "523930"]},
    {"lob_pattern": "asset management", "naics_codes": ["523920"]},
    {"lob_pattern": "capital markets", "naics_codes": ["523110", "523130"]},
    {"lob_pattern": "treasury", "naics_codes": ["522110", "523130"]},
    {"lob_pattern": "mortgage", "naics_codes": ["522310"]},
    {"lob_pattern": "credit cards", "naics_codes": ["522210"]},
    {"lob_pattern": "consumer lending", "naics_codes": ["522291"]},
    {"lob_pattern": "corporate banking", "naics_codes": ["522110"]},

    # Insurance
    {"lob_pattern": "life insurance", "naics_codes": ["524113"]},
    {"lob_pattern": "health insurance", "naics_codes": ["524114"]},
    {"lob_pattern": "property insurance", "naics_codes": ["524126"]},
    {"lob_pattern": "casualty insurance", "naics_codes": ["524126"]},
    {"lob_pattern": "reinsurance", "naics_codes": ["524130"]},
    {"lob_pattern": "insurance underwriting", "naics_codes": ["524126"]},
    {"lob_pattern": "claims", "naics_codes": ["524291"]},

    # Technology
    {"lob_pattern": "software", "naics_codes": ["541511", "541512"]},
    {"lob_pattern": "information technology", "naics_codes": ["541512"]},
    {"lob_pattern": "it services", "naics_codes": ["541512"]},
    {"lob_pattern": "cloud services", "naics_codes": ["518210"]},
    {"lob_pattern": "data services", "naics_codes": ["518210", "541511"]},
    {"lob_pattern": "cybersecurity", "naics_codes": ["541512"]},
    {"lob_pattern": "infrastructure", "naics_codes": ["541512", "517311"]},
    {"lob_pattern": "enterprise technology", "naics_codes": ["541512"]},

    # Healthcare
    {"lob_pattern": "healthcare", "naics_codes": ["62"]},
    {"lob_pattern": "pharmaceuticals", "naics_codes": ["325411"]},
    {"lob_pattern": "medical devices", "naics_codes": ["339112"]},
    {"lob_pattern": "clinical", "naics_codes": ["621111"]},
    {"lob_pattern": "hospital", "naics_codes": ["622110"]},

    # Professional Services
    {"lob_pattern": "consulting", "naics_codes": ["541611"]},
    {"lob_pattern": "legal", "naics_codes": ["541110"]},
    {"lob_pattern": "accounting", "naics_codes": ["541211"]},
    {"lob_pattern": "audit", "naics_codes": ["541211"]},
    {"lob_pattern": "tax", "naics_codes": ["541213"]},
    {"lob_pattern": "advisory", "naics_codes": ["541611"]},

    # Operations & Support
    {"lob_pattern": "operations", "naics_codes": ["561110"]},
    {"lob_pattern": "human resources", "naics_codes": ["541612"]},
    {"lob_pattern": "hr", "naics_codes": ["541612"]},
    {"lob_pattern": "finance", "naics_codes": ["523999"]},
    {"lob_pattern": "risk management", "naics_codes": ["524298"]},
    {"lob_pattern": "compliance", "naics_codes": ["541199"]},
    {"lob_pattern": "marketing", "naics_codes": ["541810"]},
    {"lob_pattern": "sales", "naics_codes": ["423"]},
    {"lob_pattern": "customer service", "naics_codes": ["561421"]},

    # Manufacturing & Industrial
    {"lob_pattern": "manufacturing", "naics_codes": ["31", "32", "33"]},
    {"lob_pattern": "supply chain", "naics_codes": ["493"]},
    {"lob_pattern": "logistics", "naics_codes": ["493110"]},
    {"lob_pattern": "procurement", "naics_codes": ["425120"]},

    # Retail & Consumer
    {"lob_pattern": "retail", "naics_codes": ["44", "45"]},
    {"lob_pattern": "e-commerce", "naics_codes": ["454110"]},
    {"lob_pattern": "consumer products", "naics_codes": ["311", "312", "316"]},

    # Real Estate
    {"lob_pattern": "real estate", "naics_codes": ["531"]},
    {"lob_pattern": "property management", "naics_codes": ["531311"]},
    {"lob_pattern": "facilities", "naics_codes": ["531312"]},

    # Energy & Utilities
    {"lob_pattern": "energy", "naics_codes": ["21", "22"]},
    {"lob_pattern": "oil and gas", "naics_codes": ["211"]},
    {"lob_pattern": "utilities", "naics_codes": ["22"]},
    {"lob_pattern": "renewable energy", "naics_codes": ["221114", "221115"]},

    # Telecommunications
    {"lob_pattern": "telecommunications", "naics_codes": ["517"]},
    {"lob_pattern": "wireless", "naics_codes": ["517312"]},
    {"lob_pattern": "broadband", "naics_codes": ["517311"]},

    # Media & Entertainment
    {"lob_pattern": "media", "naics_codes": ["51"]},
    {"lob_pattern": "entertainment", "naics_codes": ["71"]},
    {"lob_pattern": "publishing", "naics_codes": ["511"]},
    {"lob_pattern": "broadcasting", "naics_codes": ["515"]},

    # Transportation
    {"lob_pattern": "transportation", "naics_codes": ["48", "49"]},
    {"lob_pattern": "aviation", "naics_codes": ["481"]},
    {"lob_pattern": "shipping", "naics_codes": ["483"]},
    {"lob_pattern": "trucking", "naics_codes": ["484"]},

    # Government & Public Sector
    {"lob_pattern": "government", "naics_codes": ["92"]},
    {"lob_pattern": "public sector", "naics_codes": ["92"]},
    {"lob_pattern": "defense", "naics_codes": ["928110"]},

    # Education
    {"lob_pattern": "education", "naics_codes": ["61"]},
    {"lob_pattern": "higher education", "naics_codes": ["611310"]},
    {"lob_pattern": "training", "naics_codes": ["611430"]},
]
