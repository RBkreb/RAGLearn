"""Query routing based on prefix parsing."""

import re
from enum import Enum
from dataclasses import dataclass


class QueryMode(Enum):
    """Query routing modes based on prefix.

    Attributes:
        DIRECT: /btw prefix - direct LLM without memory.
        BASE: /base prefix - LLM with conversation memory.
        DEFAULT: No prefix - use config default behavior.
    """

    DIRECT = "direct"
    BASE = "base"
    DEFAULT = "default"


@dataclass
class ParsedQuery:
    """Parsed query result.

    Attributes:
        mode: The routing mode determined by prefix.
        content: Query content after removing prefix.
    """

    mode: QueryMode
    content: str


class QueryParser:
    """Parser for query prefixes.

    Extracts prefix from query and determines routing mode.
    """

    PREFIX_PATTERN = re.compile(r"^(/(btw|base))\s*", re.IGNORECASE)

    def parse(self, query: str) -> ParsedQuery:
        """Parse query to extract prefix and content.

        Args:
            query: Raw user query possibly with prefix.

        Returns:
            ParsedQuery with mode and cleaned content.
        """
        match = self.PREFIX_PATTERN.match(query)
        if match:
            prefix = match.group(2).lower()
            if prefix == "btw":
                return ParsedQuery(mode=QueryMode.DIRECT, content=query[match.end() :])
            elif prefix == "base":
                return ParsedQuery(mode=QueryMode.BASE, content=query[match.end() :])
        return ParsedQuery(mode=QueryMode.DEFAULT, content=query)


class QueryRouter:
    """Router that determines execution path based on parsed query.

    Attributes:
        parser: QueryParser instance for parsing queries.
    """

    def __init__(self) -> None:
        self._parser = QueryParser()

    def route(self, query: str) -> ParsedQuery:
        """Route query to appropriate mode.

        Args:
            query: Raw user query.

        Returns:
            ParsedQuery with determined mode and content.
        """
        return self._parser.parse(query)