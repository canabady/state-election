import unittest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from scrape_as_ac_electors import parse_rows_from_text


class ParseRowsTests(unittest.TestCase):
    def test_parses_rows_with_wrapped_district_and_ac_name(self):
        text = """
Assembly Constituency wise Final Electors
and Polling Stations
1 Kokrajhar 1 Gossaigaon 154 57469 57012 5 114486
2 Dotma (ST) 146 53180 53831 0 107011
944 352780 351436 9 704225
31 West Karbi 111 Rongkhang (ST) 193 66358 65499 1 131858
Anglong 112 Amri (ST) 165 49919 50178 0 100097
358 116277 115677 1 231955
35 Sribhumi 125 Patharkandi 228 91421 88776 4 180201
126
Ram Krishna Nagar
(SC) 277 110669 105723 4 216396
1187 482436 458201 12 940649
State Total
"""
        rows = parse_rows_from_text(text)

        self.assertEqual(len(rows), 6)

        self.assertEqual(rows[0].district_no, 1)
        self.assertEqual(rows[0].district_name, "Kokrajhar")
        self.assertEqual(rows[0].ac_no, 1)
        self.assertEqual(rows[0].polling_stations, 154)

        self.assertEqual(rows[3].district_no, 31)
        self.assertEqual(rows[3].district_name, "West Karbi Anglong")
        self.assertEqual(rows[3].ac_no, 112)

        self.assertEqual(rows[5].district_no, 35)
        self.assertEqual(rows[5].ac_no, 126)
        self.assertEqual(rows[5].ac_name, "Ram Krishna Nagar (SC)")
        self.assertEqual(rows[5].polling_stations, 277)
        self.assertEqual(rows[5].total, 216396)


if __name__ == "__main__":
    unittest.main()
