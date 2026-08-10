import json
import sys
import unittest
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import call, patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "python"))

import common.throttle as throttle_module


class ThrottleFileReadWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.throttle_path = Path(self.temporary_directory.name) / "state" / "throttle.json"

    def test_read_creates_missing_file_with_current_time(self) -> None:
        with (
            patch.object(throttle_module.time, "time", return_value=123.5),
            self.assertWarnsRegex(RuntimeWarning, "Throttle file not found"),
        ):
            result = throttle_module.throttle_file_rw(self.throttle_path)

        self.assertEqual(result, 123.5)
        self.assertEqual(
            json.loads(self.throttle_path.read_text(encoding="utf-8")),
            {"next_allowed_at": 123.5},
        )

    def test_write_replaces_existing_value_and_returns_it(self) -> None:
        self.throttle_path.parent.mkdir(parents=True)
        self.throttle_path.write_text('{"next_allowed_at": 10}', encoding="utf-8")

        result = throttle_module.throttle_file_rw(
            self.throttle_path, mode="w", next_allowed_at=42.25
        )

        self.assertEqual(result, 42.25)
        self.assertEqual(
            json.loads(self.throttle_path.read_text(encoding="utf-8")),
            {"next_allowed_at": 42.25},
        )

    def test_invalid_file_is_repaired_with_current_time(self) -> None:
        self.throttle_path.parent.mkdir(parents=True)
        self.throttle_path.write_text("not JSON", encoding="utf-8")

        with (
            patch.object(throttle_module.time, "time", return_value=99.0),
            self.assertWarnsRegex(RuntimeWarning, "Throttle file missing or invalid"),
        ):
            result = throttle_module.throttle_file_rw(self.throttle_path)

        self.assertEqual(result, 99.0)
        self.assertEqual(
            json.loads(self.throttle_path.read_text(encoding="utf-8")),
            {"next_allowed_at": 99.0},
        )

    def test_read_converts_string_timestamp_to_float(self) -> None:
        self.throttle_path.parent.mkdir(parents=True)
        self.throttle_path.write_text(
            '{"next_allowed_at": "17.5"}', encoding="utf-8"
        )

        self.assertEqual(throttle_module.throttle_file_rw(self.throttle_path), 17.5)

    def test_rejects_invalid_arguments(self) -> None:
        with self.subTest("invalid mode"):
            with self.assertRaisesRegex(ValueError, "Invalid mode"):
                throttle_module.throttle_file_rw(self.throttle_path, mode="append")

        with self.subTest("missing write value"):
            with self.assertRaisesRegex(ValueError, "must be provided"):
                throttle_module.throttle_file_rw(self.throttle_path, mode="w")

        with self.subTest("negative value"):
            with self.assertRaisesRegex(ValueError, "positive number"):
                throttle_module.throttle_file_rw(
                    self.throttle_path, mode="w", next_allowed_at=-1
                )


class TimingLogicTests(unittest.TestCase):
    @patch.object(throttle_module.time, "time", return_value=100.0)
    def test_future_timestamp_returns_wait_and_advances_from_timestamp(
        self, _mock_time
    ) -> None:
        next_allowed_at, waiting_time = throttle_module.timing_logic(110.0, 30)

        self.assertEqual(next_allowed_at, 112.0)
        self.assertEqual(waiting_time, 10.0)

    @patch.object(throttle_module.time, "time", return_value=100.0)
    def test_expired_timestamp_runs_immediately_and_advances_from_now(
        self, _mock_time
    ) -> None:
        next_allowed_at, waiting_time = throttle_module.timing_logic(90.0, 20)

        self.assertEqual(next_allowed_at, 103.0)
        self.assertEqual(waiting_time, 0.0)

    def test_rejects_non_positive_request_rate(self) -> None:
        for rate in (0, -1):
            with self.subTest(rate=rate):
                with self.assertRaisesRegex(ValueError, "greater than 0"):
                    throttle_module.timing_logic(10.0, rate)

    def test_rejects_negative_next_allowed_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            throttle_module.timing_logic(-0.1, 10)


class ThrottleTests(unittest.TestCase):
    @patch.object(throttle_module, "throttle_file_rw")
    @patch.object(throttle_module, "timing_logic", return_value=(205.0, 5.0))
    def test_reads_calculates_and_persists_next_timestamp(
        self, mock_timing_logic, mock_file_rw
    ) -> None:
        throttle_path = Path("throttle.json")
        mock_file_rw.side_effect = [200.0, 205.0]

        result = throttle_module.throttle(throttle_path, requests_per_minute=12)

        self.assertEqual(result, 5.0)
        mock_timing_logic.assert_called_once_with(200.0, 12)
        self.assertEqual(
            mock_file_rw.call_args_list,
            [call(throttle_path, "r"), call(throttle_path, "w", 205.0)],
        )


if __name__ == "__main__":
    unittest.main()
