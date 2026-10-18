"""
DocuDrift Root Entry Point for Streamlit Cloud and Local Deployment.
Allows Streamlit Cloud to use either 'app.py' or 'ui/app.py'.
"""
import os
import sys
import runpy
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Execute the core UI dashboard
target_script = os.path.join(ROOT_DIR, "ui", "app.py")
runpy.run_path(target_script, run_name="__main__")
