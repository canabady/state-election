#!/usr/bin/env python3
"""Scrape TN AC-wise elector gender counts and save as CSV.

Source page:
https://www.elections.tn.gov.in/ACwise_Gendercount_23022026.aspx
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

DEFAULT_URL = "https://www.elections.tn.gov.in/ACwise_Gendercount_23022026.aspx"
DEFAULT_OUTPUT = Path("public/data/tn_ac_wise_electors.csv")

DISTRICT_ROW_RE = re.compile(
    r"^(\d+)\s+(.+?)\s+(\d+)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$"
)
AC_ROW_RE = re.compile(r"^(\d+)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$")
TOTAL_RE = re.compile(r"^Total\s+\d+\s+\d+\s+\d+\s+\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class ElectorRow:
    district_no: int
    district_name: str
    ac_no: int
    ac_name: str
    male: int
    female: int
    third_gender: int
    total: int


class TextExtractor(HTMLParser):
    """Collect visible text from HTML while skipping script/style blocks."""

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._skip_depth == 0:
            self.parts.append(data)


class TableRowExtractor(HTMLParser):
    """Extract table rows as cell text arrays."""

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._in_td = False
        self._in_tr = False
        self._cell_parts: list[str] = []
        self._current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        if tag == "tr":
            self._in_tr = True
            self._current_row = []
        elif tag in {"td", "th"} and self._in_tr:
            self._in_td = True
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if self._skip_depth > 0:
            return
        if tag in {"td", "th"} and self._in_td:
            cell = re.sub(r"\s+", " ", "".join(self._cell_parts)).strip()
            self._current_row.append(cell)
            self._in_td = False
            self._cell_parts = []
        elif tag == "tr" and self._in_tr:
            cleaned = [c.replace("\xa0", " ").strip() for c in self._current_row]
            if any(cleaned):
                self.rows.append(cleaned)
            self._current_row = []
            self._in_tr = False

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._skip_depth == 0 and self._in_td:
            self._cell_parts.append(data)


def fetch_html(url: str, timeout: int = 30) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(req, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def normalize_lines(html: str) -> list[str]:
    parser = TextExtractor()
    parser.feed(html)
    parser.close()

    raw = "\n".join(parser.parts)
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
    return [line for line in lines if line]


def normalize_number(value: str) -> int:
    value = re.sub(r"[,\s]", "", value)
    if not value.isdigit():
        raise ValueError(f"Invalid numeric value: {value!r}")
    return int(value)


def is_header_row(cells: list[str]) -> bool:
    row = " ".join(cells).lower()
    return "district no" in row and "assembly constituency" in row


def parse_rows_from_table(html: str) -> list[ElectorRow]:
    parser = TableRowExtractor()
    parser.feed(html)
    parser.close()

    rows: list[ElectorRow] = []
    current_district_no: int | None = None
    current_district_name: str | None = None
    in_data = False

    for raw_cells in parser.rows:
        cells = [c.strip() for c in raw_cells if c.strip()]
        if not cells:
            continue

        if not in_data:
            if is_header_row(cells):
                in_data = True
            continue

        first = cells[0].lower()
        if first.startswith("grand total"):
            break
        if first.startswith("total"):
            continue

        if len(cells) >= 8 and cells[0].isdigit() and cells[2].isdigit():
            district_no = int(cells[0])
            district_name = cells[1]
            ac_no = int(cells[2])
            ac_name = cells[3]
            male = normalize_number(cells[4])
            female = normalize_number(cells[5])
            third_gender = normalize_number(cells[6])
            total = normalize_number(cells[7])

            current_district_no = district_no
            current_district_name = district_name

            rows.append(
                ElectorRow(
                    district_no=district_no,
                    district_name=district_name,
                    ac_no=ac_no,
                    ac_name=ac_name,
                    male=male,
                    female=female,
                    third_gender=third_gender,
                    total=total,
                )
            )
            continue

        if len(cells) >= 6 and cells[0].isdigit() and current_district_no is not None and current_district_name is not None:
            rows.append(
                ElectorRow(
                    district_no=current_district_no,
                    district_name=current_district_name,
                    ac_no=int(cells[0]),
                    ac_name=cells[1],
                    male=normalize_number(cells[2]),
                    female=normalize_number(cells[3]),
                    third_gender=normalize_number(cells[4]),
                    total=normalize_number(cells[5]),
                )
            )

    return rows


def parse_rows(lines: Iterable[str]) -> list[ElectorRow]:
    rows: list[ElectorRow] = []
    current_district_no: int | None = None
    current_district_name: str | None = None
    in_table = False

    for line in lines:
        if not in_table:
            if "District No." in line and "Assembly Constituency" in line:
                in_table = True
            continue

        if line.lower().startswith("grand total"):
            break

        if TOTAL_RE.match(line):
            continue

        district_match = DISTRICT_ROW_RE.match(line)
        if district_match:
            district_no = int(district_match.group(1))
            district_name = district_match.group(2).strip()
            ac_no = int(district_match.group(3))
            ac_name = district_match.group(4).strip()
            male = int(district_match.group(5))
            female = int(district_match.group(6))
            third_gender = int(district_match.group(7))
            total = int(district_match.group(8))

            current_district_no = district_no
            current_district_name = district_name

            rows.append(
                ElectorRow(
                    district_no=district_no,
                    district_name=district_name,
                    ac_no=ac_no,
                    ac_name=ac_name,
                    male=male,
                    female=female,
                    third_gender=third_gender,
                    total=total,
                )
            )
            continue

        ac_match = AC_ROW_RE.match(line)
        if ac_match and current_district_no is not None and current_district_name is not None:
            rows.append(
                ElectorRow(
                    district_no=current_district_no,
                    district_name=current_district_name,
                    ac_no=int(ac_match.group(1)),
                    ac_name=ac_match.group(2).strip(),
                    male=int(ac_match.group(3)),
                    female=int(ac_match.group(4)),
                    third_gender=int(ac_match.group(5)),
                    total=int(ac_match.group(6)),
                )
            )

    if not rows:
        raise ValueError("No AC rows parsed. Page structure may have changed.")

    return rows


def write_csv(rows: Iterable[ElectorRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "district_no",
                "district_name",
                "ac_no",
                "ac_name",
                "male",
                "female",
                "third_gender",
                "total",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.district_no,
                    row.district_name,
                    row.ac_no,
                    row.ac_name,
                    row.male,
                    row.female,
                    row.third_gender,
                    row.total,
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape TN AC-wise elector gender counts and save as CSV."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Source page URL")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output CSV path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    try:
        html = fetch_html(args.url)
        rows = parse_rows_from_table(html)
        if not rows:
            lines = normalize_lines(html)
            rows = parse_rows(lines)
        write_csv(rows, output_path)
    except (HTTPError, URLError) as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1

    print(f"Saved {len(rows)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
