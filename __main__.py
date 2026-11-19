"""Entry point for ``python -m skillprint`` from the parent directory.

When run from /tmp/ghpush, the project directory is discovered as a namespace
package with no ``__init__.py``. Point its ``__path__`` at the real src package
before importing the CLI, so relative imports inside the package resolve.
"""

import os
import sys

_SRC_PKG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "skillprint")
_pkg = sys.modules.get("skillprint")
if _pkg is not None:
    _pkg.__path__ = [_SRC_PKG]
    _pkg.__version__ = "0.1.0"
if _SRC_PKG not in sys.path:
    sys.path.insert(0, _SRC_PKG)

from skillprint.cli import main

if __name__ == "__main__":
    sys.exit(main())
