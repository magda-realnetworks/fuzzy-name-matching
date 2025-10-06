"""
Automatically import all matcher modules so they register themselves
via the @register() decorator in base.py.
"""

from importlib import import_module
from pathlib import Path

# Dynamically import all Python files (except base.py and __init__.py)
_pkg_path = Path(__file__).parent
for file in _pkg_path.glob("*.py"):
    if file.name not in ("__init__.py", "base.py"):
        import_module(f"{__package__}.{file.stem}")
