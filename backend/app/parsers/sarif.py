"""
Parse SARIF 2.1.0 JSON produced by Trivy, Gitleaks, ZAP (sarif-json template), PT AI.
Returns a list of dicts matching the Finding model fields.
"""
from __future__ import annotations

SEVERITY_MAP = {
    "error": "high",
    "warning": "medium",
    "note": "low",
    "none": "info",
    # ZAP / Trivy numeric strings
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "informational": "info",
}

_ZAP_RISK = {"3": "high", "2": "medium", "1": "low", "0": "info"}


def _map_level(level: str | None) -> str:
    if not level:
        return "info"
    return SEVERITY_MAP.get(level.lower(), "info")


def _extract_rule_meta(rules: list[dict], rule_id: str | None) -> dict:
    if not rule_id or not rules:
        return {}
    for r in rules:
        if r.get("id") == rule_id:
            full_desc = r.get("fullDescription") or r.get("shortDescription") or {}
            props = r.get("properties") or {}
            severity = props.get("severity") or props.get("problem.severity")
            return {
                "name": (r.get("name") or rule_id),
                "description": full_desc.get("text") if isinstance(full_desc, dict) else None,
                "severity": _map_level(severity),
                "cve": next(
                    (t.get("id") for t in (r.get("relationships") or [])
                     if "cve" in (t.get("id") or "").lower()),
                    None,
                ),
            }
    return {}


def _result_severity(result: dict, rule_meta: dict, rules: list[dict]) -> str:
    # Try result-level properties first (ZAP uses riskcode in properties)
    props = result.get("properties") or {}
    if "riskcode" in props:
        return _ZAP_RISK.get(str(props["riskcode"]), "info")
    if "severity" in props:
        return _map_level(props["severity"])
    level = result.get("level")
    if level:
        return _map_level(level)
    return rule_meta.get("severity", "info")


def parse(data: dict) -> list[dict]:
    findings: list[dict] = []

    for run in data.get("runs", []):
        tool = run.get("tool", {})
        driver = tool.get("driver", {})
        rules: list[dict] = driver.get("rules", [])

        for result in run.get("results", []):
            rule_id = result.get("ruleId")
            rule_meta = _extract_rule_meta(rules, rule_id)

            message_obj = result.get("message") or {}
            name = message_obj.get("text") or rule_meta.get("name") or rule_id or "Unknown finding"
            # Trivy кладёт в message многострочный текст — берём описание (оно конкретнее)
            if "\n" in name:
                name = (rule_meta.get("description")
                        or rule_meta.get("name")
                        or rule_id
                        or name.split("\n")[0].strip())
            name = (name or "Unknown finding").strip()

            severity = _result_severity(result, rule_meta, rules)

            # Location
            uri = region = None
            locations = result.get("locations") or []
            if locations:
                loc = locations[0]
                phys = loc.get("physicalLocation") or {}
                art = phys.get("artifactLocation") or {}
                uri = art.get("uri")
                reg = phys.get("region") or {}
                if reg:
                    region = {
                        "startLine": reg.get("startLine"),
                        "endLine": reg.get("endLine"),
                        "snippet": (reg.get("snippet") or {}).get("text"),
                    }

            # CVE from related locations or rule
            cve = rule_meta.get("cve")
            for rel in result.get("relatedLocations") or []:
                msg = (rel.get("message") or {}).get("text") or ""
                if "CVE-" in msg:
                    import re
                    m = re.search(r"CVE-\d{4}-\d+", msg)
                    if m:
                        cve = m.group()
                        break

            findings.append({
                "rule_id": rule_id,
                "name": name[:512],
                "description": rule_meta.get("description"),
                "severity": severity,
                "cve": cve,
                "uri": uri,
                "region": region,
                "extra": {
                    "tool": driver.get("name"),
                    "properties": result.get("properties"),
                },
            })

    return findings
