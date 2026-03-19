#!/usr/bin/env python3
"""Scrape West Bengal AC-wise draft electors and polling stations from SIR 2026 PDF."""

from __future__ import annotations

import argparse
import csv
import os
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

DEFAULT_URL = "https://ceowestbengal.wb.gov.in/Downloads/SIR2026/AC%20wise%20Draft%20Elector%20SIR%202026.pdf"
DEFAULT_OUTPUT = Path("public/data/states/wb/electors.csv")
START_MARKER = "AC wise Status of Polling Stations and Electors"
TRAILING_NUMBERS_RE = re.compile(r"^(.*?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$")
TOTAL_LINE_RE = re.compile(r"^Total\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class ElectorRow:
    district_name: str
    ac_no: int
    ac_name: str
    polling_stations: int
    male: int
    female: int
    third_gender: int
    total: int


def fetch_pdf_bytes_urllib(url: str, timeout: int = 60) -> bytes:
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


def fetch_pdf_bytes_curl(url: str) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    openssl_cfg = tmp_path.with_suffix(".cnf")
    openssl_cfg.write_text(
        """openssl_conf = default_conf

[default_conf]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
Options = UnsafeLegacyRenegotiation
""",
        encoding="utf-8",
    )

    try:
        env = os.environ.copy()
        env["OPENSSL_CONF"] = str(openssl_cfg)
        subprocess.run(
            ["curl", "-L", url, "-o", str(tmp_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)
        openssl_cfg.unlink(missing_ok=True)


def fetch_pdf_bytes(url: str) -> bytes:
    try:
        return fetch_pdf_bytes_urllib(url)
    except (HTTPError, URLError):
        return fetch_pdf_bytes_curl(url)


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

    start_idx = next((i for i, line in enumerate(lines) if START_MARKER in line), None)
    if start_idx is None:
        raise ValueError("Could not find West Bengal AC-wise table start marker")

    rows: list[ElectorRow] = []

    for line in lines[start_idx + 1 :]:
        if TOTAL_LINE_RE.match(line):
            break
        if line.startswith("Name of District"):
            continue
        if line.startswith("Assembly Constituency"):
            continue
        if line.startswith("No. of"):
            continue
        if line.startswith("Electors as per"):
            continue
        if line.startswith("Poll\n"):
            continue
        if line.startswith("No ") or line.startswith("No."):
            continue
        if line.startswith("Station"):
            continue
        if line in {"Male", "Female", "Third", "Gender", "Total"}:
            continue

        trailing = TRAILING_NUMBERS_RE.match(line)
        if not trailing:
            continue
        left = trailing.group(1).strip()
        polling_stations = int(trailing.group(2))
        male = int(trailing.group(3))
        female = int(trailing.group(4))
        third_gender = int(trailing.group(5))
        total = int(trailing.group(6))

        number_tokens = list(re.finditer(r"\b\d+\b", left))
        if not number_tokens:
            continue
        ac_token = number_tokens[-1]
        ac_no = int(ac_token.group(0))
        district_name = left[: ac_token.start()].strip()
        ac_name = left[ac_token.end() :].strip()
        if not district_name or not ac_name:
            continue

        rows.append(
            ElectorRow(
                district_name=district_name,
                ac_no=ac_no,
                ac_name=ac_name,
                polling_stations=polling_stations,
                male=male,
                female=female,
                third_gender=third_gender,
                total=total,
            )
        )

    if not rows:
        raise ValueError("No AC rows parsed. PDF structure may have changed.")

    return rows


def write_csv(rows: Iterable[ElectorRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
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
        description="Scrape West Bengal AC-wise draft electors and polling stations from SIR 2026 PDF."
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
    except subprocess.CalledProcessError as exc:
        print(f"Command failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1

    print(f"Saved {len(rows)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
