#!/usr/bin/env python3
"""Render a read-only PHANTOM governance dashboard from CI evidence snapshots.

Does not create, update, or certify acceptance decisions. Standard library only.
"""
import argparse
import html
import json
import os
from pathlib import Path

CAP_NAMES = {
    "dashboard": "Dashboard",
    "evidence": "Evidence and provenance",
    "end_to_end": "Phase lifecycle",
    "enforcement": "Mandatory enforcement",
    "baseline_review": "Baseline review",
    "impact_rollback": "Impact and rollback",
}
STAGE_NAMES = (
    "discover", "baseline_review", "dependencies", "plan",
    "authorized_execute", "build_and_tests", "evidence", "acceptance",
    "publish", "checkpoint",
)
CSS = """
:root {color-scheme:dark;--bg:#101827;--card:#1b283c;--border:#394a63;
--text:#eef4fc;--muted:#acbad0;--blue:#69bafa;--green:#3fca9c;
--orange:#ffcc76;--red:#fa8b96}
* {box-sizing:border-box}
body {margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,sans-serif}
main {max-width:1150px;margin:auto;padding:32px 20px 60px}
h1 {font-size:32px;margin-bottom:0} h2 {font-size:22px;margin:28px 0 12px}
p,.muted {color:var(--muted)}
a{color:var(--blue)}
header,.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:22px}
header{padding:28px}
.tag{display:inline-block;padding:4px 12px;border-radius:999px;background:#583b35;color:#ffcb98;font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.card h3{margin:0 0 8px;font-size:18px}
.value{font-size:36px;font-weight:800;letter-spacing:-1px}
.bar{background:#35465c;height:16px;border-radius:12px;overflow:hidden;margin:15px 0}
.fill{height:100%;background:var(--green)}
.chart-row{display:grid;grid-template-columns:180px 1fr 58px;align-items:center;gap:12px;margin:13px 0}
.chart-row .bar{margin:0}
.bars{margin-top:18px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:10px;border-bottom:1px solid var(--border);vertical-align:top}
th{color:#cbd8ea}
code{word-break:break-word;color:#b9e5ff}
.notice{border-left:4px solid var(--orange);padding:12px 17px;background:#31313b;border-radius:7px}
.status{font-weight:700}
.status.check_ok{color:var(--green)}
.status.blocked,.status.not_implemented,.status.not_executed,.status.open{color:var(--orange)}
ul{padding-left:22px}
small{color:var(--muted)}
@media(max-width:600px){.chart-row{grid-template-columns:100px 1fr 36px} main{padding:14px}}
"""


def esc(value):
    return html.escape(str(value), quote=True)


def validate(inventory, probe):
    if inventory.get("gate") != "GOV-P0" or inventory.get("decision") != "OPEN":
        raise ValueError("GOV_DASHBOARD_INVENTORY_NOT_OPEN")
    if probe.get("phase") != "GOV-P0" or probe.get("overall_acceptance") != "OPEN":
        raise ValueError("GOV_DASHBOARD_PROBE_NOT_OPEN")
    if probe.get("sha") != inventory.get("commit_sha"):
        raise ValueError("GOV_DASHBOARD_SOURCE_REVISION_MISMATCH")
    if probe.get("contract_sha256") != inventory.get("contract_digest_sha256"):
        raise ValueError("GOV_DASHBOARD_CONTRACT_HASH_MISMATCH")
    caps = inventory.get("capabilities", [])
    if len(caps) != 6 or {c.get("id") for c in caps} != set(CAP_NAMES):
        raise ValueError("GOV_DASHBOARD_SIX_CAPABILITIES_REQUIRED")
    steps = probe.get("steps", [])
    if [s.get("step") for s in steps] != list(STAGE_NAMES):
        raise ValueError("GOV_DASHBOARD_TEN_STAGES_REQUIRED")
    if probe.get("all_steps_executed") is not False:
        raise ValueError("GOV_DASHBOARD_PROBE_MUST_NOT_CLAIM_EXECUTION")
    if any(c.get("contract_state") != "OPEN" or c.get("verified") is not False for c in caps):
        raise ValueError("GOV_DASHBOARD_FALSE_CAPABILITY_ACCEPTANCE")
    for s in steps:
        if not all(s.get(k) for k in ("code", "reason", "action", "resume")):
            raise ValueError("GOV_DASHBOARD_INCOMPLETE_REMEDY")
    return caps, steps


def model(inventory, probe, run_id="", repository="barsam54/PHANTOM"):
    caps, steps = validate(inventory, probe)
    categories = {
        "CHECK_OK": sum(s["state"] == "CHECK_OK" for s in steps),
        "BLOCKED": sum(s["state"] == "BLOCKED" for s in steps),
        "NOT_IMPLEMENTED": sum(s["state"] == "NOT_IMPLEMENTED" for s in steps),
        "NOT_EXECUTED": sum(s["state"] == "NOT_EXECUTED" for s in steps),
    }
    categories["OTHER"] = len(steps) - sum(categories.values())
    return {
        "schema_version": "phantom.governance.dashboard.v1",
        "source_sha": inventory["commit_sha"],
        "contract_sha256": inventory["contract_digest_sha256"],
        "gate": "GOV-P0",
        "acceptance": "OPEN",
        "accepted_capabilities": 0,
        "capabilities": caps,
        "stages": steps,
        "stage_categories": categories,
        "historical_evidence_files": inventory.get("historical_evidence_files_found", 0),
        "historical_evidence_verified": False,
        "projects_synced": False,
        "current_ci_run_final_result": "NOT_YET_VERIFIED",
        "run_url": f"https://github.com/{repository}/actions/runs/{run_id}" if str(run_id).isdigit() else "",
        "remaining": inventory.get("remaining", []),
    }


def dashboard_html(data):
    caps = data["capabilities"]
    steps = data["stages"]
    chart_colors = {"CHECK_OK": "#3fca9c", "BLOCKED": "#fa8b96",
                    "NOT_IMPLEMENTED": "#ffcc76", "NOT_EXECUTED": "#69bafa",
                    "OTHER": "#b3a9f0"}
    def card(title, value, explanation):
        return f'<article class="card"><h3>{esc(title)}</h3><div class="value">{esc(value)}</div><p>{esc(explanation)}</p></article>'

    cap_cards = "".join(
        '<article class="card"><h3>' + esc(f"{i}. {CAP_NAMES[c['id']]}") +
        '</h3><strong class="status open">OPEN / NOT VERIFIED</strong><p>Acceptance proof: ' +
        esc(c.get("next_proof", "Missing")) + '</p></article>'
        for i, c in enumerate(caps, 1))
    chart = "".join(
        '<div class="chart-row"><span>' + esc(k.replace("_", " ")) +
        '</span><div class="bar"><div class="fill" style="width:' +
        str(100 * n // len(steps)) + '%;background:' + chart_colors[k] +
        '"></div></div><strong>' + str(n) + '</strong></div>'
        for k, n in data["stage_categories"].items()
    )
    rows = "".join(
        '<tr><td>' + str(i) + '</td><td>' + esc(s["step"]) + '</td><td class="status ' +
        esc(s["state"].lower()) + '">' + esc(s["state"]) + '</td><td>' +
        esc(s["reason"]) + '</td><td>' + esc(s["action"]) +
        '</td></tr>' for i, s in enumerate(steps, 1)
    )
    blockers = "".join("<li>" + esc(x) + "</li>" for x in data["remaining"])
    link = ('<a href="' + esc(data["run_url"]) + '">Open source GitHub Actions run</a>'
            if data["run_url"] else "GitHub Actions run URL unavailable")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PHANTOM | Governance Dashboard</title><style>{CSS}</style></head>
<body><main>
<header><span class="tag">GOV-P0 OPEN</span><h1>PHANTOM Control Dashboard</h1>
<p>Read-only evidence projection, not an acceptance authority. {link}</p>
<small>Code revision: <code>{esc(data["source_sha"])}</code><br>
Contract SHA-256: <code>{esc(data["contract_sha256"])}</code></small></header>
<h2>Acceptance summary</h2>
<section class="grid">
{card("Accepted capabilities", "0 / 6", "0 / 6 accepted. No final capability PASS is supported by complete evidence.")}
{card("Ten-step workflow", "OPEN", "Readiness probe, not autonomous phase execution.")}
{card("Historical evidence", str(data["historical_evidence_files"]), "Files discovered, not independently validated.")}
{card("Projects sync", "NOT CONNECTED", "GitHub Projects is not a verified projection source.")}
</section>
<h2>Six complementary controls</h2><section class="grid">{cap_cards}</section>
<h2>Ten-step readiness chart</h2>
<p>CHECK_OK means a precondition was inspected. It does not mean a production step executed.</p>
<section class="card bars">{chart}</section>
<h2>Step-by-step blockers and remedies</h2>
<section class="card"><table><thead><tr><th>#</th><th>Step</th><th>State</th><th>Reason</th><th>Required action</th></tr></thead>
<tbody>{rows}</tbody></table></section>
<h2>Remaining blockers</h2><section class="card"><ul>{blockers}</ul></section>
<p class="notice">CI success is not a GOV-P0 PASS. This snapshot cannot establish current CI completion,
source-code quality, verified SML gate acceptance, or live GitHub Projects synchronization.</p>
<p><small>Generated from the exact SHA of the versioned contract and a ten-stage diagnostic. No manual PASS fields.</small></p>
</main></body></html>
"""


def dashboard_svg(data):
    counts = data["stage_categories"]
    colors = {"CHECK_OK": "#3fca9c", "BLOCKED": "#fa8b96",
              "NOT_IMPLEMENTED": "#ffcc76", "NOT_EXECUTED": "#69bafa",
              "OTHER": "#b3a9f0"}
    rows = []
    for i, (key, count) in enumerate(counts.items()):
        y = 197 + 43 * i
        rows.append(
            f'<text x="30" y="{y}" fill="#e9f0ff" font-size="15">{esc(key)}</text>'
            f'<rect x="200" y="{y-16}" width="370" height="18" rx="7" fill="#34465b"/>'
            f'<rect x="200" y="{y-16}" width="{37 * count}" height="18" rx="7" fill="{colors[key]}"/>'
            f'<text x="590" y="{y}" fill="#e9f0ff" font-size="16">{count}</text>'
        )
    return ('<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PHANTOM governance, 0 of 6 controls accepted; ten stage readiness categories" viewBox="0 0 670 450">'
            '<rect width="670" height="450" rx="20" fill="#101827"/>'
            '<text x="30" y="48" font-family="sans-serif" fill="#eef4fc" font-weight="bold" font-size="27">PHANTOM | GOV-P0</text>'
            '<text x="30" y="87" font-family="sans-serif" fill="#ffcc76" font-size="22">OPEN · 0 / 6 accepted</text>'
            '<rect x="30" y="105" width="600" height="19" rx="9" fill="#34465b"/>'
            '<text x="30" y="160" font-family="sans-serif" fill="#eef4fc" font-size="19">Ten-step readiness (NOT phase completion)</text>'
            '<g font-family="sans-serif">' + "".join(rows) + '</g>'
            '<text x="30" y="430" font-family="sans-serif" fill="#acbad0" font-size="12">Evidence-backed snapshot. No SML or full phase PASS inferred.</text></svg>')


def dashboard_summary(data):
    counts = data["stage_categories"]
    lines = [
        "## PHANTOM | Visual control dashboard",
        "",
        "**GOV-P0: OPEN** · **0 / 6 controls accepted**",
        "",
        "**Acceptance**  `░░░░░░` 0%",
        "",
        "| Stage-readiness classification | Count | Chart |",
        "|---|---:|---|",
    ]
    for key, n in counts.items():
        lines.append(f"| {key} | {n} | `{'█' * n}{'░' * (10-n)}` |")
    lines += [
        "", "### Six controls",
        "| Control | Acceptance |",
        "|---|---|",
    ]
    for c in data["capabilities"]:
        lines.append(f"| {CAP_NAMES[c['id']]} | OPEN · NOT VERIFIED |")
    lines += [
        "", f"Revision: `{data['source_sha']}`",
        f"Historical evidence files discovered: {data['historical_evidence_files']} (NOT verified by this report).",
        "The full HTML dashboard and SVG chart are available in the **governance-inventory** artifact.",
        "", "This visualization cannot grant PASS or update GitHub Projects.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--probe", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
        probe = json.loads(Path(args.probe).read_text(encoding="utf-8"))
        data = model(inventory, probe,
                     run_id=os.environ.get("GITHUB_RUN_ID", ""),
                     repository=os.environ.get("GITHUB_REPOSITORY", "barsam54/PHANTOM"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("GOV_DASHBOARD_RENDER_BLOCKED:", str(exc))
        return 2
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "dashboard.html").write_text(dashboard_html(data), encoding="utf-8")
    (output / "dashboard.svg").write_text(dashboard_svg(data), encoding="utf-8")
    (output / "dashboard.md").write_text(dashboard_summary(data), encoding="utf-8")
    (output / "dashboard.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("GOV_DASHBOARD_RENDERED: PASS (visualization only, GOV-P0 OPEN)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
