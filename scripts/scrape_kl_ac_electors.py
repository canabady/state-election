#!/usr/bin/env python3
"""Scrape Kerala AC-wise electors (GENERAL + OVERSEAS) from SIR 2026 PDF."""

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

DEFAULT_URL = "https://www.ceo.kerala.gov.in/uploads/sir-2026/final_electorate_sir_2026.pdf"
DEFAULT_OUTPUT = Path("public/data/states/kl/electors.csv")

TABLE_START_MARKER = "ASSEMBLY CONSTITUANCE WISE ELECTORS"
TABLE_END_MARKER = "DISTRICTWISE -OVERSEAS"
DISTRICT_TOTAL_MARKER = "DISTRICT TOTAL"

DISTRICT_AND_ROW_RE = re.compile(
    r"^(\d+)-([A-Z][A-Z\s-]+?)\s+(\d+)-(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$"
)
DISTRICT_PREFIX_AND_ROW_RE = re.compile(
    r"^(\d+)-\s+(\d+)-(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$"
)
ROW_ONLY_RE = re.compile(r"^(\d+)-(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$")
DISTRICT_ONLY_RE = re.compile(r"^(\d+)-([A-Z][A-Z\s-]+)$")
DISTRICT_PREFIX_RE = re.compile(r"^(\d+)-$")


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
        [pdftotext, "-layout", str(pdf_path), "-"],
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

    start_idx = next((i for i, line in enumerate(lines) if TABLE_START_MARKER in line), None)
    if start_idx is None:
        raise ValueError("Could not find AC-wise table start marker")

    end_idx = next((i for i, line in enumerate(lines[start_idx + 1 :], start=start_idx + 1) if TABLE_END_MARKER in line), None)
    if end_idx is None:
        raise ValueError("Could not find AC-wise table end marker")

    segment = lines[start_idx + 1 : end_idx]
    rows: list[ElectorRow] = []

    section_rows: list[tuple[int, str, int, int, int, int]] = []
    section_district_no: int | None = None
    section_district_name: str | None = None
    pending_district_no: int | None = None

    def finalize_section() -> None:
        nonlocal section_rows, section_district_no, section_district_name
        if not section_rows:
            return
        if section_district_no is None or section_district_name is None:
            raise ValueError("District metadata missing for AC section")
        for ac_no, ac_name, male, female, third_gender, total in section_rows:
            rows.append(
                ElectorRow(
                    district_no=section_district_no,
                    district_name=section_district_name,
                    ac_no=ac_no,
                    ac_name=ac_name,
                    male=male,
                    female=female,
                    third_gender=third_gender,
                    total=total,
                )
            )
        section_rows = []
        section_district_no = None
        section_district_name = None

    for line in segment:
        upper = line.upper()

        if "DISTRICT NAME" in upper and "LAC NAME" in upper:
            continue
        if "MALE ELECTORS" in upper and "FEMALE ELECTORS" in upper:
            continue
        if DISTRICT_TOTAL_MARKER in upper:
            finalize_section()
            continue

        pending_match = DISTRICT_PREFIX_RE.match(line)
        if pending_match:
            pending_district_no = int(pending_match.group(1))
            continue

        district_only_match = DISTRICT_ONLY_RE.match(line)
        if district_only_match:
            section_district_no = int(district_only_match.group(1))
            section_district_name = district_only_match.group(2).strip()
            pending_district_no = None
            continue

        district_and_row_match = DISTRICT_AND_ROW_RE.match(line)
        if district_and_row_match:
            section_district_no = int(district_and_row_match.group(1))
            section_district_name = district_and_row_match.group(2).strip()
            pending_district_no = None
            section_rows.append(
                (
                    int(district_and_row_match.group(3)),
                    district_and_row_match.group(4).strip(),
                    int(district_and_row_match.group(5)),
                    int(district_and_row_match.group(6)),
                    int(district_and_row_match.group(7)),
                    int(district_and_row_match.group(8)),
                )
            )
            continue

        district_prefix_and_row_match = DISTRICT_PREFIX_AND_ROW_RE.match(line)
        if district_prefix_and_row_match:
            pending_district_no = int(district_prefix_and_row_match.group(1))
            section_rows.append(
                (
                    int(district_prefix_and_row_match.group(2)),
                    district_prefix_and_row_match.group(3).strip(),
                    int(district_prefix_and_row_match.group(4)),
                    int(district_prefix_and_row_match.group(5)),
                    int(district_prefix_and_row_match.group(6)),
                    int(district_prefix_and_row_match.group(7)),
                )
            )
            continue

        if pending_district_no is not None:
            row_start = re.search(r"\b\d+-", line)
            if row_start:
                district_name = line[: row_start.start()].strip()
                remainder = line[row_start.start() :].strip()
                row_match = ROW_ONLY_RE.match(remainder)
                if district_name and row_match:
                    section_district_no = pending_district_no
                    section_district_name = district_name
                    pending_district_no = None
                    section_rows.append(
                        (
                            int(row_match.group(1)),
                            row_match.group(2).strip(),
                            int(row_match.group(3)),
                            int(row_match.group(4)),
                            int(row_match.group(5)),
                            int(row_match.group(6)),
                        )
                    )
                    continue

        row_only_match = ROW_ONLY_RE.match(line)
        if row_only_match:
            section_rows.append(
                (
                int(row_only_match.group(1)),
                row_only_match.group(2).strip(),
                int(row_only_match.group(3)),
                int(row_only_match.group(4)),
                int(row_only_match.group(5)),
                int(row_only_match.group(6)),
                )
            )
            continue

    finalize_section()

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
        description="Scrape Kerala AC-wise electors (GENERAL + OVERSEAS) and save as CSV."
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
