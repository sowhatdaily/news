"""
Entry point for Streamlit Cloud.
Adds utils/ to sys.path and re-executes utils/app.py in-process
so that all Streamlit widget calls are captured.
"""
import sys
import os
from pathlib import Path

_utils = str(Path(__file__).resolve().parent / "utils")

# 1. Put utils/ on the import path so ai_service, core, db resolve
if _utils not in sys.path:
    sys.path.insert(0, _utils)

# 2. CWD → utils/ so relative file paths (DB) work
os.chdir(_utils)

# 3. Read and exec the real app in *this* module's namespace
#    (Streamlit only renders widgets from the main script's execution)
_app_path = os.path.join(_utils, "app.py")
with open(_app_path) as _f:
    exec(compile(_f.read(), _app_path, "exec"))
