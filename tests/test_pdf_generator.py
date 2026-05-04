"""
Unit tests for reports/pdf_generator.py - simplified
"""
import pytest
import pandas as pd
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from reports.pdf_generator import (
    get_leadership_team,
)


class TestGetLeadershipTeam:
    """Test get_leadership_team() from pdf_generator."""

    def test_returns_list(self):
        """Test returns a list."""
        result = get_leadership_team()
        assert isinstance(result, list)

    def test_list_not_empty(self):
        """Test list is not empty."""
        result = get_leadership_team()
        assert len(result) > 0

    def test_has_required_keys(self):
        """Test list items have required keys."""
        result = get_leadership_team()
        required = {"name", "role", "experience", "education", "specialization"}
        for key in required:
            assert key in result[0], f"Missing key: {key}"

    def test_has_bio(self):
        """Test has bio key (not achievements/quote in pdf_generator)."""
        result = get_leadership_team()
        assert "bio" in result[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
