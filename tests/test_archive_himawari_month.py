import csv
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from scripts.archive_himawari_month import copy_and_verify, validate_daily_file


class ValidateDailyFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.day = date(2026, 10, 1)
        self.city = [{"id": "wuhan"}]
        self.csv_path = self.root / "radiation_20261001.csv"
        self.status_path = self.root / "radiation_20261001.status.json"
        start = datetime(2026, 10, 1, tzinfo=timezone.utc)
        self.rows = []
        for index in range(1, 145):
            timestamp = (start + timedelta(minutes=10 * index)).isoformat().replace("+00:00", "Z")
            self.rows.append({
                "station_id": "wuhan",
                "time_utc": timestamp,
                "ghi_wm2": "0" if index == 1 else ("" if index == 2 else "123.4"),
                "temporal_resolution_seconds": "600",
                "model_requested": "jma_jaxa_himawari",
                "quality_flag": "valid" if index != 2 else "provider_returned_null",
            })
        self._write_csv()
        self._write_status()

    def tearDown(self):
        self.temp.cleanup()

    def _write_csv(self):
        with self.csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(self.rows[0]))
            writer.writeheader()
            writer.writerows(self.rows)

    def _write_status(self):
        self.status_path.write_text(json.dumps({
            "records": 144,
            "locations_requested": 1,
            "locations_succeeded": 1,
            "locations_failed": [],
            "failures": [],
            "valid_records": 143,
            "location_summaries": [{"station_id": "wuhan", "records": 144}],
        }), encoding="utf-8")

    def test_valid_day_preserves_zero_and_missing_value(self):
        result = validate_daily_file(self.csv_path, self.status_path, self.day, self.city)
        self.assertEqual(result["records"], 144)
        self.assertEqual(result["valid_records"], 143)
        self.assertEqual(result["quality_flags"]["provider_returned_null"], 1)

    def test_missing_timestamp_is_rejected(self):
        self.rows.pop(10)
        self._write_csv()
        with self.assertRaisesRegex(ValueError, "exactly 144"):
            validate_daily_file(self.csv_path, self.status_path, self.day, self.city)

    def test_wrong_cadence_is_rejected(self):
        self.rows[0]["temporal_resolution_seconds"] = "3600"
        self._write_csv()
        with self.assertRaisesRegex(ValueError, "non-600s"):
            validate_daily_file(self.csv_path, self.status_path, self.day, self.city)

    def test_copy_is_hash_verified(self):
        destination = self.root / "archive" / self.csv_path.name
        result = copy_and_verify(self.csv_path, destination)
        self.assertTrue(destination.exists())
        self.assertEqual(result["sha256"], result["sha256"])
        self.assertEqual(destination.read_bytes(), self.csv_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
