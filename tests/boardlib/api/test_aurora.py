import unittest
import unittest.mock

import requests

import boardlib.api.aurora
from tests.boardlib.api.requests_mocks import get_mock_request, MockResponse


class TestAurora(unittest.TestCase):
    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(json_data="test_login"),
    )
    def test_login_success(self, mock_post):
        self.assertEqual(
            boardlib.api.aurora.login("aurora", "test", "test"), "test_login"
        )

    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_login_failure(self, mock_post):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.aurora.login("aurora", "test", "test")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(json_data="test_explore"),
    )
    def test_explore(self, mock_get):
        self.assertEqual(boardlib.api.aurora.explore("aurora", "test"), "test_explore")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_explore_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.aurora.explore("aurora", "test")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(json_data={"logbook": []}),
    )
    def test_get_logbook(self, mock_get):
        self.assertEqual(boardlib.api.aurora.get_logbook("aurora", "test", "test"), [])

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_get_logbook_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.aurora.get_logbook("aurora", "test", "test")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(json_data="test_get_gyms"),
    )
    def test_get_gyms(self, mock_get):
        self.assertEqual(boardlib.api.aurora.get_gyms("aurora"), "test_get_gyms")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_get_gyms_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.aurora.get_gyms("aurora")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(json_data="test_get_user"),
    )
    def test_get_user(self, mock_get):
        self.assertEqual(
            boardlib.api.aurora.get_user("aurora", "test", "test"), "test_get_user"
        )

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_get_user_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.aurora.get_user("aurora", "test", "test")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(json_data="test_get_climb_stats"),
    )
    def test_get_climb_stats(self, mock_get):
        self.assertEqual(
            boardlib.api.aurora.get_climb_stats("aurora", "test", "test", "test"),
            "test_get_climb_stats",
        )

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_get_climb_stats_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.aurora.get_climb_stats("aurora", "test", "test", "test")

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(text="<h1>test_get_climb_name</h1>"),
    )
    def test_get_climb_name(self, mock_get):
        self.assertEqual(
            boardlib.api.aurora.get_climb_name("aurora", "test"), "test_get_climb_name"
        )

    @unittest.mock.patch(
        "requests.get",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_get_climb_name_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.aurora.get_climb_name("aurora", "test")

    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(json_data="test_sync"),
    )
    def test_sync(self, mock_get):
        self.assertEqual(
            boardlib.api.aurora.sync("aurora", "test", "test"), "test_sync"
        )

    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_sync_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.aurora.sync("aurora", "test", "test")

    @unittest.mock.patch(
        "boardlib.api.aurora.login",
        side_effect=lambda *args, **kwargs: {
            "token": "test_token",
            "user_id": "test_user_id",
        },
    )
    @unittest.mock.patch(
        "boardlib.api.aurora.get_logbook",
        side_effect=lambda *args, **kwargs: [
            {
                "climb_uuid": "test_climb_id",
                "climbed_at": "2021-09-30 20:31:48",
                "grade": "test_grade",
                "tries": "test_tries",
                "difficulty": 15,
                "attempt_id": 0,
                "bid_count": 5,
                "angle": 30,
            }
        ],
    )
    @unittest.mock.patch(
        "boardlib.api.aurora.get_climb_name",
        side_effect=lambda *args, **kwargs: "test_climb_name",
    )
    def test_logbook_entries(self, mock_login, mock_get_climb_name, mock_get_logbook):
        self.assertEqual(
            next(boardlib.api.aurora.logbook_entries("aurora", "test", "test")),
            {
                "board": "aurora",
                "angle": 30,
                "name": "test_climb_name",
                "date": "2021-09-30",
                "grade": "5C",
                "tries": 5,
            },
        )

    @unittest.mock.patch(
        "boardlib.api.aurora.get_gyms",
        side_effect=lambda *args, **kwargs: {
                "gyms": [
                    {'id': 1575, 'username': 'testuser', 'name': 'testgym', 'latitude': 51.43236, 'longitude': 6.7432}
                ]
            
        },
    )
    def test_gym_boards(self, mock_get_gyms):
        self.assertEqual(
            next(boardlib.api.aurora.gym_boards("aurora")),
            {
                "name": "testgym",
                "latitude": 51.43236,
                "longitude": 6.7432,
            },
        )


if __name__ == "__main__":
    unittest.main()
