"""
Parse CycloneDX BOM JSON (v1.4/1.5) produced by CodeScoring/Johnny.
Returns:
  findings  - list[dict]  (vulnerabilities → Finding)
  components - list[dict] (components → Dependency)
"""
from __future__ import annotations

SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "informational": "info",
    "none": "info",
    "unknown": "info",
}


def _sev(s: str | None) -> str:
    return SEVERITY_MAP.get((s or "").lower(), "info")


def _component_vulns(comp_ref: str, vuln_list: list[dict]) -> list[dict]:
    result = []
    for v in vuln_list:
        for affect in v.get("affects", []):
            if affect.get("ref") == comp_ref:
                result.append({
                    "id": v.get("id"),
                    "severity": _sev(
                        (v.get("ratings") or [{}])[0].get("severity")
                    ),
                    "description": v.get("description"),
                })
    return result


def parse(data: dict) -> tuple[list[dict], list[dict]]:
    findings: list[dict] = []
    components: list[dict] = []

    vuln_list: list[dict] = data.get("vulnerabilities") or []
    comp_list: list[dict] = data.get("components") or []

    # Build bom-ref → component name map
    ref_map: dict[str, dict] = {}
    for comp in comp_list:
        ref = comp.get("bom-ref") or comp.get("purl") or ""
        ref_map[ref] = comp

    # Parse vulnerabilities as findings
    for v in vuln_list:
        vid = v.get("id") or "unknown"
        ratings = v.get("ratings") or [{}]
        severity = _sev(ratings[0].get("severity"))
        description = v.get("description")

        affected_refs = [a.get("ref") for a in (v.get("affects") or [])]
        for ref in affected_refs:
            comp = ref_map.get(ref, {})
            comp_name = comp.get("name") or ref
            comp_ver = comp.get("version") or ""
            cve = vid if vid.startswith("CVE-") else None
            findings.append({
                "rule_id": vid,
                "name": f"{vid} in {comp_name}@{comp_ver}",
                "description": description,
                "severity": severity,
                "cve": cve,
                "uri": comp.get("purl"),
                "region": None,
                "extra": {
                    "source": v.get("source"),
                    "advisories": v.get("advisories"),
                    "component": {"name": comp_name, "version": comp_ver, "purl": comp.get("purl")},
                },
            })

    # Parse components as dependencies
    for comp in comp_list:
        name = comp.get("name") or "unknown"
        version = comp.get("version")
        purl = comp.get("purl")
        ref = comp.get("bom-ref") or purl or ""

        licenses: list[str] = []
        for lic in comp.get("licenses") or []:
            lic_obj = lic.get("license") or lic.get("expression") or {}
            lic_id = (lic_obj.get("id") or lic_obj.get("name") or
                      (lic_obj if isinstance(lic_obj, str) else ""))
            if lic_id:
                licenses.append(lic_id)

        comp_vulns = _component_vulns(ref, vuln_list)

        components.append({
            "name": name,
            "version": version,
            "purl": purl,
            "licenses": licenses or None,
            "vulnerabilities": comp_vulns or None,
        })

    return findings, components
