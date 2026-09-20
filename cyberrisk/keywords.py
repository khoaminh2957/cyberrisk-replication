"""Appendix A of the paper, verbatim: the keyword / phrase tables used to extract cybersecurity
risk disclosures from "Item 1A Risk Factors".

A rule is (keywords, relevant_if, irrelevant_if).  A sentence fires the rule when it contains a
keyword AND (relevant_if is empty OR contains any relevant_if term) AND contains no irrelevant_if
term.  Matching is case-insensitive and by prefix at a word boundary ("attack" also captures
attacks / attacking / attacked), which is how the paper describes its algorithm (App. A.1).
"""

_CYBER_SYSTEMS = ["cyber-", "cyber", "networks", "systems", "products", "services", "datacenter",
                  "infrastructure"]

# 1. Direct description of cybersecurity risk
DIRECT = [
    (["attack"], _CYBER_SYSTEMS, ["terror", "war", "contraband", "bombs"]),
    (["threat"], _CYBER_SYSTEMS,
     ["terror", "simulator", "disease", "legal action", "competitive", "competitors", "substitute",
      "patent", "nuclear", "life", "threaten"]),
    (["computer", "information system"], ["malware", "virus", "viruses", "intrusions"], []),
    (["malicious"], ["software", "programs", "third parties", "attacks"],
     ["fires", "product sales", "warranty claim"]),
    (["breaches"], [],
     ["fiduciary duty", "fiduciary duties", "covenant", "credit", "agreement", "warranty",
      "warranties", "obligations", "regulations", "contract", "resolution"]),
    (["hacker", "hacking", "social engineering", "denial of service", "denial-of-service",
      "phishing", "cyberattack", "cyberattacks", "cyber risk", "cyber security", "cybersecurity",
      "cyber intrusions", "unauthorized access", "breach in security", "security breach"], [], []),
]

# 2. Indirect description of cybersecurity risk
INDIRECT = {
    "Company Business": [
        (["company", "regular course"], ["business", "operation", "services"], []),
        (["technology", "technologies"],
         ["computer", "information", "communication", "proprietary", "infrastructure", "reliance",
          "digital", "advances"], []),
        (["information"], ["network", "services", "systems", "confidential", "proprietary", "account"], []),
        (["electronic"], ["network", "services", "systems", "information"], []),
        (["computer", "telecommunication", "third-party", "infrastructure"],
         ["systems", "networks", "facilities"], []),
        (["collect", "store", "transmit", "retrieve", "sensitive", "critical", "protection"],
         ["data", "information"], []),
        (["it environment", "it systems", "operational systems", "communication systems",
          "critical infrastructure"], [], []),
        (["security"],
         ["network", "products", "services", "systems", "devices", "data", "infrastructure",
          "patches", "cloud", "web", "email", "vulnerabilities", "threat", "breach", "penetrate",
          "bypass", "compromised", "incidence", "incident", "circumvent", "measures", "portfolio",
          "solutions", "practices", "standards"], []),
        (["vulnerabilities"],
         ["network", "products", "services", "systems", "devices", "data", "infrastructure",
          "claims"], []),
    ],
    "Internal Consequences": [
        (["integrity", "reliability", "protect", "protection", "protecting", "prevent",
          "prevention", "preventing", "monitors", "compromise", "secure", "failure"],
         ["network", "products", "services", "systems", "data", "measures", "information"], []),
        (["gain access"], ["network", "systems", "data", "datacenter"], []),
        (["access", "accessed", "modified"], ["improper", "improperly"], []),
        (["theft", "misuse", "misusing", "modification", "destruction", "lost", "loss", "stolen",
          "steal", "disclose", "publicly disclosed"],
         ["assets", "intellectual property", "data", "information"], []),
        (["investigate", "remediate", "remediation", "recover", "repair", "replace"],
         ["network", "products", "services", "systems", "data", "measures", "efforts"], []),
        (["interruptions", "disruptions", "delays"], ["network", "services", "system"], []),
        (["degrade the user experience", "invasion", "user names", "password", "break-ins",
          "terminated agreements"], [], []),
    ],
    "Legal Consequences": [
        (["legal"], ["claims", "actions", "challenges", "liability"], []),
        (["legislative"], ["actions"], []),
        (["regulatory"], ["actions", "investigations", "agencies"], []),
        (["liability"], ["claims"], []),
        (["lawsuits", "litigation"], [], []),
    ],
    "Economic Consequences": [
        (["business"], ["adversely", "material", "harm", "disruptive", "negative"], []),
        (["operations", "services"], ["disrupt"], []),
        (["revenues"], ["reduce", "adversely", "loss", "lose"], []),
        (["cost"], ["increase", "increasing", "remedy"], []),
        (["operating results", "operating margin"], ["harm", "diminish", "reduce"], []),
        (["earnings"], ["reduce", "adversely"], []),
        (["financial"], ["harm", "diminish", "adversely", "material", "damage", "negative"], []),
        (["competitive position"], ["harm", "diminish"], []),
        (["reputation"], ["harm", "damage", "loss", "adverse"], []),
        (["brand"], ["harm", "damage"], []),
    ],
}

# Order in which indirect categories are reported as the sentence's primary type when several
# fire.  The paper does not state a precedence; this is only a reporting convention.
INDIRECT_ORDER = ["Company Business", "Internal Consequences", "Legal Consequences",
                  "Economic Consequences"]
