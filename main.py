"""
DocuDrift Entry Point. Launches Streamlit dashboard.
"""

import subprocess
import sys
import os

def main():
    print("🛰️ Starting DocuDrift / LivingWiki Sentinel...")
    script_path = os.path.join(os.path.dirname(__file__), "ui", "app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", script_path])

if __name__ == "__main__":
    main()
