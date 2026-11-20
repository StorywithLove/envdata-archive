#!/usr/bin/env python3
"""Validate and copy a complete monthly Himawari daily-CSV archive."""
from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import math
import re
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {
    "station_id", "time_utc", "ghi_wm2", "temporal_resolution_seconds",
    "model_requested", "quality_flag",
}
ALLOWED_QUALITY_FLAGS = {
    "valid", "provider_returned_null", "provider_timestamp_missing",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_timestamps(day: date) -> list[str]:
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    return [
        (start + timedelta(minutes=10 * index)).isoformat().replace("+00:00", "Z")
        for index in range(1, 145)
    ]


def validate_daily_file(
    csv_path: Path, status_path: Path, day: date, cities: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_ids = {city["id"] for city in cities}
    rows_by_station: dict[str, list[dict[str, str]]] = defaultdict(list)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(f"{csv_path.name}: missing required CSV columns")
        for row in reader:
            station_id = row["station_id"]
            if station_id not in expected_ids:
                raise ValueError(f"{csv_path.name}: unexpected station_id {station_id!r}")
            rows_by_station[station_id].append(row)

    if set(rows_by_station) != expected_ids:
        missing = sorted(expected_ids - set(rows_by_station))
        raise ValueError(f"{csv_path.name}: missing stations {missing}")

    expected_times = expected_timestamps(day)
    quality_counts: Counter[str] = Counter()
    valid_records = 0
    for station_id in sorted(expected_ids):
        rows = rows_by_station[station_id]
        times = [row["time_utc"] for row in rows]
        if len(rows) != 144 or len(set(times)) != 144 or set(times) != set(expected_times):
            raise ValueError(
                f"{csv_path.name}: {station_id} must have exactly 144 unique "
                "interval-end timestamps from 00:10 to next-day 00:00 UTC"
            )
        for row in rows:
            if int(row["temporal_resolution_seconds"]) != 600:
                raise ValueError(f"{csv_path.name}: {station_id} has non-600s cadence")
            if row["model_requested"] != "jma_jaxa_himawari":
                raise ValueError(f"{csv_path.name}: unexpected model for {station_id}")
            flag = row["quality_flag"]
            if flag not in ALLOWED_QUALITY_FLAGS:
                raise ValueError(f"{csv_path.name}: unknown quality flag {flag!r}")
            quality_counts[flag] += 1
            if row["ghi_wm2"] != "":
                value = float(row["ghi_wm2"])
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"{csv_path.name}: invalid radiation value")
                if flag != "valid":
                    raise ValueError(f"{csv_path.name}: non-missing value has quality flag {flag!r}")
                valid_records += 1
            elif flag == "valid":
                raise ValueError(f"{csv_path.name}: blank value marked valid")

    status = json.loads(status_path.read_text(encoding="utf-8"))
    total_rows = len(expected_ids) * 144
    if status.get("records") != total_rows:
        raise ValueError(f"{status_path.name}: status records does not match {total_rows}")
    if status.get("locations_requested") != len(expected_ids):
        raise ValueError(f"{status_path.name}: unexpected locations_requested")
    if status.get("locations_succeeded") != len(expected_ids):
        raise ValueError(f"{status_path.name}: not all locations succeeded")
    if status.get("locations_failed") or status.get("failures"):
        raise ValueError(f"{status_path.name}: extraction reports failed locations")
    if status.get("valid_records") != valid_records:
        raise ValueError(f"{status_path.name}: valid_records does not match CSV")

    summaries = {
        item.get("station_id"): item
        for item in status.get("location_summaries", [])
    }
    if set(summaries) != expected_ids:
        raise ValueError(f"{status_path.name}: location_summaries do not match configured cities")
    for station_id in expected_ids:
        if summaries[station_id].get("records") != 144:
            raise ValueError(f"{status_path.name}: {station_id} summary does not report 144 records")

    return {
        "date_utc": day.isoformat(),
        "records": total_rows,
        "stations": len(expected_ids),
        "intervals_per_station": 144,
        "valid_records": valid_records,
        "missing_records": total_rows - valid_records,
        "quality_flags": dict(sorted(quality_counts.items())),
        "csv": {
            "filename": csv_path.name,
            "bytes": csv_path.stat().st_size,
            "sha256": sha256_file(csv_path),
        },
        "status": {
            "filename": status_path.name,
            "bytes": status_path.stat().st_size,
            "sha256": sha256_file(status_path),
        },
    }


def copy_and_verify(source: Path, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    source_hash = sha256_file(source)
    destination_hash = sha256_file(destination)
    if source_hash != destination_hash:
        raise ValueError(f"SHA-256 mismatch after copying {source.name}")
    return {
        "filename": source.name,
        "bytes": destination.stat().st_size,
        "sha256": destination_hash,
    }


def archive_month(
    month: str, source_dir: Path, archive_root: Path, cities_path: Path,
) -> Path:
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("month must use YYYY-MM format")
    year, month_number = map(int, month.split("-"))
    if not 1 <= month_number <= 12:
        raise ValueError("month must use YYYY-MM format")
    cities = json.loads(cities_path.read_text(encoding="utf-8"))
    if len(cities) != 31 or len({city["id"] for city in cities}) != 31:
        raise ValueError("cities.json must contain 31 unique fixed stations")

    days_in_month = calendar.monthrange(year, month_number)[1]
    manifest_days = []
    for day_number in range(1, days_in_month + 1):
        day = date(year, month_number, day_number)
        compact = day.strftime("%Y%m%d")
        csv_path = source_dir / f"radiation_{compact}.csv"
        status_path = source_dir / f"radiation_{compact}.status.json"
        if not csv_path.is_file() or not status_path.is_file():
            raise FileNotFoundError(f"Missing CSV or quality sidecar for {day.isoformat()}")

        day_manifest = validate_daily_file(csv_path, status_path, day, cities)
        target_dir = archive_root / day.isoformat()
        copied_csv = copy_and_verify(csv_path, target_dir / csv_path.name)
        copied_status = copy_and_verify(status_path, target_dir / status_path.name)
        if copied_csv["sha256"] != day_manifest["csv"]["sha256"]:
            raise ValueError(f"CSV verification failed for {day.isoformat()}")
        if copied_status["sha256"] != day_manifest["status"]["sha256"]:
            raise ValueError(f"Status verification failed for {day.isoformat()}")
        day_manifest["archive"] = {
            "csv_sha256": copied_csv["sha256"],
            "status_sha256": copied_status["sha256"],
        }
        manifest_days.append(day_manifest)

    manifest = {
        "schema_version": 1,
        "source_repository": "StorywithLove/envdata-sat",
        "archive_repository": "StorywithLove/envdata-archive",
        "month": month,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "station_count": len(cities),
        "intervals_per_station_per_day": 144,
        "expected_days": days_in_month,
        "archived_days": len(manifest_days),
        "total_records": sum(item["records"] for item in manifest_days),
        "total_valid_records": sum(item["valid_records"] for item in manifest_days),
        "days": manifest_days,
    }
    manifest_path = archive_root / "_manifests" / f"{month}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = manifest_path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(manifest_path)
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", required=True, help="Month to archive, YYYY-MM")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--cities-json", type=Path, required=True)
    args = parser.parse_args()
    manifest = archive_month(args.month, args.source_dir, args.archive_root, args.cities_json)
    print(f"Verified and archived {args.month}; manifest: {manifest}")


if __name__ == "__main__":
    main()
