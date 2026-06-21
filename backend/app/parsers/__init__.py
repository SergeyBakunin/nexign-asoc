def detect_format(data: dict) -> str:
    """Return 'sarif' or 'cyclonedx' based on payload structure."""
    if data.get("bomFormat") == "CycloneDX":
        return "cyclonedx"
    schema = data.get("$schema", "")
    if "sarif" in schema.lower():
        return "sarif"
    if "runs" in data:
        return "sarif"
    if "components" in data or "dependencies" in data:
        return "cyclonedx"
    return "sarif"
