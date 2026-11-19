"""Entry point for ``python -m skillprint`` from a source checkout."""

import sys

from skillprint.cli import main

if __name__ == "__main__":
    sys.exit(main())
