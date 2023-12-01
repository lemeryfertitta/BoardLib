import datetime

import bs4
import requests

import boardlib.util.grades

HOST = "https://moonboard.com"

BOARD_IDS = {
    "moon2016": 1,
    "moon2017": 15,
    "moon2019": 17,
    "moon2020": 19,
    "moon2024": 21,
}

ANGLES_TO_IDS = {
    "moon2016": {
        40: 3,
    },
    "moon2017": {
        25: 2,
        40: 1,
    },
    "moon2019": {
        25: 2,
        40: 1,
    },
    "moon2020": {
        40: 1,
    },
    "moon2024": {
        25: 2,
        40: 3,
    },
}

ATTEMPTS_TO_COUNT = {
    "Flashed": "1",
    "2nd try": "2",
    "3rd try": "3",
    "more than 3 tries": "4+",
}

IDS_TO_ANGLES = {
    board_name: {angle_id: angle for angle, angle_id in angle_map.items()}
    for board_name, angle_map in ANGLES_TO_IDS.items()
}


def get_session(username, password):
    session = requests.Session()
    home_page_response = session.get(HOST)
    home_page_response.raise_for_status()
    form_token = bs4.BeautifulSoup(home_page_response.text, "html.parser").find(
        "input"
    )["value"]
    login_response = session.post(
        f"{HOST}/Account/Login",
        data={
            "Login.Username": username,
            "Login.Password": password,
            "__RequestVerificationToken": form_token,
            "X-Requested-With": "XMLHttpRequest",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    login_response.raise_for_status()
    return session


def logbook_pages(session, board, page_size=40, page=1):
    response = session.post(
        f"{HOST}/Logbook/GetLogbook",
        data={
            "sort": "",
            "page": page,
            "pageSize": page_size,
            "group": "",
            "filter": f"setupId~eq~'{BOARD_IDS[board]}'",
        },
        headers={
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    response.raise_for_status()
    response_json = response.json()
    yield from response_json["Data"]
    if response_json["Total"] > page_size * page:
        yield from logbook_pages(session, board, page_size, page + 1)


def raw_logbook_entries_for_page(session, board, entry_id, page_size=30, page=1):
    response = session.post(
        f"{HOST}/Logbook/GetLogbookEntries/{entry_id}",
        data={
            "sort": "",
            "page": page,
            "pageSize": page_size,
            "group": "",
            "filter": f"setupId~eq~'{BOARD_IDS[board]}'",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    response_json = response.json()
    yield from response_json["Data"]
    if response_json["Total"] > page_size * page:
        yield from raw_logbook_entries_for_page(
            session, board, entry_id, page_size, page + 1
        )


def raw_logbook_entries(session, board, logbook_page_size=40, entry_page_size=30):
    logbook = logbook_pages(session, board, page_size=logbook_page_size)
    for entry in logbook:
        yield from raw_logbook_entries_for_page(
            session, board, entry["Id"], page_size=entry_page_size
        )


def get_my_ranking(session, board, angle):
    response = session.post(
        f"{HOST}/Dashboard/GetMyRanking/{BOARD_IDS[board]}/{ANGLES_TO_IDS[board][angle]}",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    return response.json()


def get_summary_by_benchmark_tries(session, board, angle):
    response = session.post(
        f"{HOST}/Dashboard/GetSummaryByBenchmarkTries/{BOARD_IDS[board]}/{ANGLES_TO_IDS[board][angle]}",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    return response.json()


def logbook_entries(board, username, password, grade_type="font"):
    session = get_session(username, password)
    entries = raw_logbook_entries(session, board)
    for entry in entries:
        font_grade = entry["Problem"]["UserGrade"]
        yield {
            "board": board,
            "angle": IDS_TO_ANGLES[board][
                entry["Problem"]["MoonBoardConfiguration"]["Id"]
            ],
            "name": entry["Problem"]["Name"],
            "date": datetime.datetime.strptime(entry["DateClimbedAsString"], "%d %b %Y")
            .date()
            .isoformat(),
            "grade": (
                font_grade
                if grade_type == "font"
                else boardlib.util.grades.FONT_TO_HUECO[font_grade]
            ),
            "tries": ATTEMPTS_TO_COUNT[entry["NumberOfTries"]],
        }
