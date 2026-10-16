import contextlib
import io
import os
import tempfile
import shutil
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path

import make_sample
import spendsum


def write(folder, text, bom=False, newline="\r\n"):
    path = Path(folder) / "t.csv"
    data = text.replace("\n", newline)
    path.write_bytes((("\ufeff" if bom else "") + data).encode("utf-8"))
    return path


HEAD = "Date,Description,Amount,Category\n"


class AmountTests(unittest.TestCase):
    def test_plain_and_signs(self):
        self.assertEqual(spendsum.parse_amount("12.30"), Decimal("12.30"))
        self.assertEqual(spendsum.parse_amount("-12.30"), Decimal("-12.30"))
        self.assertEqual(spendsum.parse_amount("(45.00)"), Decimal("-45.00"))

    def test_dollar_and_thousands(self):
        self.assertEqual(spendsum.parse_amount("$1,234.50"), Decimal("1234.50"))
        self.assertEqual(spendsum.parse_amount("-$4.50"), Decimal("-4.50"))
        self.assertEqual(spendsum.parse_amount("$-4.50"), Decimal("-4.50"))

    def test_refuses_unclear_text(self):
        for bad in ["abc", "", "1.2.3", "12,50", "1,23,456", "NaN", "1e5"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    spendsum.parse_amount(bad)

    def test_extra_decimals_are_refused_not_rounded(self):
        for bad in ["12.345", "0.001", "1,000.999"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError) as caught:
                    spendsum.parse_amount(bad)
                self.assertIn("decimal places", str(caught.exception))

    def test_other_currencies_and_odd_digits_are_refused(self):
        for bad in ["\u20ac12.00", "12.00 USD", "USD 12.00", "\u0663", "\uff11\uff12"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    spendsum.parse_amount(bad)

    def test_huge_numbers_are_refused(self):
        self.assertEqual(spendsum.parse_amount("999999999999.99"), Decimal("999999999999.99"))
        with self.assertRaises(ValueError):
            spendsum.parse_amount("9999999999999.99")

    def test_pennies_add_up_exactly(self):
        total = sum([spendsum.parse_amount("0.10")] * 3, Decimal(0)) - spendsum.parse_amount("0.30")
        self.assertEqual(total, 0)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def read(self, text, **kw):
        return spendsum.read_rows(write(self.tmp.name, text, **kw))

    def test_excel_marker_and_windows_line_ends(self):
        rows, problems, _ = self.read(HEAD + "2026-01-02,A,-1.00,Food\n", bom=True)
        self.assertEqual(len(rows), 1)
        self.assertEqual(problems, [])

    def test_comma_inside_quotes_is_one_value(self):
        rows, problems, _ = self.read(HEAD + '2026-01-02,"Shop, big",-3.00,Food\n')
        self.assertEqual(rows[0][1], "Shop, big")

    def test_unquoted_extra_comma_is_refused_not_misread(self):
        rows, problems, _ = self.read(HEAD + "2026-01-02,Cinema,-12,50,Fun\n")
        self.assertEqual(rows, [])
        self.assertEqual(len(problems), 1)

    def test_column_order_and_case_do_not_matter(self):
        rows, _, _ = self.read("category,AMOUNT,Date,description\nFood,-2.00,2026-01-02,x\n")
        self.assertEqual(rows[0][2], Decimal("-2.00"))
        self.assertEqual(rows[0][3], "Food")

    def test_missing_column_names_it(self):
        with self.assertRaises(ValueError) as caught:
            self.read("Date,Amount\n2026-01-01,1\n")
        self.assertIn("category", str(caught.exception))

    def test_repeated_needed_column_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            self.read("Date,Description,Amount,Category,Amount\n2026-01-01,A,1,Food,2\n")
        self.assertIn("more than once", str(caught.exception))

    def test_broken_quotes_refuse_the_whole_file(self):
        with self.assertRaises(ValueError) as caught:
            self.read(HEAD + '2026-01-02,"Shop"x,-3.00,Food\n')
        self.assertIn("Nothing was totalled", str(caught.exception))

    def test_empty_file(self):
        with self.assertRaises(ValueError):
            self.read("")

    def test_blank_lines_are_counted(self):
        _, _, blanks = self.read(HEAD + "\n\n2026-01-02,A,-1,Food\n")
        self.assertEqual(blanks, 2)

    def test_problem_rows_name_their_line(self):
        _, problems, _ = self.read(HEAD + "2026-01-02,A,-1,Food\nbad-date,B,-1,Food\n")
        self.assertTrue(problems[0].startswith("line 3:"))

    def test_bad_dates(self):
        _, problems, _ = self.read(HEAD + "2026-02-30,A,-1,Food\n03/04/2026,B,-1,Food\n")
        self.assertEqual(len(problems), 2)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_totals_and_order(self):
        path = write(self.tmp.name, HEAD + "2026-01-01,Pay,100.00,Income\n2026-01-02,A,-10.10,Food\n2026-01-03,B,-20.20,Bills\n2026-01-04,C,-5.05,Food\n")
        out = spendsum.report(path)
        self.assertIn("Money out: 35.35", out)
        self.assertIn("Money in:  100.00", out)
        self.assertIn("Net:       64.65", out)
        self.assertLess(out.index("Bills"), out.index("Food"))
        self.assertIn("15.15", out)

    def test_problem_rows_are_listed_and_excluded(self):
        path = write(self.tmp.name, HEAD + "2026-01-02,A,-10.00,Food\n2026-01-03,B,oops,Food\n")
        out = spendsum.report(path)
        self.assertIn("Money out: 10.00", out)
        self.assertIn("line 3", out)
        self.assertIn("Skipped 1 row", out)

    def test_missing_category(self):
        path = write(self.tmp.name, HEAD + "2026-01-02,A,-10.00,\n")
        self.assertIn("(none)", spendsum.report(path))

    def test_report_says_one_currency(self):
        path = write(self.tmp.name, HEAD + "2026-01-02,A,-10.00,Food\n")
        self.assertIn("one currency", spendsum.report(path))

    def test_file_is_not_changed(self):
        path = write(self.tmp.name, HEAD + "2026-01-02,A,-10.00,Food\n")
        before = (path.read_bytes(), os.stat(path).st_mtime_ns)
        spendsum.report(path)
        self.assertEqual(before, (path.read_bytes(), os.stat(path).st_mtime_ns))

    def test_sample_known_totals(self):
        path = make_sample.make(Path(self.tmp.name) / "sample")
        out = spendsum.report(path)
        self.assertIn("Money out: 1,351.40", out)
        self.assertIn("Skipped 3 row(s)", out)

    def run_main(self, args):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = spendsum.main(args)
        return code, buffer.getvalue()

    def test_main_codes(self):
        self.assertEqual(self.run_main([])[0], 2)
        code, text = self.run_main([str(Path(self.tmp.name) / "nope.csv")])
        self.assertEqual(code, 2)
        self.assertIn("Could not find", text)
        bad = Path(self.tmp.name) / "b.csv"
        bad.write_bytes(b"\xff\xfe\x00bad")
        code, text = self.run_main([str(bad)])
        self.assertEqual(code, 2)
        self.assertIn("UTF-8", text)
        self.assertEqual(self.run_main([str(make_sample.make(Path(self.tmp.name) / "sample"))])[0], 0)


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "sample"

    def snapshot(self):
        return sorted((p.relative_to(self.root).as_posix(),p.is_dir(),p.stat().st_mtime_ns,
                       p.read_bytes() if p.is_file() else None) for p in self.root.rglob("*"))

    def test_existing_folder_and_nested_data_preserved(self):
        (self.root/"nested").mkdir(parents=True)
        (self.root/"spending.csv").write_bytes(b"ORIGINAL")
        (self.root/"nested/keep").write_bytes(b"KEEP")
        before=self.snapshot()
        with self.assertRaises(FileExistsError):make_sample.make(self.root)
        self.assertEqual(before,self.snapshot())

    def test_existing_file_preserved(self):
        self.root.write_bytes(b"KEEP");before=self.root.stat().st_mtime_ns
        with self.assertRaises(FileExistsError):make_sample.make(self.root)
        self.assertEqual(self.root.read_bytes(),b"KEEP")
        self.assertEqual(self.root.stat().st_mtime_ns,before)

    def test_repeat_setup_and_extra_file_preserved(self):
        make_sample.make(self.root)
        (self.root/"extra.txt").write_bytes(b"KEEP");before=self.snapshot()
        with self.assertRaises(FileExistsError):make_sample.make(self.root)
        self.assertEqual(before,self.snapshot())

    def test_cli_refuses_existing_path(self):
        script=Path(self.tmp.name)/"make_sample.py"
        shutil.copyfile(Path(make_sample.__file__),script)
        self.root.mkdir();(self.root/"keep").write_bytes(b"KEEP")
        before=self.snapshot()
        result=subprocess.run([sys.executable,str(script)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertIn("Nothing was replaced or deleted",result.stderr)
        self.assertEqual(before,self.snapshot())


if __name__ == "__main__":
    unittest.main()
