"""
KTDB 데이터베이스 스키마 초기화 스크립트
- psycopg v3 직접 사용 (SQLAlchemy 미사용)
- Azure PostgreSQL: sslmode='require'
- 모든 테이블에 ktdb_ 접두어 사용
"""

import os
import sys
from pathlib import Path

# Load .env from project root (01_ktdb/.env)
from dotenv import load_dotenv

# Resolve project root: src/db/init_schema.py -> src/db -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)

import psycopg


def get_connection():
    """Create psycopg v3 connection with Azure PostgreSQL settings."""
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    dbname = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]

    conninfo = (
        f"host={host} port={port} dbname={dbname} "
        f"user={user} password={password} sslmode=require"
    )
    return psycopg.connect(conninfo, autocommit=True)


# ---------------------------------------------------------------------------
# DDL statements in dependency order
# ---------------------------------------------------------------------------

DDL_STATEMENTS = [
    # 1. ktdb_zones_17
    (
        "ktdb_zones_17",
        """
CREATE TABLE IF NOT EXISTS ktdb_zones_17 (
    id SERIAL PRIMARY KEY,
    zone_code_17 INTEGER UNIQUE NOT NULL,
    sido_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
""",
    ),
    # 2. ktdb_zones_250
    (
        "ktdb_zones_250",
        """
CREATE TABLE IF NOT EXISTS ktdb_zones_250 (
    id SERIAL PRIMARY KEY,
    zone_code_250 INTEGER UNIQUE NOT NULL,
    zone_name VARCHAR(100),
    sido_code VARCHAR(5),
    sido_name VARCHAR(50),
    zone_161 INTEGER,
    zone_17 INTEGER REFERENCES ktdb_zones_17(zone_code_17),
    created_at TIMESTAMP DEFAULT NOW()
);
""",
    ),
    # 3. ktdb_zones_subzone + indexes
    (
        "ktdb_zones_subzone",
        """
CREATE TABLE IF NOT EXISTS ktdb_zones_subzone (
    id SERIAL PRIMARY KEY,
    zone_code VARCHAR(10) UNIQUE NOT NULL,
    zone_seq INTEGER,
    dong_name VARCHAR(100),
    sigungu_code VARCHAR(10),
    sigungu_name VARCHAR(100),
    sido_code VARCHAR(5),
    sido_name VARCHAR(50),
    admin_code VARCHAR(20),
    region_id VARCHAR(5) NOT NULL,
    zone_250 INTEGER REFERENCES ktdb_zones_250(zone_code_250),
    centroid_lat DOUBLE PRECISION,
    centroid_lon DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);
""",
    ),
    (
        "idx_ktdb_zones_subzone_region",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_zones_subzone_region ON ktdb_zones_subzone(region_id);",
    ),
    (
        "idx_ktdb_zones_subzone_sigungu",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_zones_subzone_sigungu ON ktdb_zones_subzone(sigungu_code);",
    ),
    # 4. ktdb_socioeconomic + indexes
    (
        "ktdb_socioeconomic",
        """
CREATE TABLE IF NOT EXISTS ktdb_socioeconomic (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    zone_level VARCHAR(10) NOT NULL,
    zone_code VARCHAR(10) NOT NULL,
    indicator_type VARCHAR(20) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, zone_code, indicator_type)
);
""",
    ),
    (
        "idx_ktdb_socio_year_type",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_socio_year_type ON ktdb_socioeconomic(year, indicator_type);",
    ),
    (
        "idx_ktdb_socio_zone",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_socio_zone ON ktdb_socioeconomic(zone_code);",
    ),
    # 5. ktdb_od_purpose_subzone (partitioned) + partitions + indexes
    (
        "ktdb_od_purpose_subzone",
        """
CREATE TABLE IF NOT EXISTS ktdb_od_purpose_subzone (
    id BIGSERIAL,
    year INTEGER NOT NULL,
    region_id VARCHAR(5) NOT NULL,
    origin_zone VARCHAR(10) NOT NULL,
    destination_zone VARCHAR(10) NOT NULL,
    commute DOUBLE PRECISION DEFAULT 0,
    school DOUBLE PRECISION DEFAULT 0,
    business DOUBLE PRECISION DEFAULT 0,
    return_home DOUBLE PRECISION DEFAULT 0,
    etc DOUBLE PRECISION DEFAULT 0,
    total DOUBLE PRECISION DEFAULT 0,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (year);
""",
    ),
    (
        "ktdb_od_purpose_subzone_2023",
        "CREATE TABLE IF NOT EXISTS ktdb_od_purpose_subzone_2023 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2023) TO (2024);",
    ),
    (
        "ktdb_od_purpose_subzone_2025",
        "CREATE TABLE IF NOT EXISTS ktdb_od_purpose_subzone_2025 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2025) TO (2026);",
    ),
    (
        "ktdb_od_purpose_subzone_2030",
        "CREATE TABLE IF NOT EXISTS ktdb_od_purpose_subzone_2030 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2030) TO (2031);",
    ),
    (
        "ktdb_od_purpose_subzone_2035",
        "CREATE TABLE IF NOT EXISTS ktdb_od_purpose_subzone_2035 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2035) TO (2036);",
    ),
    (
        "ktdb_od_purpose_subzone_2040",
        "CREATE TABLE IF NOT EXISTS ktdb_od_purpose_subzone_2040 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2040) TO (2041);",
    ),
    (
        "ktdb_od_purpose_subzone_2045",
        "CREATE TABLE IF NOT EXISTS ktdb_od_purpose_subzone_2045 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2045) TO (2046);",
    ),
    (
        "ktdb_od_purpose_subzone_2050",
        "CREATE TABLE IF NOT EXISTS ktdb_od_purpose_subzone_2050 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2050) TO (2051);",
    ),
    (
        "idx_ktdb_od_purp_sub_lookup",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_od_purp_sub_lookup ON ktdb_od_purpose_subzone(year, origin_zone, destination_zone);",
    ),
    (
        "idx_ktdb_od_purp_sub_origin",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_od_purp_sub_origin ON ktdb_od_purpose_subzone(year, origin_zone);",
    ),
    (
        "idx_ktdb_od_purp_sub_region",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_od_purp_sub_region ON ktdb_od_purpose_subzone(year, region_id);",
    ),
    (
        "idx_ktdb_od_purp_sub_unique",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_ktdb_od_purp_sub_unique ON ktdb_od_purpose_subzone(year, region_id, origin_zone, destination_zone);",
    ),
    # 6. ktdb_od_purpose_250 + index
    (
        "ktdb_od_purpose_250",
        """
CREATE TABLE IF NOT EXISTS ktdb_od_purpose_250 (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    origin_sido VARCHAR(50),
    origin_sigungu VARCHAR(100),
    destination_sido VARCHAR(50),
    destination_sigungu VARCHAR(100),
    commute DOUBLE PRECISION DEFAULT 0,
    school DOUBLE PRECISION DEFAULT 0,
    business DOUBLE PRECISION DEFAULT 0,
    return_home DOUBLE PRECISION DEFAULT 0,
    etc DOUBLE PRECISION DEFAULT 0,
    total DOUBLE PRECISION DEFAULT 0,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, origin_sigungu, destination_sigungu)
);
""",
    ),
    (
        "idx_ktdb_od_purp_250_lookup",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_od_purp_250_lookup ON ktdb_od_purpose_250(year, origin_sigungu, destination_sigungu);",
    ),
    # 7. ktdb_od_mode_subzone (partitioned) + partitions + indexes
    (
        "ktdb_od_mode_subzone",
        """
CREATE TABLE IF NOT EXISTS ktdb_od_mode_subzone (
    id BIGSERIAL,
    year INTEGER NOT NULL,
    region_id VARCHAR(5) NOT NULL,
    origin_zone VARCHAR(10) NOT NULL,
    destination_zone VARCHAR(10) NOT NULL,
    mode_code VARCHAR(10) NOT NULL,
    volume DOUBLE PRECISION DEFAULT 0,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (year);
""",
    ),
    (
        "ktdb_od_mode_subzone_2023",
        "CREATE TABLE IF NOT EXISTS ktdb_od_mode_subzone_2023 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2023) TO (2024);",
    ),
    (
        "ktdb_od_mode_subzone_2025",
        "CREATE TABLE IF NOT EXISTS ktdb_od_mode_subzone_2025 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2025) TO (2026);",
    ),
    (
        "ktdb_od_mode_subzone_2030",
        "CREATE TABLE IF NOT EXISTS ktdb_od_mode_subzone_2030 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2030) TO (2031);",
    ),
    (
        "ktdb_od_mode_subzone_2035",
        "CREATE TABLE IF NOT EXISTS ktdb_od_mode_subzone_2035 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2035) TO (2036);",
    ),
    (
        "ktdb_od_mode_subzone_2040",
        "CREATE TABLE IF NOT EXISTS ktdb_od_mode_subzone_2040 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2040) TO (2041);",
    ),
    (
        "ktdb_od_mode_subzone_2045",
        "CREATE TABLE IF NOT EXISTS ktdb_od_mode_subzone_2045 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2045) TO (2046);",
    ),
    (
        "ktdb_od_mode_subzone_2050",
        "CREATE TABLE IF NOT EXISTS ktdb_od_mode_subzone_2050 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2050) TO (2051);",
    ),
    (
        "idx_ktdb_od_mode_sub_lookup",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_od_mode_sub_lookup ON ktdb_od_mode_subzone(year, origin_zone, destination_zone);",
    ),
    (
        "idx_ktdb_od_mode_sub_mode",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_od_mode_sub_mode ON ktdb_od_mode_subzone(year, mode_code);",
    ),
    (
        "idx_ktdb_od_mode_sub_unique",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_ktdb_od_mode_sub_unique ON ktdb_od_mode_subzone(year, region_id, origin_zone, destination_zone, mode_code);",
    ),
    # 8. ktdb_od_mode_250 + index
    (
        "ktdb_od_mode_250",
        """
CREATE TABLE IF NOT EXISTS ktdb_od_mode_250 (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    origin_sido VARCHAR(50),
    origin_sigungu VARCHAR(100),
    destination_sido VARCHAR(50),
    destination_sigungu VARCHAR(100),
    car DOUBLE PRECISION DEFAULT 0,
    bus DOUBLE PRECISION DEFAULT 0,
    subway DOUBLE PRECISION DEFAULT 0,
    rail DOUBLE PRECISION DEFAULT 0,
    ktx DOUBLE PRECISION DEFAULT 0,
    air DOUBLE PRECISION DEFAULT 0,
    ship DOUBLE PRECISION DEFAULT 0,
    total DOUBLE PRECISION DEFAULT 0,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, origin_sigungu, destination_sigungu)
);
""",
    ),
    (
        "idx_ktdb_od_mode_250_lookup",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_od_mode_250_lookup ON ktdb_od_mode_250(year, origin_sigungu, destination_sigungu);",
    ),
    # 9. ktdb_od_freight + index
    (
        "ktdb_od_freight",
        """
CREATE TABLE IF NOT EXISTS ktdb_od_freight (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    origin_zone_250 INTEGER NOT NULL,
    origin_zone_17 INTEGER,
    destination_zone_250 INTEGER NOT NULL,
    destination_zone_17 INTEGER,
    tonnage_small DOUBLE PRECISION DEFAULT 0,
    tonnage_medium DOUBLE PRECISION DEFAULT 0,
    tonnage_large DOUBLE PRECISION DEFAULT 0,
    tonnage_total DOUBLE PRECISION DEFAULT 0,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, origin_zone_250, destination_zone_250)
);
""",
    ),
    (
        "idx_ktdb_od_freight_lookup",
        "CREATE INDEX IF NOT EXISTS idx_ktdb_od_freight_lookup ON ktdb_od_freight(year, origin_zone_250, destination_zone_250);",
    ),
    # 10. ktdb_upload_history
    (
        "ktdb_upload_history",
        """
CREATE TABLE IF NOT EXISTS ktdb_upload_history (
    id SERIAL PRIMARY KEY,
    zip_filename VARCHAR(500),
    extracted_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    data_category VARCHAR(50) NOT NULL,
    region_id VARCHAR(5),
    year INTEGER,
    row_count INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    last_success_row INTEGER,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
""",
    ),
    # 11. ktdb_query_history
    (
        "ktdb_query_history",
        """
CREATE TABLE IF NOT EXISTS ktdb_query_history (
    id SERIAL PRIMARY KEY,
    user_query TEXT NOT NULL,
    generated_sql TEXT,
    result_summary TEXT,
    execution_time_ms INTEGER,
    confidence_score DOUBLE PRECISION,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
""",
    ),
]


def init_schema():
    """Initialize all KTDB tables in the public schema."""
    print(f"Loading .env from: {env_path}")
    if not env_path.exists():
        print(f"ERROR: .env file not found at {env_path}", file=sys.stderr)
        sys.exit(1)

    print("Connecting to database...")
    try:
        conn = get_connection()
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}", file=sys.stderr)
        sys.exit(1)

    print("Connected. Starting schema initialization...\n")

    success_count = 0
    error_count = 0

    try:
        with conn.cursor() as cur:
            for name, ddl in DDL_STATEMENTS:
                try:
                    cur.execute(ddl)
                    print(f"  OK  {name}")
                    success_count += 1
                except Exception as e:
                    print(f"  ERR {name}: {e}", file=sys.stderr)
                    error_count += 1
    finally:
        conn.close()

    print(f"\n--- Done ---")
    print(f"Success: {success_count}")
    if error_count:
        print(f"Errors:  {error_count}")
        sys.exit(1)
    else:
        print("All statements executed successfully.")


if __name__ == "__main__":
    init_schema()
