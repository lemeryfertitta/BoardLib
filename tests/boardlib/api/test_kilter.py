import datetime
import unittest
import unittest.mock

import requests

import boardlib.api.kilter
from tests.boardlib.api.requests_mocks import get_mock_request, MockResponse


UTC = datetime.timezone.utc

GRADES = [
    {
        "difficultyGradeId": 17,
        "boulderDifficulty": "6A+/V3",
        "routeDifficulty": "6c+/5.11c",
        "isListed": True,
        "fontScale": "6A+",
        "vScale": "V3",
        "frenchScale": "6c+",
        "ydsScale": "5.11c",
    },
    {
        "difficultyGradeId": 18,
        "boulderDifficulty": "6B/V4",
        "routeDifficulty": "7a/5.11d",
        "isListed": True,
        "fontScale": "6B",
        "vScale": "V4",
        "frenchScale": "7a",
        "ydsScale": "5.11d",
    },
]

GRADE_NAMES = {17: "6A+/V3", 18: "6B/V4"}


def make_log(**fields):
    log = {
        "logUuid": "test_log",
        "userUuid": "test_user",
        "climbUuid": "TESTCLIMB1",
        "climbName": "test_climb_1",
        "angle": 40,
        "attempts": 1,
        "topped": True,
        "flashed": True,
        "currentDifficultyId": 17,
        "createdAt": "2026-04-01T18:00:00.123456Z",
        "gymUuid": "test_gym",
        "wallUuid": "test_wall",
        "productLayoutUuid": "test_layout",
    }
    log.update(fields)
    return log


def process_logs(*logs, tz=UTC):
    return boardlib.api.kilter.process_logs("kilter", logs, GRADE_NAMES, tz)


class TestKilter(unittest.TestCase):
    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(
            json_data={"access_token": "test_token", "token_type": "Bearer"}
        ),
    )
    def test_login_success(self, mock_post):
        self.assertEqual(
            boardlib.api.kilter.login("test@example.com", "test"),
            {"access_token": "test_token", "token_type": "Bearer"},
        )
        mock_post.assert_called_once_with(
            boardlib.api.kilter.TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": "kilter",
                "scope": "openid offline_access",
                "username": "test@example.com",
                "password": "test",
            },
            headers={"Accept": "application/json"},
        )

    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(
            json_data={
                "error": "invalid_grant",
                "error_description": "Invalid user credentials",
            },
            status_code=requests.codes.unauthorized,
        ),
    )
    def test_login_invalid_credentials(self, mock_post):
        with self.assertRaisesRegex(ValueError, "email"):
            boardlib.api.kilter.login("test", "test")

    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_login_failure(self, mock_post):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.kilter.login("test@example.com", "test")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(json_data=[make_log()]),
    )
    def test_get_logs(self, mock_get):
        self.assertEqual(boardlib.api.kilter.get_logs("test_token"), [make_log()])
        mock_get.assert_called_once_with(
            "https://portal.kiltergrips.com/api/logs",
            headers={
                "Authorization": "Bearer test_token",
                "Accept": "application/json",
            },
        )

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(status_code=requests.codes.unauthorized),
    )
    def test_get_logs_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.kilter.get_logs("test_token")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(json_data=GRADES),
    )
    def test_get_grades(self, mock_get):
        self.assertEqual(boardlib.api.kilter.get_grades(), GRADES)

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(status_code=requests.codes.internal_server_error),
    )
    def test_get_grades_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.kilter.get_grades()

    def test_get_grade_names(self):
        self.assertEqual(boardlib.api.kilter.get_grade_names(GRADES), GRADE_NAMES)
        self.assertEqual(
            boardlib.api.kilter.get_grade_names(GRADES, "font"), {17: "6A+", 18: "6B"}
        )
        self.assertEqual(
            boardlib.api.kilter.get_grade_names(GRADES, "hueco"), {17: "V3", 18: "V4"}
        )

    def test_parse_timestamp(self):
        expected = datetime.datetime(2026, 4, 1, 17, 42, 10)
        for timestamp in (
            "2026-04-01T17:42:10Z",
            "2026-04-01T17:42:10.1Z",
            "2026-04-01T17:42:10.123456Z",
            "2026-04-01T17:42:10.123456789Z",
            "2026-04-01T19:42:10.5+02:00",
            "2026-04-01T17:42:10",
        ):
            self.assertEqual(
                boardlib.api.kilter.parse_timestamp(timestamp, UTC), expected
            )
        self.assertEqual(
            boardlib.api.kilter.parse_timestamp(
                "2026-04-01T23:42:10Z", datetime.timezone(datetime.timedelta(hours=-4))
            ),
            datetime.datetime(2026, 4, 1, 19, 42, 10),
        )

    def test_process_logs_flash(self):
        self.assertEqual(
            process_logs(make_log()),
            [
                {
                    "climb_angle_uuid": "TESTCLIMB1-40",
                    "climb_uuid": "TESTCLIMB1",
                    "board": "kilter",
                    "angle": 40,
                    "climb_name": "test_climb_1",
                    "date": datetime.datetime(2026, 4, 1, 18, 0, 0),
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
            ],
        )

    def test_process_logs_climb_rating(self):
        rating = {
            "climbRatingUuid": "test_rating",
            "climbUuid": "TESTCLIMB1",
            "angle": 40,
            "difficultyGradeId": 18,
            "rating": 3,
            "comment": "test_comment",
            "status": "NEW",
            "weight": 1,
            "createdAt": "2026-04-01T18:01:00.000000Z",
        }
        rated, rated_at_other_angle = process_logs(
            make_log(climbRating=rating),
            make_log(angle=45, createdAt="2026-04-01T18:30:00Z", climbRating=rating),
        )
        self.assertEqual(rated["logged_grade"], "6B/V4")
        self.assertEqual(rated["comment"], "test_comment")
        self.assertIsNone(rated_at_other_angle["logged_grade"])
        self.assertIsNone(rated_at_other_angle["comment"])

    def test_process_logs_attempts_before_ascent(self):
        (entry,) = process_logs(
            make_log(
                attempts=4,
                topped=True,
                flashed=False,
                createdAt="2026-04-01T18:30:00Z",
            ),
            make_log(attempts=2, topped=False, flashed=False),
        )
        self.assertEqual(entry["date"], datetime.datetime(2026, 4, 1, 18, 30))
        self.assertTrue(entry["is_ascent"])
        self.assertEqual(entry["tries"], 6)
        self.assertEqual(entry["tries_total"], 6)

    def test_process_logs_attempts_after_ascent(self):
        (ascent,) = process_logs(
            make_log(),
            make_log(
                attempts=2,
                topped=False,
                flashed=False,
                createdAt="2026-04-01T18:30:00Z",
            ),
            make_log(
                attempts=1,
                topped=False,
                flashed=False,
                createdAt="2026-04-01T18:45:00Z",
            ),
        )
        self.assertEqual((ascent["is_ascent"], ascent["tries"]), (True, 1))
        self.assertEqual(ascent["tries_total"], 1)

    def test_process_logs_attempts_after_ascent_other_day(self):
        ascent, attempts = process_logs(
            make_log(),
            make_log(
                attempts=2,
                topped=False,
                flashed=False,
                createdAt="2026-04-08T18:30:00Z",
            ),
        )
        self.assertEqual((ascent["is_ascent"], ascent["tries"]), (True, 1))
        self.assertEqual(attempts["date"], datetime.datetime(2026, 4, 8, 18, 30))
        self.assertEqual(attempts["is_ascent"], False)
        self.assertEqual(attempts["logged_grade"], None)
        self.assertEqual(attempts["displayed_grade"], "6A+/V3")
        self.assertEqual(attempts["tries"], 2)
        self.assertEqual(attempts["tries_total"], 3)
        self.assertEqual(attempts["sessions_count"], 2)
        self.assertTrue(attempts["is_repeat"])

    def test_process_logs_sessions(self):
        # Newest first, like the API
        entries = process_logs(
            make_log(angle=45, createdAt="2026-04-08T18:30:00Z"),
            make_log(createdAt="2026-04-08T18:00:00Z"),
            make_log(
                climbUuid="TESTCLIMB2",
                climbName="test_climb_2",
                createdAt="2026-04-01T18:30:00Z",
            ),
            make_log(
                attempts=3,
                topped=False,
                flashed=False,
                createdAt="2026-04-01T18:00:00Z",
            ),
        )
        self.assertEqual(
            [
                (
                    entry["date"].date().isoformat(),
                    entry["climb_name"],
                    entry["angle"],
                    entry["is_ascent"],
                    entry["sessions_count"],
                    entry["tries_total"],
                    entry["is_repeat"],
                )
                for entry in entries
            ],
            [
                ("2026-04-01", "test_climb_1", 40, False, 1, 3, False),
                ("2026-04-01", "test_climb_2", 40, True, 1, 1, False),
                ("2026-04-08", "test_climb_1", 40, True, 2, 4, True),
                ("2026-04-08", "test_climb_1", 45, True, 1, 1, False),
            ],
        )

    def test_process_logs_days_in_timezone(self):
        logs = (
            make_log(
                attempts=2,
                topped=False,
                flashed=False,
                createdAt="2026-04-01T23:30:00Z",
            ),
            make_log(
                attempts=1,
                topped=True,
                flashed=False,
                createdAt="2026-04-02T00:30:00Z",
            ),
        )
        self.assertEqual(len(process_logs(*logs)), 2)
        (entry,) = process_logs(
            *logs, tz=datetime.timezone(datetime.timedelta(hours=-4))
        )
        self.assertEqual(entry["date"], datetime.datetime(2026, 4, 1, 20, 30))
        self.assertEqual(entry["tries"], 3)

    def test_process_logs_zero_attempts(self):
        attempt, ascent = process_logs(
            make_log(attempts=0, topped=False, flashed=False),
            make_log(
                attempts=0,
                topped=True,
                flashed=False,
                climbUuid="TESTCLIMB2",
                createdAt="2026-04-01T18:30:00Z",
            ),
        )
        self.assertEqual((attempt["is_ascent"], attempt["tries"]), (False, 1))
        self.assertEqual((ascent["is_ascent"], ascent["tries"]), (True, 1))

    def test_process_logs_empty(self):
        self.assertEqual(process_logs(), [])

    @unittest.mock.patch(
        "requests.get",
        side_effect=lambda url, *args, **kwargs: MockResponse(
            json_data=(
                GRADES
                if url.endswith("/api/grades")
                else [
                    make_log(createdAt="2026-04-08T18:00:00Z", currentDifficultyId=18),
                    make_log(),
                ]
            )
        ),
    )
    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(json_data={"access_token": "test_token"}),
    )
    def test_logbook_entries(self, mock_post, mock_get):
        entries = boardlib.api.kilter.logbook_entries(
            "kilter", "test@example.com", "test", grade_type="font", tz=UTC
        )
        self.assertEqual(
            [(entry["date"], entry["displayed_grade"]) for entry in entries],
            [
                (datetime.datetime(2026, 4, 1, 18, 0), "6A+"),
                (datetime.datetime(2026, 4, 8, 18, 0), "6B"),
            ],
        )
        self.assertEqual(
            mock_get.call_args_list[-1].kwargs["headers"]["Authorization"],
            "Bearer test_token",
        )

    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(status_code=requests.codes.unauthorized),
    )
    def test_logbook_entries_invalid_credentials(self, mock_post):
        with self.assertRaises(ValueError):
            boardlib.api.kilter.logbook_entries("kilter", "test", "test")


if __name__ == "__main__":
    unittest.main()
