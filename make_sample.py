"""Creates a small, made-up spending export called sample/spending.csv next to this script.

Run only in a new empty lesson folder: python make_sample.py
Any existing sample path is refused, not reset or replaced.
It copies what a bank export often looks like: a hidden marker at the start (as Excel
adds), names with commas inside quotes, amounts with dollar signs and thousands commas,
brackets for negative amounts, a blank line, and a few rows with problems.
"""
import sys
from pathlib import Path

LINES = [
    "Date,Description,Amount,Category",
    "2026-03-01,Salary,\"2,500.00\",Income",
    "2026-03-02,\"Supermarket, weekly shop\",-84.10,Food",
    "2026-03-03,Bus pass,-30.00,Transport",
    "2026-03-04,Cafe,$-4.50,Food",
    "2026-03-05,Rent,\"-1,200.00\",Housing",
    "2026-03-06,Phone bill,(25.00),Bills",
    "",
    "2026-03-07,Cinema,-12,50,Fun",
    "2026-03-08,Refund,15.25,Food",
    "March 9,Taxi,-9.00,Transport",
    "2026-03-10,Mystery,-7.80,",
    "2026-03-11,Books,abc,Fun",
]


def make(folder):
    folder = Path(folder)
    folder.mkdir()  # Refuse any existing file, folder or link.
    target = folder / "spending.csv"
    with target.open("xb") as handle:
        handle.write(("\ufeff" + "\r\n".join(LINES) + "\r\n").encode("utf-8"))
    return target


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    try:
        make(here / "sample")
    except FileExistsError:
        raise SystemExit("Stopped: sample already exists. Nothing was replaced or deleted.")
    print("Made sample/spending.csv")
    sys.exit(0)
