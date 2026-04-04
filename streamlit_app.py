"""
Entry point for Streamlit Cloud.
Adds the utils/ directory to sys.path so that existing imports
(ai_service, core, db) resolve correctly, then runs the main app.
"""
import sys
import os
import runpy
from pathlib import Path

# Add utils/ to the Python path so imports work as before
_utils = str(Path(__file__).resolve().parent / "utils")
if _utils not in sys.path:
    sys.path.insert(0, _utils)

# Set CWD to utils/ so relative paths (DB, .env) resolve correctly
os.chdir(_utils)

# Run utils/app.py as __main__ so all top-level st.* calls execute
runpy.run_path(os.path.join(_utils, "app.py"), run_name="__main__")
