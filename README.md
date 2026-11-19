# skillprint

**Pre-install capability label for AI agent skills.**

`skillprint` scans an AI-agent *skill* directory — a folder containing a
`SKILL.md` with YAML-ish frontmatter and a `scripts/` directory — and emits a
compact, deterministic **capability label**: a structured manifest describing
what the skill can do *before* it is installed or loaded.

It is a pure static analyzer. It **never executes skill code** and **never
makes network calls**. It uses only the Python standard library (3.9+), so it
can run in sandboxes, CI, and air-gapped machines.

## The problem

Installing an AI agent skill usually means trusting a README. By the time the
skill is loaded, it may read or write files, run shell commands, or call the
network — and you only find out afterward. `skillprint` gives you a
machine-readable label you can inspect and gate on *first*.

## Install

```console
pip install .
```

Or run it directly from a checkout — a tiny root-level shim makes the bare
command work without installing:

```console
python -m skillprint --help
```

(The real implementation lives in `src/skillprint`; the shim delegates to it.
`PYTHONPATH=src python -m skillprint ...` also works.)

## Usage

```console
skillprint [SKILL_DIR] [--format {text,json}] [--check]
```

* `SKILL_DIR` — path to the skill directory (default: `.`). Must contain
  `SKILL.md`.
* `--format` — `text` (default, human-readable table) or `json`
  (deterministic, sorted keys — safe to commit or diff).
* `--check` — safety gate (see below).

### Examples

Human-readable label for a skill:

```console
$ python -m skillprint demo_skill
Capability label: demo-skill
Version:          1.0.0
Description:      A demonstration skill that reads and writes files, runs shell commands, and fetches data over the network.
Allowed tools:    network, read, shell, write

CAPABILITIES
CAPABILITY  STATUS    DECLARED  EVIDENCE
code-exec   -         -         -
file-read   detected  yes       scripts/helper.py:5
file-write  detected  yes       scripts/helper.py:10
image-gen   -         -         -
network     detected  yes       scripts/helper.py:23 (+1)
shell       detected  yes       scripts/helper.py:17
```

Deterministic JSON:

```console
$ python -m skillprint demo_skill --format json
{
  "allowed_tools": [...],
  "capabilities": { ... },
  "name": "demo-skill",
  ...
}
```

Safety gate in CI:

```console
python -m skillprint path/to/skill --check --format json
```

## What is detected

The detector uses conservative regular expressions over the skill's text
files. Every hit carries `file:line` evidence. Known capabilities:

| Capability | Meaning | Example markers |
| --- | --- | --- |
| `file-read` | reads files | `open(..., "r")`, `read_text()` |
| `file-write` | writes files | `open(..., "w")`, `write_text()` |
| `network` | network access | `requests.get`, `urllib`, `http://` |
| `shell` | shell execution | `subprocess.run`, `os.system`, `shell=True` |
| `code-exec` | dynamic code | `exec(`, `eval(` |
| `image-gen` | image generation | `PIL`, `Image.open`, `images.generate` |

Detection is conservative by design: it may miss unusual idioms, but it aims
to avoid false accusations. Treat a clean label as "no known markers found",
not as a formal proof of safety.

## `--check` safety rules

`--check` exits **1** if either rule is violated:

1. **Declared but not documented** — the frontmatter's `capabilities:` list
   names a capability that is neither evidenced in the files nor described in
   the SKILL.md prose.
2. **Undeclared dangerous marker** — a `shell` or `network` marker is detected
   but `allowed-tools` does not include a matching token (`shell`/`bash`/
   `execute`/… or `network`/`web`/`http`/…).

This catches the two common honesty failures: a skill claiming powers it does
not have, and a skill quietly reaching the shell or network without saying so.

## Frontmatter format

```yaml
---
name: demo-skill
description: Reads and writes files, runs shell commands, fetches data.
version: 1.0.0
allowed-tools:
  - read
  - write
  - shell
  - network
capabilities: [file-read, file-write, shell, network]
---
```

Inline lists (`[a, b]`), block lists (`- item`), and quoted scalars are
supported. A minimal parser is included — **no PyYAML required**.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | OK |
| 1 | `--check` failed |
| 2 | usage / input error (bad path, missing or malformed `SKILL.md`) |

## Repo layout

```
src/skillprint/   package (parser, detector, label builder, CLI)
tests/            unittest suite
demo_skill/       fixture skill used by the tests
```

## License

MIT — see [LICENSE](LICENSE).
