#!/usr/bin/env python3
"""Verify *specific* source claims against live official pages before PR build.

Fail closed for fetch/redirect/content mismatches. This proves page availability
and presence of predeclared terms, NOT vendor truth or API compatibility.
Only stdlib, strict HTTPS host allowlist; no remote code execution.
"""
import argparse
import html
from html.parser import HTMLParser
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/architecture/SOURCE-FIRST-DECISION.json"
CONTRACT = ROOT / "docs/architecture/GOVERNANCE-CONTRACT.json"
MAX_PAGE_BYTES = 2_000_000
MAX_ASSERTIONS_PER_SOURCE = 12
PATTERN = re.compile(r"^[\w][\w .\-/:()]{2,119}$", re.UNICODE)


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def accepted_host(url, hosts):
    try:
        parsed = urlparse(url)
        return (parsed.scheme == "https" and parsed.hostname in hosts and
                parsed.port in (None, 443) and not parsed.username and
                not parsed.password and not parsed.fragment)
    except ValueError:
        return False


class StrictRedirects(HTTPRedirectHandler):
    def __init__(self, hosts):
        super().__init__()
        self.hosts = hosts

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if not accepted_host(newurl, self.hosts):
            raise ValueError("GOV_SOURCE_UNTRUSTED_REDIRECT: " + newurl)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def fetch_visible_text(url, hosts, *, timeout=15):
    if not accepted_host(url, hosts):
        raise ValueError("GOV_SOURCE_HOST_INVALID: " + url)
    opener = build_opener(HTTPSHandler(), StrictRedirects(hosts))
    request = Request(url, headers={"User-Agent": "PHANTOM-source-first-audit/1.0",
                                    "Accept": "text/html, text/plain"})
    with opener.open(request, timeout=timeout) as response:
        if not accepted_host(response.url, hosts):
            raise ValueError("GOV_SOURCE_REDIRECT_OUTSIDE_ALLOWLIST")
        status = getattr(response, "status", 200)
        if status != 200:
            raise ValueError("GOV_SOURCE_HTTP_STATUS: " + str(status))
        mime = response.headers.get_content_type()
        if mime not in ("text/html", "text/plain"):
            raise ValueError("GOV_SOURCE_CONTENT_TYPE: " + mime)
        payload = response.read(MAX_PAGE_BYTES + 1)
        if len(payload) > MAX_PAGE_BYTES:
            raise ValueError("GOV_SOURCE_PAGE_TOO_LARGE")
        codec = response.headers.get_content_charset() or "utf-8"
    raw = payload.decode(codec, errors="replace")
    if mime == "text/html":
        parser = VisibleText()
        parser.feed(raw)
        raw = " ".join(parser.parts)
    return " ".join(html.unescape(raw).casefold().split())


def check_sources(decision, contract, fetcher=fetch_visible_text):
    config = contract.get("source_first", {})
    hosts = set(config.get("official_hosts", []))
    sources = decision.get("official_sources", [])
    issues = []
    results = []
    if not sources or not isinstance(sources, list):
        return [{"code": "GOV_SOURCE_LIST_MISSING",
                 "reason": "No official documentation sources."}], []
    for i, source in enumerate(sources):
        url = source.get("url") if isinstance(source, dict) else None
        terms = source.get("expected_terms") if isinstance(source, dict) else None
        if (not isinstance(url, str) or not accepted_host(url, hosts) or
            not isinstance(terms, list) or len(terms) < 2 or
            len(terms) > MAX_ASSERTIONS_PER_SOURCE or
            any(not isinstance(t, str) or not PATTERN.fullmatch(t)
                for t in terms)):
            issues.append({"code": "GOV_SOURCE_ASSERTION_INVALID", "source": i,
                           "reason": "Each official HTTPS source needs 2-12 valid predeclared terms."})
            continue
        try:
            page = fetcher(url, hosts)
            missing = [term for term in terms
                       if " ".join(term.casefold().split()) not in page]
            if missing:
                issues.append({"code": "GOV_SOURCE_CLAIM_NOT_FOUND", "source": i,
                               "reason": "Declared terms are absent: " + ", ".join(missing)})
            else:
                results.append({"source": i, "url": url,
                                "matched_terms": len(terms),
                                "status": "TEXT_MATCH_ONLY"})
        except (OSError, UnicodeError, ValueError, HTTPError, URLError,
                LookupError) as exc:
            issues.append({"code": "GOV_SOURCE_FETCH_FAILED", "source": i,
                           "reason": type(exc).__name__ + ": " + str(exc)[:250]})
    return issues, results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out")
    opts = parser.parse_args()
    try:
        decision = json.loads(RECORD.read_text(encoding="utf-8"))
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        issues, results = check_sources(decision, contract)
    except (OSError, ValueError, UnicodeError) as exc:
        issues, results = [{"code": "GOV_SOURCE_AUDIT_INPUT_INVALID",
                            "reason": str(exc)}], []
    report = {
        "status": "BLOCKED" if issues else "TEXT_VERIFIED",
        "authority": "LIVE_OFFICIAL_PAGE_TEXT_ONLY_NOT_API_OR_ACCEPTANCE_PROOF",
        "sources_checked": len(results) + len(issues),
        "matched": results,
        "denials": issues,
        "action": "Recheck official page, its pinned-version relevance and"
                  " required terms; do not bypass the gate on network failure.",
        "resume": "source_first",
    }
    serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if opts.json_out:
        dest = Path(opts.json_out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(serialized, encoding="utf-8")
    print(serialized)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
