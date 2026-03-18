import unittest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from scrape_tn_ac_electors import parse_rows, parse_rows_from_table


class ParseRowsTests(unittest.TestCase):
    def test_parses_district_and_ac_rows(self):
        lines = [
            "Some intro",
            "District No. District Name AC No. Name of Assembly Constituency Male Female Third Gender Total",
            "1 Chennai 11 Dr.Radhakrishnan Nagar 127413 124819 3 252235",
            "13 Perambur 127147 125078 3 252228",
            "Total 254560 249897 6 504463",
            "2 Tiruvallur 1 Gummidipoondi 115247 112750 6 228003",
            "Grand Total 330000 320000 100 650100",
        ]

        rows = parse_rows(lines)

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].district_no, 1)
        self.assertEqual(rows[0].district_name, "Chennai")
        self.assertEqual(rows[1].district_no, 1)
        self.assertEqual(rows[1].ac_no, 13)
        self.assertEqual(rows[2].district_no, 2)
        self.assertEqual(rows[2].ac_name, "Gummidipoondi")

    def test_parses_html_table_rows(self):
        html = """
        <html><body>
          <table>
            <tr>
              <th>District No.</th><th>District Name</th><th>AC No.</th>
              <th>Name of Assembly Constituency</th><th>Male</th><th>Female</th>
              <th>Third Gender</th><th>Total</th>
            </tr>
            <tr>
              <td>1</td><td>Chennai</td><td>11</td><td>Dr.Radhakrishnan Nagar</td>
              <td>127,413</td><td>124,819</td><td>3</td><td>252,235</td>
            </tr>
            <tr>
              <td>13</td><td>Perambur</td><td>127,147</td><td>125,078</td><td>3</td><td>252,228</td>
            </tr>
            <tr><td>Total</td><td>254560</td><td>249897</td><td>6</td><td>504463</td></tr>
            <tr>
              <td>2</td><td>Tiruvallur</td><td>1</td><td>Gummidipoondi</td>
              <td>115247</td><td>112750</td><td>6</td><td>228003</td>
            </tr>
            <tr><td>Grand Total</td><td>369807</td><td>362647</td><td>12</td><td>732466</td></tr>
          </table>
        </body></html>
        """

        rows = parse_rows_from_table(html)

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].district_name, "Chennai")
        self.assertEqual(rows[1].district_no, 1)
        self.assertEqual(rows[1].ac_no, 13)
        self.assertEqual(rows[1].male, 127147)
        self.assertEqual(rows[2].district_name, "Tiruvallur")


if __name__ == "__main__":
    unittest.main()
