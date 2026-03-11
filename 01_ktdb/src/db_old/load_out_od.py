"""
수도권 목적OD (.OUT 파일) → PostgreSQL 적재 스크립트

- psycopg v3 COPY 프로토콜 사용 (bulk loading)
- CP949 인코딩, 공백 구분자, 헤더 없음
- 파일당 약 170만 행 처리
- 연도+지역 중복 체크 후 스킵
"""

import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

import psycopg

# ---------------------------------------------------------------------------
# Source files
# ---------------------------------------------------------------------------
OD_DIR = (
    PROJECT_ROOT
    / "data/extracted"
    / "2024-OD-PSN-OBJ-01 수도권 목적OD(2023-2050)"
    / "2024-OD-PSN-OBJ-01 수도권 목적OD(2023-2050)"
    / "4. OD"
)

SOURCE_FILES = [
    "ODTRIP23_F.OUT",
    "ODTRIP25_F.OUT",
    "ODTRIP30_F.OUT",
    "ODTRIP35_F.OUT",
    "ODTRIP40_F.OUT",
    "ODTRIP45_F.OUT",
    "ODTRIP50_F.OUT",
]

REGION_ID = "01"  # 수도권
PROGRESS_INTERVAL = 200_000


def extract_year(filename: str) -> int:
    """ODTRIP23_F.OUT → 2023, ODTRIP50_F.OUT → 2050"""
    m = re.search(r"ODTRIP(\d{2})_", filename, re.IGNORECASE)
    if not m:
        raise ValueError(f"Cannot extract year from filename: {filename}")
    suffix = int(m.group(1))
    # 23 → 2023, 25 → 2025, ..., 50 → 2050
    year = 2000 + suffix
    return year


def get_connection() -> psycopg.Connection:
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    dbname = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]

    conninfo = (
        f"host={host} port={port} dbname={dbname} "
        f"user={user} password={password} sslmode=require"
    )
    return psycopg.connect(conninfo, autocommit=True, prepare_threshold=None)


def check_existing(conn: psycopg.Connection, year: int, region_id: str) -> int:
    """Return row count for year+region. 0 means not yet loaded."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM ktdb_od_purpose_subzone "
            "WHERE year = %s AND region_id = %s",
            (year, region_id),
        )
        row = cur.fetchone()
        return row[0] if row else 0


def load_file(conn: psycopg.Connection, filepath: Path, year: int) -> int:
    """
    Stream .OUT file into PostgreSQL via COPY protocol.
    Returns number of rows loaded.
    """
    filename_only = filepath.name
    row_count = 0
    t0 = time.perf_counter()

    copy_sql = (
        "COPY ktdb_od_purpose_subzone "
        "(year, region_id, origin_zone, destination_zone, "
        " commute, school, business, return_home, etc, total, source_file) "
        "FROM STDIN"
    )

    with conn.cursor() as cur:
        with cur.copy(copy_sql) as copy:
            with open(filepath, "r", encoding="cp949") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line:
                        continue

                    parts = line.split()
                    if len(parts) != 9:
                        # Skip malformed lines
                        continue

                    # Parts: O_seq O_zone_code D_seq D_zone_code 출근 등교 업무 귀가 합계
                    o_zone = parts[1]   # 7-digit origin zone code
                    d_zone = parts[3]   # 7-digit destination zone code
                    commute = float(parts[4])
                    school = float(parts[5])
                    business = float(parts[6])
                    return_home = float(parts[7])
                    total = float(parts[8])
                    etc = 0.0           # 수도권 .OUT has no 기타 column

                    copy.write_row((
                        year,
                        REGION_ID,
                        o_zone,
                        d_zone,
                        commute,
                        school,
                        business,
                        return_home,
                        etc,
                        total,
                        filename_only,
                    ))

                    row_count += 1
                    if row_count % PROGRESS_INTERVAL == 0:
                        elapsed = time.perf_counter() - t0
                        rate = row_count / elapsed if elapsed > 0 else 0
                        print(
                            f"  [{filename_only}] {row_count:,} rows "
                            f"({elapsed:.1f}s, {rate:,.0f} rows/s)"
                        )

    elapsed = time.perf_counter() - t0
    rate = row_count / elapsed if elapsed > 0 else 0
    print(
        f"  [{filename_only}] DONE: {row_count:,} rows in {elapsed:.2f}s "
        f"({rate:,.0f} rows/s)"
    )
    return row_count


def main() -> None:
    print(f"Project root: {PROJECT_ROOT}")
    print(f"OD directory: {OD_DIR}")
    print()

    print("Connecting to database...")
    try:
        conn = get_connection()
    except Exception as e:
        print(f"ERROR: DB connection failed: {e}", file=sys.stderr)
        sys.exit(1)
    print("Connected.\n")

    total_rows = 0
    total_t0 = time.perf_counter()

    for fname in SOURCE_FILES:
        filepath = OD_DIR / fname
        if not filepath.exists():
            print(f"WARN: File not found, skipping: {filepath}")
            continue

        year = extract_year(fname)
        print(f"--- {fname} (year={year}) ---")

        # Duplicate check
        existing = check_existing(conn, year, REGION_ID)
        if existing > 0:
            print(f"  SKIP: already have {existing:,} rows for year={year}, region_id='{REGION_ID}'\n")
            continue

        try:
            rows = load_file(conn, filepath, year)
            total_rows += rows
        except Exception as e:
            print(f"  ERROR loading {fname}: {e}", file=sys.stderr)
            conn.close()
            sys.exit(1)

        print()

    conn.close()

    total_elapsed = time.perf_counter() - total_t0
    print("=" * 60)
    print(f"All files processed.")
    print(f"Total rows loaded : {total_rows:,}")
    print(f"Total time        : {total_elapsed:.2f}s")
    if total_elapsed > 0 and total_rows > 0:
        print(f"Overall rate      : {total_rows / total_elapsed:,.0f} rows/s")
    print("=" * 60)


if __name__ == "__main__":
    main()
