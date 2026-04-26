"""Build HP Assistant into a distributable Windows folder via PyInstaller."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    spec = Path(__file__).parent / "hp.spec"
    if not spec.exists():
        print(f"ERROR: spec file not found at {spec}")
        sys.exit(1)

    print("Building HP Assistant…")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec), "--clean", "--noconfirm"],
        check=True,
    )
    dist = Path(__file__).parent / "dist" / "HP"
    print(f"\nBuild complete → {dist}")
    print("Run: dist\\HP\\HP.exe")


if __name__ == "__main__":
    main()
