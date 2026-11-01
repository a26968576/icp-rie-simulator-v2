"""Convenience launcher (also the PyInstaller entry script)."""
import sys
from icpsim.app.main import main

if __name__ == "__main__":
    sys.exit(main())
