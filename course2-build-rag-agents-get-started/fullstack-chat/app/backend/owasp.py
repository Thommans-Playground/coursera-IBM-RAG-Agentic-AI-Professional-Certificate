"""Where the OWASP Top 10:2025 text comes from, and how we clean it.
The pages are published by OWASP under CC BY-SA 4.0: https://github.com/OWASP/Top10"""
import re

import httpx

RAW = "https://raw.githubusercontent.com/OWASP/Top10/master/2025/docs/en/{file}.md"
PAGE = "https://owasp.org/Top10/2025/{file}/"

CATEGORIES = [
    ("A01:2025", "Broken Access Control", "A01_2025-Broken_Access_Control"),
    ("A02:2025", "Security Misconfiguration", "A02_2025-Security_Misconfiguration"),
    ("A03:2025", "Software Supply Chain Failures", "A03_2025-Software_Supply_Chain_Failures"),
    ("A04:2025", "Cryptographic Failures", "A04_2025-Cryptographic_Failures"),
    ("A05:2025", "Injection", "A05_2025-Injection"),
    ("A06:2025", "Insecure Design", "A06_2025-Insecure_Design"),
    ("A07:2025", "Authentication Failures", "A07_2025-Authentication_Failures"),
    ("A08:2025", "Software or Data Integrity Failures", "A08_2025-Software_or_Data_Integrity_Failures"),
    ("A09:2025", "Security Logging and Alerting Failures", "A09_2025-Security_Logging_and_Alerting_Failures"),
    ("A10:2025", "Mishandling of Exceptional Conditions", "A10_2025-Mishandling_of_Exceptional_Conditions"),
]
FILES = {key: file for key, _, file in CATEGORIES}


def title(key: str, name: str) -> str:
    return f"{key} {name}"


def page_url(key: str) -> str:
    return PAGE.format(file=FILES[key])


def fetch_markdown(key: str) -> str:
    res = httpx.get(RAW.format(file=FILES[key]), timeout=30, follow_redirects=True)
    res.raise_for_status()
    return clean(res.text)


def clean(md: str) -> str:
    md = re.sub(r"<table>.*?</table>", "", md, flags=re.S)  # score tables are numbers, not prose
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?", "", md)  # icons and images
    md = re.sub(r"[ \t]+\n", "\n", md)
    return re.sub(r"\n{3,}", "\n\n", md).strip()
