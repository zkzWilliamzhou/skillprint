"""Checkout shim for ``python -m skillprint`` without installing.

The real package lives in ``src/skillprint``. When running from a source
checkout, Python finds this root-level package first; redirecting ``__path__``
to the src package makes every submodule resolve to the real implementation.
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
__path__ = [os.path.join(_ROOT, "src", "skillprint")]
__version__ = "0.1.0"
