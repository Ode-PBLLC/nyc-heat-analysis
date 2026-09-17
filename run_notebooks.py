#!/usr/bin/env python3
"""Execute the analysis notebooks in order and save them with their outputs.

    python3 run_notebooks.py                       # runs the four analysis notebooks
    python3 run_notebooks.py --workbook PATH       # also runs 04a aggregate_dss.ipynb against the DSS workbook

Each notebook runs with its own directory as the working directory and writes its data/ files. Requires
Jupyter (nbformat, nbclient, ipykernel) with a kernel named python3 that has geopandas, pandas, numpy,
shapely and openpyxl installed.
"""
import argparse
import os
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent
ANALYSIS = [
    "01_heat_vulnerability_map/analysis.ipynb",
    "02_no_working_ac/analysis.ipynb",
    "03_days_at_or_above_90f/analysis.ipynb",
    "04_heat_vulnerability_overlap/analysis.ipynb",
]
AGGREGATE = "04_heat_vulnerability_overlap/aggregate_dss.ipynb"


def run(relative: str) -> None:
    path = ROOT / relative
    notebook = nbformat.read(path, as_version=4)
    NotebookClient(notebook, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(path.parent)}}).execute()
    nbformat.write(notebook, path)
    print(f"ran {relative}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workbook", type=Path, help="DSS workbook; when given, aggregate_dss.ipynb runs first")
    args = parser.parse_args()
    if args.workbook:
        os.environ["DSS_WORKBOOK"] = str(args.workbook.resolve())
        run(AGGREGATE)
    for relative in ANALYSIS:
        run(relative)
