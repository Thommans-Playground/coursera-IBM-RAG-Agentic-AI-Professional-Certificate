"""Fetches the OWASP pages from GitHub and cleans the Markdown."""
import re

import httpx

from chatapp.knowledge.domain.catalog import entry_for

RAW = "https://raw.githubusercontent.com/OWASP/Top10/master/2025/docs/en/{slug}.md"


def clean(md: str) -> str:
    md = re.sub(r"<table>.*?</table>", "", md, flags=re.S)  # score tables are numbers, not prose
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?", "", md)  # icons and images
    md = re.sub(r"[ \t]+\n", "\n", md)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


class GithubOwaspSource:
    async def fetch(self, key: str) -> str:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            res = await client.get(RAW.format(slug=entry_for(key).slug))  # the domain knows the page name
        res.raise_for_status()
        return clean(res.text)
