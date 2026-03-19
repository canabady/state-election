import unittest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from scrape_py_ac_electors import parse_rows_from_table


class ParseRowsTests(unittest.TestCase):
    def test_parses_puducherry_table_rows(self):
        html = """
        <table>
          <tbody>
            <tr><td colspan="5" align="CENTER"><b>PUDUCHERRY DISTRICT</b></td></tr>
            <tr>
              <td><a href='ac_wise_polling_station.php?c=MQ==' title='1.MANNADIPET'>1.MANNADIPET<td style="text-align:right;">14600</td><td style="text-align:right;">16460</td><td style="text-align:right;">3</td><td style="text-align:right;">31063</td>
            </tr>
            <tr>
              <td><a href='ac_wise_polling_station.php?c=Mg==' title='2.THIRUBHUVANAI'>2.THIRUBHUVANAI (SC) </a></td><td style="text-align:right;">14976</td><td style="text-align:right;">16867</td><td style="text-align:right;">0</td><td style="text-align:right;">31843</td>
            </tr>
            <tr><td style="text-align:right;">Puducherry District Total</td><td>29576</td><td>33327</td><td>3</td><td>62906</td></tr>
            <tr><td colspan="5" align="CENTER"><b>KARAIKAL DISTRICT</b></td></tr>
            <tr>
              <td><a href='ac_wise_polling_station.php?c=MjQ=' title='24.NEDUNGADU'>24.NEDUNGADU (SC) </a></td><td>14776</td><td>16724</td><td>6</td><td>31506</td>
            </tr>
            <tr><td style="text-align:right;">U.T. Total</td><td>443595</td><td>500477</td><td>139</td><td>944211</td></tr>
          </tbody>
        </table>
        """

        rows = parse_rows_from_table(html)

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].district_no, 1)
        self.assertEqual(rows[0].district_name, "Puducherry")
        self.assertEqual(rows[0].ac_no, 1)
        self.assertEqual(rows[0].ac_name, "MANNADIPET")
        self.assertEqual(rows[1].ac_name, "THIRUBHUVANAI (SC)")
        self.assertEqual(rows[2].district_no, 2)
        self.assertEqual(rows[2].district_name, "Karaikal")
        self.assertEqual(rows[2].ac_no, 24)
        self.assertEqual(rows[2].total, 31506)


if __name__ == "__main__":
    unittest.main()
