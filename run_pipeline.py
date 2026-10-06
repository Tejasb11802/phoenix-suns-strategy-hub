"""Run the full project pipeline in order. Usage: python run_pipeline.py"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = ["01_generate_data.py", "02_clean_and_load.py", "03_analysis.py", "04_build_powerbi.py", "05_build_report.py"]

if __name__ == "__main__":
    start = time.time()
    for step in STEPS:
        result = subprocess.run([sys.executable, str(ROOT / "src" / step)], cwd=ROOT)
        if result.returncode != 0:
            sys.exit(f"Pipeline stopped: {step} failed.")
    print(f"\nPipeline finished in {time.time() - start:.0f} seconds.")
    print("Next: open powerbi\\Phoenix_Suns_Strategy_Hub.pbip in Power BI Desktop and click Refresh.")
