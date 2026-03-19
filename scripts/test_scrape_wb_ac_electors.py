import unittest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from scrape_wb_ac_electors import parse_rows_from_text


class ParseRowsTests(unittest.TestCase):
    def test_parses_wb_ac_rows(self):
        text = """
AC wise Status of Polling Stations and Electors in Draft Electoral Roll w.r.t 01.01.2026 (SIR)
Name of District Assembly Constituency No. of Polling Station Male Female Third Gender Total
COOCHBEHAR 1 Mekliganj 239 119553 112317 3 231873
COOCHBEHAR 2 Mathabhanga 276 134478 123989 1 258468
KOLKATA NORTH 162 Chowrangee 222 72340 63390 6 135736
NORTH 24 PARGANAS 94 Bagda 300 137251 125883 8 263142
Total 80681 36199391 34615837 1402 70816630
"""

        rows = parse_rows_from_text(text)

        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0].district_name, "COOCHBEHAR")
        self.assertEqual(rows[0].ac_no, 1)
        self.assertEqual(rows[0].polling_stations, 239)
        self.assertEqual(rows[0].total, 231873)

        self.assertEqual(rows[2].district_name, "KOLKATA NORTH")
        self.assertEqual(rows[2].ac_no, 162)
        self.assertEqual(rows[2].ac_name, "Chowrangee")
        self.assertEqual(rows[3].district_name, "NORTH 24 PARGANAS")
        self.assertEqual(rows[3].ac_no, 94)
        self.assertEqual(rows[3].ac_name, "Bagda")


if __name__ == "__main__":
    unittest.main()
