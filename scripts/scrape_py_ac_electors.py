#!/usr/bin/env python3
"""Scrape Puducherry AC-wise elector gender counts and save as CSV.

Source page:
https://ceopuducherry.py.gov.in/ac_wise_electrol.php
"""

from __future__ import annotations

import argparse
import csv
import html as html_lib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_URL = "https://ceopuducherry.py.gov.in/ac_wise_electrol.php"
DEFAULT_OUTPUT = Path("public/data/states/py/electors.csv")

TBODY_RE = re.compile(r"<tbody[^>]*>(.*?)</tbody>", re.IGNORECASE | re.DOTALL)
TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
DISTRICT_RE = re.compile(r"^([A-Z][A-Z\s.'-]+ DISTRICT)$")
AC_ROW_RE = re.compile(
    r"^(\d+)\.\s*(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)$"
)


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


def normalize_text(value: str) -> str:
    value = html_lib.unescape(value).replace("\xa0", " ")
    value = TAG_RE.sub(" ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_number(value: str) -> int:
    value = re.sub(r"[,\s]", "", value)
    if not value.isdigit():
        raise ValueError(f"Invalid numeric value: {value!r}")
    return int(value)


def normalize_district_name(value: str) -> str:
    value = value.strip().replace(" DISTRICT", "")
    return value.title()


def extract_table_body(html: str) -> str:
    tbody_match = TBODY_RE.search(html)
    if tbody_match:
        return tbody_match.group(1)

    lower_html = html.lower()
    tbody_start = lower_html.find("<tbody")
    if tbody_start == -1:
        raise ValueError("Could not locate AC elector table body")

    tbody_content_start = lower_html.find(">", tbody_start)
    if tbody_content_start == -1:
        raise ValueError("Malformed tbody tag in source HTML")

    table_end = lower_html.find("</table", tbody_content_start + 1)
    if table_end == -1:
        raise ValueError("Could not locate end of AC elector table")

    return html[tbody_content_start + 1 : table_end]


def parse_rows_from_table(html: str) -> list[ElectorRow]:
    tbody_html = extract_table_body(html)
    rows: list[ElectorRow] = []

    district_no = 0
    current_district_no: int | None = None
    current_district_name: str | None = None

    for tr_html in TR_RE.findall(tbody_html):
        row_text = normalize_text(tr_html)
        if not row_text:
            continue

        district_match = DISTRICT_RE.match(row_text.upper())
        if district_match:
            district_no += 1
            current_district_no = district_no
            current_district_name = normalize_district_name(district_match.group(1))
            continue

        row_text_lower = row_text.lower()
        if "district total" in row_text_lower or "u.t. total" in row_text_lower:
            continue

        ac_match = AC_ROW_RE.match(row_text)
        if ac_match and current_district_no is not None and current_district_name is not None:
            rows.append(
                ElectorRow(
                    district_no=current_district_no,
                    district_name=current_district_name,
                    ac_no=int(ac_match.group(1)),
                    ac_name=ac_match.group(2).strip(),
                    male=normalize_number(ac_match.group(3)),
                    female=normalize_number(ac_match.group(4)),
                    third_gender=normalize_number(ac_match.group(5)),
                    total=normalize_number(ac_match.group(6)),
                )
            )

    if not rows:
        raise ValueError("No AC rows parsed. Page structure may have changed.")

    return rows


def write_csv(rows: Iterable[ElectorRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
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
        description="Scrape Puducherry AC-wise elector gender counts and save as CSV."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Source page URL")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output CSV path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    try:
        html = fetch_html(args.url)
        rows = parse_rows_from_table(html)
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
