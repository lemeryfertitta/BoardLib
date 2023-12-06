import unittest
import unittest.mock

import requests

import boardlib.api.moon
from tests.boardlib.api.requests_mocks import MockResponse, MockSession


class TestMoon(unittest.TestCase):
    @unittest.mock.patch(
        "requests.Session",
        side_effect=lambda: MockSession(
            MockResponse(text="<input value='token'></input>"), MockResponse()
        ),
    )
    def test_get_session_success(self, mock_session):
        self.assertIsNotNone(
            boardlib.api.moon.get_session("username", "password"),
        )

    @unittest.mock.patch(
        "requests.Session",
        side_effect=lambda: MockSession(
            MockResponse(status_code=requests.codes.bad_request)
        ),
    )
    def test_get_session_failure(self, mock_session):
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.moon.get_session("username", "password")

    def test_logbook_pages(self):
        mock_session = MockSession(
            MockResponse(
                json_data={
                    "Data": ["test1"],
                    "Total": 2,
                }
            ),
            MockResponse(
                json_data={
                    "Data": ["test2"],
                    "Total": 2,
                }
            ),
        )
        self.assertEqual(
            list(
                boardlib.api.moon.logbook_pages(mock_session, "moon2016", page_size=1)
            ),
            ["test1", "test2"],
        )

    def test_logbook_pages(self):
        mock_session = MockSession(MockResponse(status_code=requests.codes.bad_request))
        with self.assertRaises(requests.exceptions.HTTPError):
            list(boardlib.api.moon.logbook_pages(mock_session, "moon2016"))

    def raw_logbook_entries_for_page(self):
        mock_session = MockSession(
            MockResponse(
                json_data={
                    "Data": ["test1"],
                    "Total": 2,
                }
            ),
            MockResponse(
                json_data={
                    "Data": ["test2"],
                    "Total": 2,
                }
            ),
        )
        self.assertEqual(
            list(
                boardlib.api.moon.raw_logbook_entries_for_page(
                    mock_session, "moon2016", "test", page_size=1
                )
            ),
            ["test1", "test2"],
        )

    def test_raw_logbook_entries(self):
        mock_session = MockSession(
            MockResponse(
                json_data={
                    "Data": [{"Id": "test_id1"}],
                    "Total": 2,
                }
            ),
            MockResponse(
                json_data={
                    "Data": ["test_entry1"],
                    "Total": 2,
                }
            ),
            MockResponse(
                json_data={
                    "Data": ["test_entry2"],
                    "Total": 2,
                }
            ),
            MockResponse(
                json_data={
                    "Data": [{"Id": "test_id1"}],
                    "Total": 2,
                }
            ),
            MockResponse(
                json_data={
                    "Data": ["test_entry3"],
                    "Total": 2,
                }
            ),
            MockResponse(
                json_data={
                    "Data": ["test_entry4"],
                    "Total": 2,
                }
            ),
        )
        self.assertEqual(
            list(
                boardlib.api.moon.raw_logbook_entries(
                    mock_session, "moon2016", logbook_page_size=1, entry_page_size=1
                )
            ),
            ["test_entry1", "test_entry2", "test_entry3", "test_entry4"],
        )

    def test_get_my_ranking(self):
        mock_session = MockSession(
            MockResponse(json_data="test"),
        )
        self.assertEqual(
            boardlib.api.moon.get_my_ranking(mock_session, "moon2016", 40),
            "test",
        )

    def test_get_my_ranking_failure(self):
        mock_session = MockSession(
            MockResponse(status_code=requests.codes.bad_request),
        )
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.moon.get_my_ranking(mock_session, "moon2016", 40)

    def test_get_summary_by_benchmark_tries(self):
        mock_session = MockSession(
            MockResponse(json_data="test"),
        )
        self.assertEqual(
            boardlib.api.moon.get_summary_by_benchmark_tries(
                mock_session, "moon2016", 40
            ),
            "test",
        )

    def test_get_summary_by_benchmark_tries_failure(self):
        mock_session = MockSession(
            MockResponse(status_code=requests.codes.bad_request),
        )
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.moon.get_summary_by_benchmark_tries(
                mock_session, "moon2016", 40
            )

    @unittest.mock.patch(
        "requests.Session",
        side_effect=lambda: MockSession(
            MockResponse(text="<input value='token'></input>"),
            MockResponse(),
            MockResponse(
                json_data={
                    "Data": [{"Id": "test_id"}],
                    "Total": 1,
                }
            ),
            MockResponse(
                json_data={
                    "Data": [
                        {
                            "Problem": {
                                "UserGrade": "7A",
                                "MoonBoardConfiguration": {"Id": 3},
                                "Name": "test_name",
                            },
                            "DateClimbedAsString": "05 Sep 2023",
                            "NumberOfTries": "Flashed",
                        }
                    ],
                    "Total": 1,
                }
            ),
        ),
    )
    def test_logbook_entries(self, mock_session):
        self.assertEqual(
            next(boardlib.api.moon.logbook_entries("moon2016", "username", "password")),
            {
                "board": "moon2016",
                "grade": "7A",
                "angle": 40,
                "name": "test_name",
                "date": "2023-09-05",
                "tries": "1",
            },
        )

    def test_get_map_markers(self):
        mock_session = MockSession(
            MockResponse(
                json_data="test",
            )
        )
        self.assertEqual(
            boardlib.api.moon.get_map_markers(mock_session),
            "test",
        )

    def test_get_map_markers_failure(self):
        mock_session = MockSession(
            MockResponse(status_code=requests.codes.bad_request),
        )
        with self.assertRaises(requests.exceptions.HTTPError):
            boardlib.api.moon.get_map_markers(mock_session)

    def test_gym_boards(self):
        mock_session = MockSession(
            MockResponse(
                json_data=[
                    {
                        "Name": "The School Room",
                        "Description": "The original MoonBoard in the legendary School Room. \r\n\r\nThe School Room, Sheffield is a high spec members-only training facility for intermediate to advanced climbers aged 18+ who wish to improve their strength and endurance for climbing. \r\n\r\nOpen 24/7, 7-days a week.",
                        "Image": "/Content/Account/Users/MoonBoards/SchoolRoom.jpg",
                        "Latitude": 53.386304,
                        "Longitude": -1.47619,
                        "IsCommercial": True,
                        "IsLed": True,
                        "LatLng": [53.386304, -1.47619],
                    }
                ]
            )
        )
        self.assertEqual(
            next(boardlib.api.moon.gym_boards(mock_session)),
            {
                "name": "The School Room",
                "latitude": 53.386304,
                "longitude": -1.47619,
            },
        )
