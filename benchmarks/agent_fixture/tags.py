def normalize_tags(tags):
    """Return unique, nonempty trimmed tags, preserving first appearance."""
    seen = set()
    result = []
    for tag in tags:
        trimmed = tag.strip()
        if not trimmed or trimmed in seen:
            continue
        seen.add(trimmed)
        result.append(trimmed)
    return result
