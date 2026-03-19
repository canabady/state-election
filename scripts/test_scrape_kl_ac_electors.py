import unittest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from scrape_kl_ac_electors import parse_rows_from_text


class ParseRowsTests(unittest.TestCase):
    def test_parses_ac_rows_with_wrapped_district_name(self):
        text = """
ASSEMBLY CONSTITUANCE WISE ELECTORS
(GENERAL + OVERSEAS)
DISTRICT NAME LAC NAME Male Electors Female Electors Third Gender Electors DISTRICT TOTAL
1-KASARAGOD 1-MANJESHWAR 114570 112833 0 227403
2-KASARAGOD 104866 104866 0 209732
1-KASARAGOD 3-UDMA 111473 115723 4 227200
DISTRICT TOTAL 219436 217699 0 437135
14-
THIRUVANANTHAPURAM 134-THIRUVANANTHAPURAM 75669 81769 15 157453
135-NEMOM 81809 87553 9 169371
DISTRICT TOTAL 157478 169322 24 326800
DISTRICTWISE -OVERSEAS (NRI ) ELECTORS
"""

        rows = parse_rows_from_text(text)

        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0].district_no, 1)
        self.assertEqual(rows[0].district_name, "KASARAGOD")
        self.assertEqual(rows[0].ac_no, 1)

        self.assertEqual(rows[2].district_no, 1)
        self.assertEqual(rows[2].ac_no, 3)
        self.assertEqual(rows[2].ac_name, "UDMA")

        self.assertEqual(rows[3].district_no, 14)
        self.assertEqual(rows[3].district_name, "THIRUVANANTHAPURAM")
        self.assertEqual(rows[3].ac_no, 134)
        self.assertEqual(rows[3].ac_name, "THIRUVANANTHAPURAM")
        self.assertEqual(rows[3].third_gender, 15)

        self.assertEqual(rows[4].district_no, 14)
        self.assertEqual(rows[4].ac_no, 135)
        self.assertEqual(rows[4].ac_name, "NEMOM")


if __name__ == "__main__":
    unittest.main()
