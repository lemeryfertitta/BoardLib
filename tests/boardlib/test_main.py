import csv
import datetime
import os
import sys
import tempfile
import unittest
import unittest.mock

import boardlib.__main__


KILTER_ENTRY = {
    "climb_angle_uuid": "TESTCLIMB1-40",
    "climb_uuid": "TESTCLIMB1",
    "board": "kilter",
    "angle": 40,
    "climb_name": "test_climb_1",
    "date": datetime.datetime(2026, 4, 1, 18, 0),
    "logged_grade": None,
    "displayed_grade": "6A+/V3",
    "is_benchmark": None,
    "tries": 1,
    "is_mirror": None,
    "is_ascent": True,
    "comment": None,
    "is_repeat": False,
    "sessions_count": 1,
    "tries_total": 1,
}


class TestMain(unittest.TestCase):
    @unittest.mock.patch.dict(os.environ, {"KILTER_PASSWORD": "test_password"})
    @unittest.mock.patch(
        "boardlib.api.kilter.logbook_entries", return_value=[KILTER_ENTRY]
    )
    def test_logbook_kilter(self, mock_logbook_entries):
        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "logbook.csv")
            argv = [
                "boardlib",
                "logbook",
                "kilter",
                "-u",
                "test@example.com",
                "-o",
                output,
            ]
            with unittest.mock.patch.object(sys, "argv", argv):
                boardlib.__main__.main()

            with open(output, encoding="utf-8") as output_file:
                rows = list(csv.DictReader(output_file))

        mock_logbook_entries.assert_called_once_with(
            "kilter", "test@example.com", "test_password"
        )
        self.assertEqual(
            rows,
            [
                {
                    "board": "kilter",
                    "angle": "40",
                    "climb_name": "test_climb_1",
                    "date": "2026-04-01 18:00:00",
                    "logged_grade": "",
                    "displayed_grade": "6A+/V3",
                    "is_benchmark": "",
                    "tries": "1",
                    "is_mirror": "",
                    "sessions_count": "1",
                    "tries_total": "1",
                    "is_repeat": "False",
                    "is_ascent": "True",
                    "comment": "",
                }
            ],
        )

    @unittest.mock.patch(
        "boardlib.api.kilter.logbook_entries", return_value=[KILTER_ENTRY]
    )
    def test_logbook_entries_kilter(self, mock_logbook_entries):
        self.assertEqual(
            list(boardlib.__main__.logbook_entries("kilter", "test", "test")),
            [KILTER_ENTRY],
        )
        mock_logbook_entries.assert_called_once_with("kilter", "test", "test")


if __name__ == "__main__":
    unittest.main()
