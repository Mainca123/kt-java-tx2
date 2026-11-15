"""Create the TX2 report from the user's original screenshots."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("create-report-from-screenshots.py")), run_name="__main__")
