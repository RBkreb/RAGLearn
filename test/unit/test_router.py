"""Unit tests for router.py - QueryParser and QueryRouter."""

import pytest

from src.router import QueryMode, QueryParser, QueryRouter, ParsedQuery


class TestQueryParser:
    """Tests for QueryParser.parse() method."""

    def test_parse_with_btw_prefix_lowercase(self):
        """Test /btw prefix (lowercase) returns DIRECT mode."""
        parser = QueryParser()
        query = "/btw what is the meaning of life"

        result = parser.parse(query)

        assert result.mode == QueryMode.DIRECT
        assert result.content == "what is the meaning of life"

    def test_parse_with_btw_prefix_uppercase(self):
        """Test /BTW prefix (uppercase) returns DIRECT mode."""
        parser = QueryParser()
        query = "/BTW what is the meaning of life"

        result = parser.parse(query)

        assert result.mode == QueryMode.DIRECT
        assert result.content == "what is the meaning of life"

    def test_parse_with_btw_prefix_mixed_case(self):
        """Test /Btw prefix (mixed case) returns DIRECT mode."""
        parser = QueryParser()
        query = "/Btw what is the meaning of life"

        result = parser.parse(query)

        assert result.mode == QueryMode.DIRECT
        assert result.content == "what is the meaning of life"

    def test_parse_with_btw_prefix_no_space(self):
        """Test /btw prefix without trailing space."""
        parser = QueryParser()
        query = "/btwhello world"

        result = parser.parse(query)

        assert result.mode == QueryMode.DIRECT
        assert result.content == "hello world"

    def test_parse_with_base_prefix_lowercase(self):
        """Test /base prefix (lowercase) returns BASE mode."""
        parser = QueryParser()
        query = "/base what is python"

        result = parser.parse(query)

        assert result.mode == QueryMode.BASE
        assert result.content == "what is python"

    def test_parse_with_base_prefix_uppercase(self):
        """Test /BASE prefix (uppercase) returns BASE mode."""
        parser = QueryParser()
        query = "/BASE what is python"

        result = parser.parse(query)

        assert result.mode == QueryMode.BASE
        assert result.content == "what is python"

    def test_parse_with_base_prefix_mixed_case(self):
        """Test /BaSe prefix (mixed case) returns BASE mode."""
        parser = QueryParser()
        query = "/BaSe what is python"

        result = parser.parse(query)

        assert result.mode == QueryMode.BASE
        assert result.content == "what is python"

    def test_parse_with_base_prefix_no_space(self):
        """Test /base prefix without trailing space."""
        parser = QueryParser()
        query = "/basehello"

        result = parser.parse(query)

        assert result.mode == QueryMode.BASE
        assert result.content == "hello"

    def test_parse_no_prefix_returns_default(self):
        """Test query without prefix returns DEFAULT mode."""
        parser = QueryParser()
        query = "what is the weather today"

        result = parser.parse(query)

        assert result.mode == QueryMode.DEFAULT
        assert result.content == "what is the weather today"

    def test_parse_empty_query_returns_default(self):
        """Test empty query returns DEFAULT mode with empty content."""
        parser = QueryParser()
        query = ""

        result = parser.parse(query)

        assert result.mode == QueryMode.DEFAULT
        assert result.content == ""

    def test_parse_query_with_only_prefix(self):
        """Test query with only /btw or /base prefix."""
        parser = QueryParser()

        result_btw = parser.parse("/btw")
        assert result_btw.mode == QueryMode.DIRECT
        assert result_btw.content == ""

        result_base = parser.parse("/base")
        assert result_base.mode == QueryMode.BASE
        assert result_base.content == ""

    def test_parse_whitespace_before_prefix(self):
        """Test query with whitespace before prefix is not recognized."""
        parser = QueryParser()
        query = " /btw message"

        result = parser.parse(query)

        assert result.mode == QueryMode.DEFAULT
        assert result.content == " /btw message"

    def test_parse_btw_prefix_with_extra_spaces(self):
        """Test /btw prefix with multiple spaces after."""
        parser = QueryParser()
        query = "/btw   multiple spaces before message"

        result = parser.parse(query)

        assert result.mode == QueryMode.DIRECT
        assert result.content == "multiple spaces before message"

    def test_parse_base_prefix_with_extra_spaces(self):
        """Test /base prefix with multiple spaces after."""
        parser = QueryParser()
        query = "/base   multiple spaces before message"

        result = parser.parse(query)

        assert result.mode == QueryMode.BASE
        assert result.content == "multiple spaces before message"


class TestQueryRouter:
    """Tests for QueryRouter.route() method."""

    def test_route_returns_parsed_query(self):
        """Test that route() returns ParsedQuery from parser."""
        router = QueryRouter()
        query = "/btw test message"

        result = router.route(query)

        assert isinstance(result, ParsedQuery)
        assert result.mode == QueryMode.DIRECT
        assert result.content == "test message"

    def test_route_btw_prefix(self):
        """Test route() with /btw prefix."""
        router = QueryRouter()

        result = router.route("/btw direct message")

        assert result.mode == QueryMode.DIRECT
        assert result.content == "direct message"

    def test_route_base_prefix(self):
        """Test route() with /base prefix."""
        router = QueryRouter()

        result = router.route("/base base message")

        assert result.mode == QueryMode.BASE
        assert result.content == "base message"

    def test_route_no_prefix(self):
        """Test route() without prefix."""
        router = QueryRouter()

        result = router.route("regular query")

        assert result.mode == QueryMode.DEFAULT
        assert result.content == "regular query"


class TestQueryMode:
    """Tests for QueryMode enum values."""

    def test_query_mode_direct_value(self):
        """Test DIRECT mode has correct value."""
        assert QueryMode.DIRECT.value == "direct"

    def test_query_mode_base_value(self):
        """Test BASE mode has correct value."""
        assert QueryMode.BASE.value == "base"

    def test_query_mode_default_value(self):
        """Test DEFAULT mode has correct value."""
        assert QueryMode.DEFAULT.value == "default"


class TestParsedQuery:
    """Tests for ParsedQuery dataclass."""

    def test_parsed_query_attributes(self):
        """Test ParsedQuery stores mode and content correctly."""
        query = ParsedQuery(mode=QueryMode.DIRECT, content="test content")

        assert query.mode == QueryMode.DIRECT
        assert query.content == "test content"
