"""Curated database of must-read financial, economics & investment classic books."""
from __future__ import annotations

from .curated_investing_books import INVESTING_BOOKS
from .curated_economics_books import ECONOMICS_BOOKS

CURATED_BOOKS: list[dict] = [*INVESTING_BOOKS, *ECONOMICS_BOOKS]
