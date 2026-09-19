import unicodedata
import re
from dataclasses import dataclass, field
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.product_repo import ProductRepository


@dataclass
class MatchResult:
    product: Optional[dict] = None
    confidence: float = 0.0
    candidates: Optional[List[dict]] = field(default_factory=list)


class ProductMatcher:
    """Match spoken product text against the product database."""

    def __init__(self):
        self.repo = ProductRepository()

    def _normalize(self, text: str) -> str:
        """Normalize text: lowercase, NFC normalize, remove punctuation but keep letters/digits/spaces."""
        if not text:
            return ""
        text = text.lower().strip()
        # NFC normalization preserves composed characters (Devanagari, Telugu)
        text = unicodedata.normalize('NFC', text)
        # Keep letters (all scripts), marks (combining characters like matras), digits, and spaces
        # \w covers letters+digits+underscore; we also need Unicode marks (category M)
        result = []
        for ch in text:
            cat = unicodedata.category(ch)
            if cat.startswith('L') or cat.startswith('M') or cat.startswith('N') or ch in (' ', '_'):
                result.append(ch)
        text = ''.join(result)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _get_alias_text(self, alias) -> str:
        """Extract text from alias (handles both dict and string formats)."""
        if isinstance(alias, dict):
            return alias.get("text", alias.get("normalized", ""))
        return str(alias)

    async def match_product(self, db: AsyncIOMotorDatabase, shop_id: str, product_text: str) -> MatchResult:
        """Match product text against shop's products using multi-stage matching."""
        if not product_text:
            return MatchResult()

        products = await self.repo.find_all(db, shop_id, active_only=True)
        norm_text = self._normalize(product_text)

        exact_matches = []
        partial_matches = []

        for p in products:
            # Try matching against product name
            p_name = p.get("display_name", p.get("name", ""))
            p_norm = self._normalize(p_name)
            p_normalized_name = self._normalize(p.get("normalized_name", ""))

            if norm_text == p_norm or norm_text == p_normalized_name:
                exact_matches.append(p)
                continue

            # Try matching against aliases
            alias_matched = False
            for alias in p.get("aliases", []):
                alias_text = self._get_alias_text(alias)
                alias_norm = self._normalize(alias_text)
                if norm_text == alias_norm:
                    exact_matches.append(p)
                    alias_matched = True
                    break

            if alias_matched:
                continue

            # Partial matching: substring
            if norm_text in p_norm or p_norm in norm_text or norm_text in p_normalized_name:
                partial_matches.append(p)
            else:
                for alias in p.get("aliases", []):
                    alias_text = self._get_alias_text(alias)
                    alias_norm = self._normalize(alias_text)
                    if norm_text in alias_norm or alias_norm in norm_text:
                        partial_matches.append(p)
                        break

        if len(exact_matches) == 1:
            return MatchResult(product=exact_matches[0], confidence=1.0)
        if len(exact_matches) > 1:
            return MatchResult(candidates=exact_matches, confidence=0.8)

        if len(partial_matches) == 1:
            return MatchResult(product=partial_matches[0], confidence=0.6)
        if len(partial_matches) > 1:
            return MatchResult(candidates=partial_matches, confidence=0.4)

        return MatchResult()
