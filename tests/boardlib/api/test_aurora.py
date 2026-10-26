import unittest
import unittest.mock

import requests

import boardlib.api.aurora
from tests.boardlib.api.requests_mocks import get_mock_request, MockResponse


class TestAurora(unittest.TestCase):
    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(
            json_data={"session": {"token": "test", "user_id": 1234}},
        ),
    )
    def test_login_success(self, mock_post):
        self.assertEqual(
            boardlib.api.aurora.login("aurora", "test", "test"),
            {"token": "test", "user_id": 1234},
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
        "requests.post",
        side_effect=get_mock_request(json_data={"ascents": []}),
    )
    def test_get_logbook(self, mock_post):
        self.assertEqual(boardlib.api.aurora.get_ascents("aurora", "test"), [])

    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_get_logbook_failure(self, mock_get):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.aurora.get_ascents("aurora", "test")

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
        "requests.post",
        side_effect=lambda *args, **kwargs: MockResponse(
            json_data={"climbs": [], "_complete": True}
        ),
    )
    def test_sync(self, mock_post):
        self.assertEqual(
            list(
                boardlib.api.aurora.sync(
                    "aurora", {"climbs": boardlib.api.aurora.BASE_SYNC_DATE}, "test"
                )
            ),
            [{"climbs": []}],
        )

    @unittest.mock.patch(
        "requests.post",
        side_effect=get_mock_request(status_code=requests.codes.bad_request),
    )
    def test_sync_failure(self, mock_post):
        with self.assertRaises(requests.exceptions.HTTPError):
            list(
                boardlib.api.aurora.sync(
                    "aurora", {"climbs": boardlib.api.aurora.BASE_SYNC_DATE}, "test"
                )
            )

    @unittest.mock.patch(
        "boardlib.api.aurora.get_gyms",
        side_effect=lambda *args, **kwargs: {
            "gyms": [
                {
                    "id": 1575,
                    "username": "testuser",
                    "name": "testgym",
                    "latitude": 51.43236,
                    "longitude": 6.7432,
                }
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
