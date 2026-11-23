"""Offline tests for strict, live official documentation validation."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "official_docs", ROOT / "scripts/verify_official_sources.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

HOSTS = ["learn.microsoft.com", "docs.github.com"]
URL = "https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints"


class OfficialSourceVerificationTests(unittest.TestCase):
    def record(self, **changes):
        record = {"url": URL,
                  "expected_terms": ["Checkpoints", "superstep"]}
        return record | changes

    def test_verified_page_text_not_confused_with_api_acceptance(self):
        issues, results = audit.check_sources(
            {"official_sources": [self.record()]},
            {"source_first": {"official_hosts": HOSTS}},
            fetcher=lambda *_: "checkpoints are created after each superstep")
        self.assertEqual([], issues)
        self.assertEqual("TEXT_MATCH_ONLY", results[0]["status"])

    def test_fails_if_claim_missing(self):
        issues, _ = audit.check_sources(
            {"official_sources": [self.record()]},
            {"source_first": {"official_hosts": HOSTS}},
            fetcher=lambda *_: "a page without the described behavior")
        self.assertEqual("GOV_SOURCE_CLAIM_NOT_FOUND", issues[0]["code"])

    def test_fetch_failure_blocks_even_for_valid_url(self):
        def failed(*_):
            raise OSError("unavailable")
        issues, _ = audit.check_sources(
            {"official_sources": [self.record()]},
            {"source_first": {"official_hosts": HOSTS}},
            fetcher=failed)
        self.assertEqual("GOV_SOURCE_FETCH_FAILED", issues[0]["code"])

    def test_untrusted_vendor_host_rejected_before_network(self):
        issues, _ = audit.check_sources(
            {"official_sources": [self.record(
                url="https://example.org/mirrored-checkpoints")]},
            {"source_first": {"official_hosts": HOSTS}},
            fetcher=lambda *_: self.fail("Network must not be called"))
        self.assertEqual("GOV_SOURCE_ASSERTION_INVALID", issues[0]["code"])

    def test_invalid_or_missing_assertions_fail_closed(self):
        for terms in ([], ["one"], ["x", "other"], ["valid", "bad\nheader"]):
            with self.subTest(terms=terms):
                issues, _ = audit.check_sources(
                    {"official_sources": [self.record(expected_terms=terms)]},
                    {"source_first": {"official_hosts": HOSTS}},
                    fetcher=lambda *_: self.fail("Invalid assertions must block fetch"))
                self.assertEqual("GOV_SOURCE_ASSERTION_INVALID", issues[0]["code"])

    def test_redirects_cannot_change_host_or_protocol(self):
        handler = audit.StrictRedirects(set(HOSTS))
        for url in ("http://learn.microsoft.com/case",
                    "https://example.org/case",
                    "https://learn.microsoft.com:444/case"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    handler.redirect_request(None, None, 301, "Moved", {}, url)

    def test_html_ignores_injected_script_or_style_terms(self):
        parser = audit.VisibleText()
        parser.feed("<h1>Checkpoints</h1><script>superstep</script><p>Not evidence</p>")
        self.assertIn("Checkpoints", " ".join(parser.parts))
        self.assertNotIn("superstep", " ".join(parser.parts))

    def test_official_https_validation_rejects_embedded_credentials(self):
        self.assertFalse(audit.accepted_host(
            "https://user:token@learn.microsoft.com/page", set(HOSTS)))


if __name__ == "__main__":
    unittest.main()
