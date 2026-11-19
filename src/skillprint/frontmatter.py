"""Minimal, zero-dependency parser for the YAML-ish frontmatter of SKILL.md.

Frontmatter is the block delimited by ``---`` lines at the very top of the
file.  Only the small subset needed by skillprint is supported:

* scalar ``key: value`` pairs
* inline lists: ``allowed-tools: [read, write]``
* block lists::

      allowed-tools:
        - read
        - write

Quotes (single or double) around scalar values are stripped.  Anything more
exotic is intentionally *not* supported; the parser is conservative and
deterministic rather than clever.
"""

from __future__ import annotations

from typing import Dict, List

DELIMITER = "---"


class FrontmatterError(ValueError):
    """Raised when a SKILL.md frontmatter block cannot be parsed."""


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _parse_inline_list(value: str) -> List[str]:
    inner = value.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    return [_strip_quotes(item) for item in inner.split(",") if item.strip()]


def parse_frontmatter(text: str) -> Dict[str, object]:
    """Parse frontmatter from ``text`` and return a plain dict.

    If the document has no frontmatter block an empty dict is returned.
    ``FrontmatterError`` is raised for a malformed (unclosed) block.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != DELIMITER:
        return {}

    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == DELIMITER:
            end = index
            break
    if end is None:
        raise FrontmatterError("unclosed frontmatter block (missing closing '---')")

    data: Dict[str, object] = {}
    current_list_key = None
    for raw in lines[1:end]:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("-") and current_list_key is not None:
            item = _strip_quotes(stripped[1:])
            if item:
                existing = data.get(current_list_key)
                if not isinstance(existing, list):
                    existing = []
                existing.append(item)  # type: ignore[union-attr]
                data[current_list_key] = existing
            continue

        current_list_key = None
        if ":" not in line:
            raise FrontmatterError("invalid frontmatter line (expected 'key: value'): %r" % raw)
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise FrontmatterError("empty frontmatter key")
        value = value.strip()
        if not value:
            data[key] = []
            current_list_key = key
        elif value.startswith("["):
            data[key] = _parse_inline_list(value)
        else:
            data[key] = _strip_quotes(value)

    return data
