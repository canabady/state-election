#!/usr/bin/env python3
"""Scrape Assam AC-wise electors and polling stations from official PDF."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_URL = "https://ceoassam.nic.in/summary/2026/Final%20Electors_10-02-2026.pdf"
DEFAULT_OUTPUT = Path("public/data/states/as/electors.csv")
END_MARKER = "State Total"

FULL_ROW_RE = re.compile(
    r"^(\d+)\s+([A-Za-z][A-Za-z .()'\-/]+?)\s+(\d+)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$"
)
AC_ROW_RE = re.compile(r"^(\d+)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$")
DISTRICT_PREFIX_AC_ROW_RE = re.compile(
    r"^([A-Za-z][A-Za-z .()'\-/]+?)\s+(\d+)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$"
)
TOTAL_ROW_RE = re.compile(r"^\d+\s+\d+\s+\d+\s+\d+\s+\d+$")
TRAILING_NUMBERS_RE = re.compile(r"^(.*?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$")


@dataclass(frozen=True)
class ElectorRow:
    district_no: int
    district_name: str
    ac_no: int
    ac_name: str
    polling_stations: int
    male: int
    female: int
    third_gender: int
    total: int


def fetch_pdf_bytes(url: str, timeout: int = 60) -> bytes:
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
        return response.read()


def extract_pdf_text(pdf_path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise RuntimeError("pdftotext is required but not found in PATH")

    result = subprocess.run(
        [pdftotext, "-raw", str(pdf_path), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.replace("\xa0", " ")).strip()


def parse_rows_from_text(text: str) -> list[ElectorRow]:
    lines = [normalize_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    rows: list[ElectorRow] = []
    current_district_no: int | None = None
    current_district_name: str | None = None
    pending_ac_no: int | None = None
    pending_ac_name_parts: list[str] = []

    for line in lines:
        if END_MARKER in line:
            break
        if line.startswith("Page "):
            continue
        if line in {"No.", "Name", "MEN WOMEN", "THIRD", "GENDER", "TOTAL"}:
            continue
        if line.startswith("District Name") or line.startswith("Sl."):
            continue
        if line.startswith("General Electors") or line.startswith("Assembly Constituency"):
            continue
        if line.startswith("Final Publication date"):
            continue
        if line.startswith("District Total") or line.startswith("Dist. Total") or line.endswith("Total"):
            continue
        if line == "x":
            continue

        if TOTAL_ROW_RE.match(line):
            pending_ac_no = None
            pending_ac_name_parts = []
            continue

        full_match = FULL_ROW_RE.match(line)
        if full_match:
            current_district_no = int(full_match.group(1))
            current_district_name = full_match.group(2).strip()
            rows.append(
                ElectorRow(
                    district_no=current_district_no,
                    district_name=current_district_name,
                    ac_no=int(full_match.group(3)),
                    ac_name=full_match.group(4).strip(),
                    polling_stations=int(full_match.group(5)),
                    male=int(full_match.group(6)),
                    female=int(full_match.group(7)),
                    third_gender=int(full_match.group(8)),
                    total=int(full_match.group(9)),
                )
            )
            pending_ac_no = None
            pending_ac_name_parts = []
            continue

        prefix_match = DISTRICT_PREFIX_AC_ROW_RE.match(line)
        if prefix_match and current_district_no is not None and current_district_name is not None:
            prefix = prefix_match.group(1).strip()
            if not current_district_name.endswith(prefix):
                current_district_name = f"{current_district_name} {prefix}".strip()
            rows.append(
                ElectorRow(
                    district_no=current_district_no,
                    district_name=current_district_name,
                    ac_no=int(prefix_match.group(2)),
                    ac_name=prefix_match.group(3).strip(),
                    polling_stations=int(prefix_match.group(4)),
                    male=int(prefix_match.group(5)),
                    female=int(prefix_match.group(6)),
                    third_gender=int(prefix_match.group(7)),
                    total=int(prefix_match.group(8)),
                )
            )
            pending_ac_no = None
            pending_ac_name_parts = []
            continue

        ac_match = AC_ROW_RE.match(line)
        if ac_match and current_district_no is not None and current_district_name is not None:
            rows.append(
                ElectorRow(
                    district_no=current_district_no,
                    district_name=current_district_name,
                    ac_no=int(ac_match.group(1)),
                    ac_name=ac_match.group(2).strip(),
                    polling_stations=int(ac_match.group(3)),
                    male=int(ac_match.group(4)),
                    female=int(ac_match.group(5)),
                    third_gender=int(ac_match.group(6)),
                    total=int(ac_match.group(7)),
                )
            )
            pending_ac_no = None
            pending_ac_name_parts = []
            continue

        if line.isdigit() and pending_ac_no is None:
            pending_ac_no = int(line)
            pending_ac_name_parts = []
            continue

        trailing_match = TRAILING_NUMBERS_RE.match(line)
        if trailing_match and pending_ac_no is not None and current_district_no is not None and current_district_name is not None:
            name_suffix = trailing_match.group(1).strip()
            full_name_parts = [part for part in [*pending_ac_name_parts, name_suffix] if part]
            if not full_name_parts:
                raise ValueError(f"Could not reconstruct split AC name for line: {line}")
            rows.append(
                ElectorRow(
                    district_no=current_district_no,
                    district_name=current_district_name,
                    ac_no=pending_ac_no,
                    ac_name=" ".join(full_name_parts),
                    polling_stations=int(trailing_match.group(2)),
                    male=int(trailing_match.group(3)),
                    female=int(trailing_match.group(4)),
                    third_gender=int(trailing_match.group(5)),
                    total=int(trailing_match.group(6)),
                )
            )
            pending_ac_no = None
            pending_ac_name_parts = []
            continue

        if pending_ac_no is not None:
            pending_ac_name_parts.append(line)
            continue

    if not rows:
        raise ValueError("No AC rows parsed. PDF structure may have changed.")

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
                "polling_stations",
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
                    row.polling_stations,
                    row.male,
                    row.female,
                    row.third_gender,
                    row.total,
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Assam AC-wise electors and polling stations from PDF."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Source PDF URL")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output CSV path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    try:
        pdf_bytes = fetch_pdf_bytes(args.url)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(pdf_bytes)

        try:
            text = extract_pdf_text(tmp_path)
            rows = parse_rows_from_text(text)
        finally:
            tmp_path.unlink(missing_ok=True)

        write_csv(rows, output_path)
    except (HTTPError, URLError) as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Failed to extract PDF text: {exc.stderr.strip()}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1

    print(f"Saved {len(rows)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
