# Add up a spending export without trusting it blindly

A small read-only Python tool built step by step. It reads a spending file saved as CSV (from a bank or a budgeting app), adds up money out, money in and spending by category, and lists every row it could not read instead of quietly leaving it out. It never changes the file.

## Run it

    python make_sample.py                      # makes a made-up file called sample/spending.csv
    python spendsum.py sample/spending.csv     # the report
    python -m unittest -v                      # nineteen automated tests

On Windows, if `python` is not found, use `py`.

## Files

- `spendsum.py` - the tool
- `make_sample.py` - makes the made-up practice file
- `test_spendsum.py` - tests
- `expected_output.txt` - the report the lesson shows; the automated check compares against it

## Notes

- It uses Python's `csv` module and `Decimal` numbers, so cents add up exactly. Both come with Python (see docs.python.org/3/library/csv.html and docs.python.org/3/library/decimal.html).
- It expects the columns Date, Description, Amount and Category (any order, any capital letters), dates like 2026-03-15, a dot for decimals, and negative amounts for money going out. Amounts like -12.30, $1,234.50 and (45.00) are understood. Anything else, such as 12,50 with a decimal comma, is listed as unreadable, not guessed.
- A row with more or fewer values than the header is listed as unreadable. It is never guessed at.
- Files saved with a semicolon between values, or in an old Windows text encoding, are not supported; the tool tells you it cannot read them.
- Real bank exports differ a lot. This was tested only on the made-up sample and on small test files, not on a real bank export. Check the totals against your bank before you rely on them.
- Uses only what comes with Python 3. Tested on Python 3.10 (Linux) and, by GitHub Actions, Python 3.12 on Windows and Ubuntu. Not tested on a Windows 10 or 11 desktop.
- The practice data is made up. Educational example, no warranty. Use at your own risk. This is not financial advice.
- Code is MIT licensed (see LICENSE). Python is a separate project with its own license; this repository does not include it.
