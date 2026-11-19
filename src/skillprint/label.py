"""Build the capability label, run the safety check, and render output."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from . import capabilities as caps
from .frontmatter import FrontmatterError, parse_frontmatter

SKILL_FILENAME = "SKILL.md"


class LabelError(Exception):
    """Input error (bad path, missing SKILL.md, malformed frontmatter)."""


def _as_list(value: object) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def load_skill(skill_dir: str) -> Dict[str, object]:
    """Read a skill directory and return a structured capability label."""
    if not os.path.isdir(skill_dir):
        raise LabelError("not a directory: %s" % skill_dir)
    skill_path = os.path.join(skill_dir, SKILL_FILENAME)
    if not os.path.isfile(skill_path):
        raise LabelError("missing %s in %s" % (SKILL_FILENAME, skill_dir))
    try:
        with open(skill_path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, IOError) as exc:
        raise LabelError("cannot read %s: %s" % (skill_path, exc))

    try:
        front = parse_frontmatter(text)
    except FrontmatterError as exc:
        raise LabelError("frontmatter error in %s: %s" % (skill_path, exc))

    detected = caps.detect(skill_dir)
    allowed_tools = _as_list(front.get("allowed-tools", front.get("allowed_tools", [])))
    declared = _as_list(front.get("capabilities", []))

    # Split the document into frontmatter body and prose for "documented" checks.
    prose = text
    if text.startswith("---"):
        parts = text.split("\n---", 1)
        if len(parts) == 2:
            prose = parts[1]
    prose_lower = prose.lower()

    label_capabilities: Dict[str, object] = {}
    for name in caps.known_capabilities():
        evidence = detected.get(name, [])
        documented = bool(evidence) or name.lower() in prose_lower
        label_capabilities[name] = {
            "detected": bool(evidence),
            "declared": name in declared,
            "documented": documented,
            "description": caps.capability_description(name),
            "evidence": evidence,
        }

    label = {
        "schema_version": 1,
        "name": str(front.get("name", os.path.basename(os.path.abspath(skill_dir)))),
        "version": str(front.get("version", "0.0.0")),
        "description": str(front.get("description", "")),
        "allowed_tools": sorted(set(allowed_tools)),
        "declared_capabilities": sorted(set(declared)),
        "capabilities": label_capabilities,
    }
    return label


def check(label: Dict[str, object]) -> List[str]:
    """Return a list of check failures (empty means the check passed)."""
    failures: List[str] = []
    capabilities = label["capabilities"]
    assert isinstance(capabilities, dict)
    allowed_lower = {str(tool).lower() for tool in label["allowed_tools"]}

    for name in sorted(capabilities):
        info = capabilities[name]
        assert isinstance(info, dict)

        # Rule 1: a capability declared in frontmatter must be documented
        # (either by marker evidence or by prose in SKILL.md).
        if info["declared"] and not info["documented"]:
            failures.append(
                "capability '%s' is declared but not documented" % name
            )

        # Rule 2: a dangerous marker requires an explicit allowed-tools token.
        if name in caps.DANGEROUS and info["detected"]:
            if not allowed_lower.intersection(caps.ALLOWED_TOKENS[name]):
                failures.append(
                    "dangerous capability '%s' detected without an explicit allowed-tools declaration"
                    % name
                )

    return failures


def _text_table(label: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("Capability label: %s" % label["name"])
    lines.append("Version:          %s" % label["version"])
    lines.append("Description:      %s" % (label["description"] or "-"))
    lines.append("Allowed tools:    %s" % (", ".join(label["allowed_tools"]) or "-"))
    lines.append("")
    lines.append("CAPABILITIES")
    capabilities = label["capabilities"]
    assert isinstance(capabilities, dict)

    names = sorted(capabilities)
    header = ("CAPABILITY", "STATUS", "DECLARED", "EVIDENCE")
    rows = []
    for name in names:
        info = capabilities[name]
        assert isinstance(info, dict)
        evidence_list = info["evidence"]
        if evidence_list:
            first = evidence_list[0]
            evidence_text = "%s:%s" % (first["file"], first["line"])
            if len(evidence_list) > 1:
                evidence_text += " (+%d)" % (len(evidence_list) - 1)
        else:
            evidence_text = "-"
        rows.append(
            (
                name,
                "detected" if info["detected"] else "-",
                "yes" if info["declared"] else "-",
                evidence_text,
            )
        )

    all_rows = [header] + rows
    widths = [max(len(row[i]) for row in all_rows) for i in range(len(header))]
    fmt = "  ".join("{:<%d}" % width for width in widths)

    lines.append(fmt.format(*header))
    lines.append("  ".join("-" * width for width in widths))
    for row in rows:
        lines.append(fmt.format(*row))
    return "\n".join(lines)


def render(label: Dict[str, object], output_format: str) -> str:
    """Render the label as deterministic JSON or a human-readable table."""
    if output_format == "json":
        return json.dumps(label, indent=2, sort_keys=True, ensure_ascii=False)
    if output_format == "text":
        return _text_table(label)
    raise ValueError("unknown output format: %s" % output_format)
