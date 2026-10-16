# Add up a spending export without trusting it blindly

A small read-only Python tool built step by step. It reads a spending file saved as CSV (from a bank or a budgeting app), adds up money out, money in and spending by category, and lists every row it could not read instead of quietly leaving it out. It never changes the file.

Setup creates a new sample folder, exclusively writes its fictional CSV and refuses any existing path. It never resets or replaces old sample data. Start only in a new empty lesson folder. Reports reveal categories, paths and problem details; do not share private output.

## Run it

    python make_sample.py                      # makes a made-up file called sample/spending.csv
    python spendsum.py sample/spending.csv     # the report
    python -m unittest -v                      # 29 temporary-fixture tests

On Windows, if `python` is not found, use `py`.

## Files

- `spendsum.py` - the tool
- `make_sample.py` - makes the made-up practice file
- `test_spendsum.py` - tests
- `expected_output.txt` - the report the lesson shows; the automated check compares against it

## Evidence

Two Windows and two Ubuntu recordings pass all 29 tests. Each platform's paired outputs differ only in unittest time. Displays use first Windows output, not mixed recordings. The recorder saves the visible first comma-splitting version then the final checker inside a unique temporary folder and removes only that recording folder. Setup itself stops on a second run. The checker is unchanged in this repair. Four added setup collision/repeat tests preserve nested unrelated bytes and modification times. These are limited fixture passes, not universal safety proof.

## Notes

- It uses Python's `csv` module and `Decimal` numbers, which come with Python (https://docs.python.org/3/library/csv.html and https://docs.python.org/3/library/decimal.html). Decimal adds exactly for the amounts this tool accepts: up to 12 digits before the point and at most 2 after it. Anything else is listed as unreadable, not rounded.
- One currency only. The tool does not read currency names or convert anything. It accepts a plain number, optionally with a leading `$` or in brackets, and treats every amount as the same currency. Other symbols or codes (for example a euro sign or `USD`) are listed as unreadable. If your file mixes currencies, do not use these totals.
- It expects the columns Date, Description, Amount and Category (any order, any capital letters), dates like 2026-03-15, a dot for decimals, and negative amounts for money going out. Amounts like -12.30, $1,234.50 and (45.00) are understood. Anything else, such as 12,50 with a decimal comma, is listed as unreadable, not guessed.
- A row with more or fewer values than the header is listed as unreadable. It is never guessed at. A column name that appears twice (for example two Amount columns), or quotes that are broken, make the tool stop with a message and total nothing.
- A test checks that one small test file has the same bytes and modified time after a run. That is the only evidence that the tool leaves files unchanged.
- Files saved with a semicolon between values, or in an old Windows text encoding, are not supported; the tool tells you it cannot read them.
- Real bank exports differ a lot. This was tested only on the made-up sample and on small test files, not on a real bank export. Check the totals against your bank before you rely on them.
- Uses only what comes with Python 3. Tested on Python 3.10 (Linux) and, by GitHub Actions, Python 3.12 on Windows and Ubuntu. Not tested on a Windows 10 or 11 desktop.
- The practice data is made up. Educational example, no warranty. Use at your own risk. This is not financial advice.
- Code is MIT licensed (see LICENSE). Python is a separate project with its own license; this repository does not include it.
