"""
Tests for network_security.utils.ml_utils.feature_extraction — specifically
the parts that don't require live network access (WHOIS, DNS, SSL, HTTP
fetch), so these run fast and deterministically in CI.

Covers the URL_of_Anchor / Links_in_tags computation added this session
(previously hardcoded to a neutral 0 for every live prediction, discarding
~27% of the model's total feature importance) and the URL validation guard
that prevents non-URLs (page fragments, localhost) from being scored.

Run with: pytest tests/test_feature_extraction.py -v
"""

from network_security.utils.ml_utils.feature_extraction import (
    _having_at_symbol,
    _having_ip_address,
    _https_token,
    _is_external_or_suspicious_link,
    _links_in_tags,
    _shortening_service,
    _url_of_anchor,
)


class TestUrlOfAnchor:
    """The model's 2nd most important feature (22.8% of total importance).
    Previously hardcoded to 0 for every live prediction — see Finding #3 in
    the technical bug report.
    """

    def test_mostly_same_domain_links_scores_legitimate(self) -> None:
        html = """
        <a href="/login">Login</a>
        <a href="/about">About</a>
        <a href="/contact">Contact</a>
        """
        assert _url_of_anchor(html, "example.com") == 1

    def test_mostly_broken_or_external_links_scores_phishing(self) -> None:
        html = """
        <a href="#">Login</a>
        <a href="javascript:void(0)">Secure Login</a>
        <a href="https://totally-different-domain.com/x">Home</a>
        <a href="#">Verify Account</a>
        """
        assert _url_of_anchor(html, "fake-paypal-login.tk") == -1

    def test_no_anchor_tags_scores_neutral(self) -> None:
        assert _url_of_anchor("<div>no links here</div>", "example.com") == 0

    def test_empty_html_scores_neutral(self) -> None:
        assert _url_of_anchor("", "example.com") == 0


class TestIsExternalOrSuspiciousLink:
    def test_empty_href_is_suspicious(self) -> None:
        assert _is_external_or_suspicious_link("", "example.com") is True

    def test_bare_hash_is_suspicious(self) -> None:
        assert _is_external_or_suspicious_link("#", "example.com") is True

    def test_javascript_void_is_suspicious(self) -> None:
        assert _is_external_or_suspicious_link("javascript:void(0)", "example.com") is True

    def test_relative_link_is_not_suspicious(self) -> None:
        assert _is_external_or_suspicious_link("/login", "example.com") is False

    def test_same_domain_absolute_link_is_not_suspicious(self) -> None:
        assert _is_external_or_suspicious_link("https://example.com/login", "example.com") is False

    def test_different_domain_is_suspicious(self) -> None:
        assert _is_external_or_suspicious_link("https://other-site.com/login", "example.com") is True

    def test_mailto_is_not_suspicious(self) -> None:
        assert _is_external_or_suspicious_link("mailto:contact@example.com", "example.com") is False


class TestLinksInTags:
    def test_no_tag_links_scores_neutral(self) -> None:
        assert _links_in_tags("<div>nothing</div>", "example.com") == 0

    def test_same_domain_script_and_meta_scores_legitimate(self) -> None:
        html = """
        <script src="/static/app.js"></script>
        <link href="/static/style.css">
        <meta property="og:url" content="https://example.com/page">
        """
        assert _links_in_tags(html, "example.com") == 1


class TestOtherFeatureFunctions:
    """Spot-check a few of the simpler, already-existing feature functions
    to guard against accidental regressions during future refactors.
    """

    def test_having_ip_address_detects_raw_ip_hostname(self) -> None:
        assert _having_ip_address("http://192.168.1.1/login", "192.168.1.1") == -1

    def test_having_ip_address_detects_ip_hidden_in_userinfo(self) -> None:
        # Classic phishing trick: IP hidden before "@" as fake userinfo,
        # which urlparse strips out of hostname entirely.
        assert _having_ip_address("http://192.168.1.1@fake-bank.com", "fake-bank.com") == -1

    def test_having_ip_address_normal_domain_is_fine(self) -> None:
        assert _having_ip_address("https://example.com", "example.com") == 1

    def test_having_at_symbol(self) -> None:
        assert _having_at_symbol("http://user@example.com") == -1
        assert _having_at_symbol("http://example.com") == 1

    def test_shortening_service_detects_known_shorteners(self) -> None:
        assert _shortening_service("http://bit.ly/abc123") == -1
        assert _shortening_service("http://example.com/abc123") == 1

    def test_https_token_catches_https_stuffed_into_hostname(self) -> None:
        # Not dead code: this is the classic trick of stuffing "https" into
        # the domain itself to look trustworthy at a glance.
        assert _https_token("https-paypal-secure.com") == -1
        assert _https_token("paypal.com") == 1