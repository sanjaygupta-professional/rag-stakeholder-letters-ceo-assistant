#!/usr/bin/env python3
"""Script 08 — Launch the Streamlit demo."""

import os
import subprocess
import sys

def main():
    app_path = os.path.join(os.path.dirname(__file__), "..", "src", "demo", "app.py")
    print("Launching Streamlit demo...")
    print("  URL: http://localhost:8501")
    print("  Press Ctrl+C to stop")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path,
                    "--server.port", "8501"])

if __name__ == "__main__":
    main()
