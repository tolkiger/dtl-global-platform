"""Tests for the deploy_client_website.py script.

Tests input validation, duplicate detection, config manipulation,
and the overall deployment flow with mocked external services.

Part of Phase 4 of the DTL-Global Platform.
"""

# === Standard Library Imports ===
import json  # JSON parsing for config manipulation tests
import os  # Environment variable manipulation
import sys  # System path manipulation for imports
import unittest  # Test framework
from unittest.mock import MagicMock, patch  # Mocking external calls

# Add the scripts directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

# === Local Imports ===
from deploy_client_website import (
    slugify,
    normalize_domain,
    normalize_github_repo_slug,
    check_duplicate,
    add_site_to_config,
)


class TestNormalizeGithubRepoSlug(unittest.TestCase):
    """Tests for normalize_github_repo_slug."""

    def test_owner_repo_form(self):
        """owner/repo should compare equal to repo-only form."""
        self.assertEqual(
            normalize_github_repo_slug("TolKiger/dtl-client-foo"), "dtl-client-foo",
        )

    def test_case_insensitive(self):
        """Repo slugs should fold case for duplicate detection."""
        self.assertEqual(normalize_github_repo_slug("BusinessCenter"), "businesscenter")


class TestNormalizeDomain(unittest.TestCase):
    """Tests for normalize_domain (Route 53-safe comparison)."""

    def test_lowercases_and_strips_trailing_dot(self):
        """FQDN-style input should match Route 53 API name shape."""
        self.assertEqual(
            normalize_domain("BusinessCenterSolutions.NET."),
            "businesscentersolutions.net",
        )

    def test_strips_whitespace(self):
        """Leading or trailing spaces should not break zone reuse."""
        self.assertEqual(
            normalize_domain("  example.com "),
            "example.com",
        )


class TestSlugify(unittest.TestCase):
    """Tests for the slugify function."""

    def test_simple_name(self):
        """Test slugifying a simple business name."""
        result = slugify("Smith Roofing")  # Simple two-word name
        self.assertEqual(result, "smith-roofing")

    def test_name_with_special_chars(self):
        """Test slugifying a name with special characters."""
        result = slugify("Smith & Sons Roofing Co.")  # Ampersand and period
        self.assertEqual(result, "smith-sons-roofing-co")

    def test_name_with_extra_spaces(self):
        """Test slugifying a name with extra whitespace."""
        result = slugify("  Smith   Roofing  ")  # Extra spaces
        self.assertEqual(result, "smith-roofing")

    def test_already_slugified(self):
        """Test that an already-slugified name passes through unchanged."""
        result = slugify("smith-roofing")  # Already a slug
        self.assertEqual(result, "smith-roofing")


class TestCheckDuplicate(unittest.TestCase):
    """Tests for the check_duplicate function."""

    def setUp(self):
        """Set up a sample config for duplicate testing."""
        self.config = {
            "websites": [
                {
                    "siteName": "smith-roofing-website",
                    "githubRepo": "dtl-client-smith-roofing",
                    "domainName": "smithroofing.com",
                    "hostedZoneId": "Z0123456789",
                    "hostedZoneName": "smithroofing.com",
                    "menuPdfEnabled": False
                }
            ]
        }

    def test_duplicate_by_site_name(self):
        """Test detection of duplicate by site name."""
        result = check_duplicate(self.config, "smith-roofing-website", "other.com", "dtl-client-other")
        self.assertTrue(result)  # Should detect duplicate

    def test_duplicate_by_domain(self):
        """Test detection of duplicate by domain name."""
        result = check_duplicate(self.config, "other-website", "smithroofing.com", "dtl-client-other")
        self.assertTrue(result)  # Should detect duplicate

    def test_duplicate_by_domain_case_insensitive(self):
        """Domain in config vs CLI may differ only by case (prevents extra CloudFront rows)."""
        result = check_duplicate(self.config, "new-website", "SmithRoofing.COM", "dtl-client-smith-roofing")
        self.assertTrue(result)

    def test_duplicate_by_github_repo(self):
        """Same GitHub repo must not get a second pipeline-factory entry."""
        result = check_duplicate(self.config, "different-name-website", "different.com", "dtl-client-smith-roofing")
        self.assertTrue(result)

    def test_no_duplicate(self):
        """Test that non-duplicates pass through."""
        result = check_duplicate(self.config, "jones-plumbing-website", "jonesplumbing.com", "dtl-client-jones")
        self.assertFalse(result)  # Should not detect duplicate

    def test_empty_config(self):
        """Test with empty websites array."""
        empty_config = {"websites": []}
        result = check_duplicate(empty_config, "any-website", "any.com", "any-repo")
        self.assertFalse(result)  # No duplicates possible


class TestAddSiteToConfig(unittest.TestCase):
    """Tests for the add_site_to_config function."""

    def test_add_new_site(self):
        """Test adding a new site to the config."""
        config = {"websites": []}  # Start with empty config

        # Add a new site
        result = add_site_to_config(
            config=config,
            client_name="Smith Roofing",
            github_repo="dtl-client-smith-roofing",
            domain="smithroofing.com",
            hosted_zone_id="Z0123456789",
            hosted_zone_name="smithroofing.com"
        )

        # Verify the site was added
        self.assertEqual(len(result["websites"]), 1)  # One site added
        site = result["websites"][0]
        self.assertEqual(site["siteName"], "smith-roofing-website")
        self.assertEqual(site["githubRepo"], "dtl-client-smith-roofing")
        self.assertEqual(site["domainName"], "smithroofing.com")
        self.assertEqual(site["hostedZoneId"], "Z0123456789")
        self.assertEqual(site["hostedZoneName"], "smithroofing.com")
        self.assertFalse(site["menuPdfEnabled"])

    def test_add_preserves_existing(self):
        """Test that adding a site preserves existing entries."""
        config = {
            "websites": [
                {"siteName": "existing-site", "domainName": "existing.com"}
            ]
        }

        result = add_site_to_config(
            config=config,
            client_name="New Client",
            github_repo="dtl-client-new",
            domain="newclient.com",
            hosted_zone_id="Z9999999999",
            hosted_zone_name="newclient.com"
        )

        # Verify both sites exist
        self.assertEqual(len(result["websites"]), 2)  # Two sites total
        self.assertEqual(result["websites"][0]["siteName"], "existing-site")  # Original preserved
        self.assertEqual(result["websites"][1]["siteName"], "new-client-website")  # New added


if __name__ == "__main__":
    unittest.main()