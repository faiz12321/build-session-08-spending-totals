"""Add up a spending export (CSV file) by category. It only reads the file.

Usage:  python spendsum.py FILE.csv
The file needs the columns Date, Description, Amount and Category.
Dates look like 2026-03-15. Money going out is negative, money coming in is positive.
"""
import csv
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation

NEEDED = ["date", "description", "amount", "category"]
PLAIN = re.compile(r"^\d{1,3}(,\d{3})*(\.\d+)?$|^\d+(\.\d+)?$")


def parse_amount(text):
    """Turn text like -12.30, $1,234.50 or (45.00) into a Decimal. Raise ValueError if unsure."""
    raw = text.strip()
    negative = raw.startswith("(") and raw.endswith(")")
    if negative:
        raw = raw[1:-1].strip()
    for _ in range(2):
        if raw.startswith("-"):
            negative = True
            raw = raw[1:].strip()
        raw = raw.lstrip("$").strip()
    if not PLAIN.match(raw):
        if re.match(r"^\d+,\d{1,2}$", raw):
            raise ValueError("looks like a decimal comma (12,50); this tool expects a dot (12.50)")
        raise ValueError(f"not a number: {text.strip() or '(empty)'}")
    try:
        value = Decimal(raw.replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"not a number: {text.strip()}")
    return -value if negative else value


def money(value):
    return f"{value:,.2f}"


def read_rows(path):
    """Return (rows, problems, blank_count). Every line that cannot be used is listed in problems."""
    rows, problems, blanks = [], [], 0
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            raise ValueError("The file is empty.")
        names = [h.strip().lower() for h in header]
        missing = [n for n in NEEDED if n not in names]
        if missing:
            raise ValueError("Missing column(s): " + ", ".join(missing) + ". Found: " + ", ".join(h.strip() for h in header))
        at = {n: names.index(n) for n in NEEDED}
        for row in reader:
            line = reader.line_num
            if not any(cell.strip() for cell in row):
                blanks += 1
                continue
            if len(row) != len(header):
                problems.append(f"line {line}: has {len(row)} columns but the header has {len(header)} (a comma inside a value that is not in quotes?)")
                continue
            try:
                day = date.fromisoformat(row[at["date"]].strip())
            except ValueError:
                problems.append(f"line {line}: date is not like 2026-03-15: {row[at['date']].strip() or '(empty)'}")
                continue
            try:
                amount = parse_amount(row[at["amount"]])
            except ValueError as error:
                problems.append(f"line {line}: {error}")
                continue
            category = row[at["category"]].strip() or "(none)"
            rows.append((day, row[at["description"]].strip(), amount, category))
    return rows, problems, blanks


def report(path):
    rows, problems, blanks = read_rows(path)
    spent = {}
    received = Decimal(0)
    for _, _, amount, category in rows:
        if amount < 0:
            spent[category] = spent.get(category, Decimal(0)) - amount
        else:
            received += amount
    total_spent = sum(spent.values(), Decimal(0))
    lines = [f"File: {path}", f"Used {len(rows)} rows" + (f" from {min(r[0] for r in rows)} to {max(r[0] for r in rows)}" if rows else "") + f". Skipped {len(problems)} row(s) that could not be read, and {blanks} blank line(s).", "",
             f"Money out: {money(total_spent)}", f"Money in:  {money(received)}", f"Net:       {money(received - total_spent)}", "", "Spent by category:"]
    ranked = sorted(spent.items(), key=lambda item: (-item[1], item[0]))
    lines += [f"  {money(value):>12}  {name}" for name, value in ranked] or ["  (nothing spent)"]
    if problems:
        lines += ["", "Rows that could not be read (not included in any total):"] + [f"  {p}" for p in problems]
    return "\n".join(lines)


def main(argv):
    try:
        sys.stdout.reconfigure(errors="replace")
    except AttributeError:
        pass
    if len(argv) != 1:
        print("Usage: python spendsum.py FILE.csv")
        return 2
    try:
        print(report(argv[0]))
    except FileNotFoundError:
        print(f"Could not find {argv[0]}")
        return 2
    except UnicodeDecodeError:
        print(f"Could not read {argv[0]}: it is not a UTF-8 text file. In Excel, save it as CSV UTF-8.")
        return 2
    except ValueError as error:
        print(error)
        return 2
    except OSError as error:
        print(f"Could not read {argv[0]}: {error.strerror or error}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
