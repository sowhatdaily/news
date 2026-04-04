"""Redirect — actual app lives in utils/app.py."""
import sys, os
from pathlib import Path

_utils = str(Path(__file__).resolve().parent / "utils")
if _utils not in sys.path:
    sys.path.insert(0, _utils)
os.chdir(_utils)

with open(os.path.join(_utils, "app.py")) as _f:
    exec(compile(_f.read(), "app.py", "exec"))
