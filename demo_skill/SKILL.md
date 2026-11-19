---
name: demo-skill
description: A demonstration skill that reads and writes files, runs shell commands, and fetches data over the network.
version: 1.0.0
allowed-tools:
  - read
  - write
  - shell
  - network
capabilities:
  - file-read
  - file-write
  - shell
  - network
---

# Demo Skill

This fixture is scanned by skillprint's tests. It intentionally demonstrates
several well-known capability markers:

- **file-read / file-write** via Python's `open()` in `scripts/helper.py`.
- **shell** via `subprocess.run(...)`.
- **network** via `requests.get(...)`.

Every capability used here is declared in `allowed-tools` and described above,
so `skillprint demo_skill --check` passes.
