"""Conservative, regex-based capability detection over a skill directory.

The detector never executes skill code.  It only reads text files and looks
for a small set of well-known markers.  Every hit is reported with an
``evidence`` record containing the relative file path, the 1-based line
number and the matching source line, so a human can audit the result.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Pattern

# Capability name -> (human description, compiled conservative marker regex).
# Patterns are intentionally narrow to keep false positives low.
_MARKERS: Dict[str, tuple] = {
    "file-read": (
        "Reads files from disk",
        re.compile(r"(read_text\(|\bread_file\b|\bopen\([^)]*['\"]r[b]?['\"]|\bPath\(.*\)\.read)"),
    ),
    "file-write": (
        "Writes files to disk",
        re.compile(r"(write_text\(|\bwrite_file\b|\bopen\([^)]*['\"]w[b]?['\"]|\bshutil\.copy|\bunlink\(|\brmtree\()"),
    ),
    "network": (
        "Makes network requests",
        re.compile(r"(\brequests\.(get|post|put|delete)\b|\burllib\.request\b|\bhttp[s]?://|\bfetch\(|\bcurl\b|\bhttpx\b|\bsocket\.socket\b)"),
    ),
    "shell": (
        "Executes shell commands",
        re.compile(r"(\bsubprocess\.(run|Popen|call|check_output)\b|\bos\.system\(|\bshell\s*=\s*True\b|\bos\.popen\(|\bshlex\.)"),
    ),
    "code-exec": (
        "Dynamically executes code",
        re.compile(r"(?<![\w.])(exec|eval)\s*\(|\bcompile\s*\("),
    ),
    "image-gen": (
        "Generates or manipulates images",
        re.compile(r"(\bPIL\b|\bImage\.open\b|\bgenerate_image\b|\bimage_gen\b|\bimages\.generate\b|\bImageDraw\b)"),
    ),
}

DANGEROUS = ("shell", "network")

# A dangerous marker is only considered explicitly authorised when at least
# one of these tokens appears in the skill's ``allowed-tools`` declaration.
ALLOWED_TOKENS: Dict[str, frozenset] = {
    "shell": frozenset({"shell", "bash", "sh", "terminal", "execute", "exec", "subprocess"}),
    "network": frozenset({"network", "web", "http", "https", "fetch", "curl", "internet"}),
}

# Text file extensions we are willing to scan.  Binary / unknown files are
# skipped so detection stays deterministic and cheap.
_TEXT_SUFFIXES = {".py", ".js", ".ts", ".sh", ".md", ".json", ".yaml", ".yml", ".txt", ".rb", ".go", ".rs"}


def known_capabilities() -> List[str]:
    """Return the sorted list of well-known capability names."""
    return sorted(_MARKERS)


def capability_description(name: str) -> str:
    """Return the human description for a known capability."""
    return _MARKERS[name][0]


def _pattern(name: str) -> Pattern[str]:
    return _MARKERS[name][1]


def _iter_text_files(root: str):
    """Yield (absolute_path, relative_path) for scannable files, sorted."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for filename in sorted(filenames):
            suffix = os.path.splitext(filename)[1].lower()
            if suffix and suffix not in _TEXT_SUFFIXES:
                continue
            absolute = os.path.join(dirpath, filename)
            relative = os.path.relpath(absolute, root).replace(os.sep, "/")
            yield absolute, relative


def detect(root: str) -> Dict[str, List[dict]]:
    """Scan ``root`` and return ``{capability: [evidence, ...]}``.

    Only capabilities with at least one hit are included.  Evidence entries
    are dictionaries with ``file``, ``line`` and ``text`` keys, ordered by
    file then line.  Read errors on individual files are skipped silently.
    """
    results: Dict[str, List[dict]] = {name: [] for name in _MARKERS}

    for absolute, relative in _iter_text_files(root):
        try:
            with open(absolute, "r", encoding="utf-8", errors="replace") as handle:
                lines = handle.readlines()
        except (OSError, IOError):
            continue
        for line_number, line in enumerate(lines, start=1):
            snippet = line.strip()
            for name in _MARKERS:
                if _pattern(name).search(line):
                    results[name].append(
                        {"file": relative, "line": line_number, "text": snippet}
                    )

    # Deterministic ordering: by file, then line, then snippet text.
    for name in results:
        results[name].sort(key=lambda e: (e["file"], e["line"], e["text"]))
    return {name: evidence for name, evidence in results.items() if evidence}
