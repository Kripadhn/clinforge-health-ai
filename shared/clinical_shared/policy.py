"""Guardrails shared across services: disclaimer and citation validation."""
import re
from typing import Iterable, List

from .config import DISCLAIMER

# Record ids are unique per table only, so citations are table-qualified: [cond:560], [med:586]
CITE = re.compile(r"\[([a-z]{2,5}:[0-9A-Za-z_-]+)\]")


def cited_ids(text: str) -> List[str]:
    return CITE.findall(text)


def citations_valid(text: str, allowed: Iterable[str]) -> bool:
    """True if the text cites at least one record and every cited id is a known record."""
    allowed = set(allowed)
    ids = cited_ids(text)
    return bool(ids) and all(i in allowed for i in ids)


def with_disclaimer(text: str) -> str:
    return text.rstrip() + "\n\n" + DISCLAIMER
