"""
Convenience wrapper that boots the Streamlit dashboard.

Equivalent to running:
    streamlit run src/dashboard/app.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cmd = [sys.executable, "-m", "streamlit", "run", str(ROOT / "src" / "dashboard" / "app.py")]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
