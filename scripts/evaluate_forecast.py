"""Print the recorded offline challenger selection without retraining."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, nargs="?", default=Path("runtime/forecast_evaluation.json"))
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    for row in report["selected"]:
        print(f"{row['supplier']} | {row['unit']} | {row['segment']} | "
              f"{row['method']}: WAPE {row['wape_pct']}, bias {row['bias_pct']}; "
              f"selected {row['selected_method']}")


if __name__ == "__main__":
    main()
