
"""
Runner for Moonlighter Optimizer (web + CLI)
Provides run_optimizer(csv_path, night_slots=1, strategy='balanced') -> dict
Also writes CSV outputs when run as a script.
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from moonlighter_optimizer import run_from_csv, MoonlighterScheduleOptimizer

def run_optimizer(csv_path: str, night_slots: int = 1, strategy: str = "balanced"):
    return run_from_csv(csv_path, night_slots=night_slots, strategy=strategy)

def _write_csv_outputs(result: dict, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1) Schedule
    rows = []
    for date, fids in result["schedule"].items():
        for fid in fids:
            rows.append({
                "date": date,
                "faculty_id": fid,
                "faculty_name": next((s["name"] for s in result["summary"] if s["id"]==fid), "")
            })
    pd.DataFrame(rows).to_csv(outdir / f"moonlighter_schedule_{stamp}.csv", index=False)

    # 2) Summary
    pd.DataFrame(result["summary"]).to_csv(outdir / f"moonlighter_schedule_summary_{stamp}.csv", index=False)

    # 3) Requests analysis (placeholder)

    pd.DataFrame([]).to_csv(outdir / f"moonlighter_schedule_requests_{stamp}.csv", index=False)

if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="moonlighter_template.csv", help="Path to input CSV")
    ap.add_argument("--strategy", default="balanced", choices=["balanced","coverage","satisfaction"])
    ap.add_argument("--night-slots", type=int, default=1, help="Number of people per night")
    ap.add_argument("--outdir", default=".", help="Folder for CSV outputs")
    args = ap.parse_args()

    try:
        result = run_optimizer(args.csv, night_slots=args.night_slots, strategy=args.strategy)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(json.dumps(result, indent=2))
    _write_csv_outputs(result, Path(args.outdir))
