"""What the knowledge base is made of: the ten OWASP Top 10:2025 categories.
The text is published by OWASP under CC BY-SA 4.0: https://github.com/OWASP/Top10"""
from dataclasses import dataclass

PAGE = "https://owasp.org/Top10/2025/{slug}/"


@dataclass(frozen=True)
class CatalogEntry:
    key: str    # "A05:2025"
    name: str   # "Injection"
    slug: str   # the page name, "A05_2025-Injection"

    @property
    def title(self) -> str:
        return f"{self.key} {self.name}"

    @property
    def page_url(self) -> str:
        return PAGE.format(slug=self.slug)


CATALOG = (
    CatalogEntry("A01:2025", "Broken Access Control", "A01_2025-Broken_Access_Control"),
    CatalogEntry("A02:2025", "Security Misconfiguration", "A02_2025-Security_Misconfiguration"),
    CatalogEntry("A03:2025", "Software Supply Chain Failures", "A03_2025-Software_Supply_Chain_Failures"),
    CatalogEntry("A04:2025", "Cryptographic Failures", "A04_2025-Cryptographic_Failures"),
    CatalogEntry("A05:2025", "Injection", "A05_2025-Injection"),
    CatalogEntry("A06:2025", "Insecure Design", "A06_2025-Insecure_Design"),
    CatalogEntry("A07:2025", "Authentication Failures", "A07_2025-Authentication_Failures"),
    CatalogEntry("A08:2025", "Software or Data Integrity Failures", "A08_2025-Software_or_Data_Integrity_Failures"),
    CatalogEntry("A09:2025", "Security Logging and Alerting Failures", "A09_2025-Security_Logging_and_Alerting_Failures"),
    CatalogEntry("A10:2025", "Mishandling of Exceptional Conditions", "A10_2025-Mishandling_of_Exceptional_Conditions"),
)


def entry_for(key: str) -> CatalogEntry:
    for entry in CATALOG:
        if entry.key == key:
            return entry
    raise KeyError(f"{key} is not in the catalog")
