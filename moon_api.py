import bs4
import requests

HOST = "https://moonboard.com"

BOARD_IDS = {
    "2016": 1,
    "2017": 15,
    "2019": 17,
    "2020": 19,
    "2024": 21,
}

ANGLE_IDS = {
    "2016": {
        "40": "3",
    },
    "2017": {
        "25": "2",
        "40": "1",
    },
    "2019": {
        "25": "2",
        "40": "1",
    },
    "2020": {
        "40": "1",
    },
    "2024": {
        "25": "2",
        "40": "3",
    },
}


def get_session(username, password):
    session = requests.Session()
    response = session.get(HOST)
    form_token = bs4.BeautifulSoup(response.text, "html.parser").find("input")["value"]
    response = session.post(
        f"{HOST}/Account/Login",
        data={
            "Login.Username": username,
            "Login.Password": password,
            "__RequestVerificationToken": form_token,
            "X-Requested-With": "XMLHttpRequest",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    return session


def get_logbook(session, board, page_size=40, page=1):
    print(f"Request logbook entries on page {page}")
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
        yield from get_logbook(session, board, page_size, page + 1)


def get_logbook_entry(session, entry_id, board, page_size=30, page=1):
    print(f"Request logbook entry {entry_id} climbs on page {page}")
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
        yield from get_logbook_entry(session, entry_id, board, page_size, page + 1)


def get_logbook_entries(session, board):
    logbook = get_logbook(session, board)
    for entry in logbook:
        yield from get_logbook_entry(session, entry["Id"], board)


def get_my_ranking(session, board, angle):
    response = session.post(
        f"{HOST}/Dashboard/GetMyRanking/{BOARD_IDS[board]}/{ANGLE_IDS[board][angle]}",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    return response.json()


def get_summary_by_benchmark_tries(session, board, angle):
    response = session.post(
        f"{HOST}/Dashboard/GetSummaryByBenchmarkTries/{BOARD_IDS[board]}/{ANGLE_IDS[board][angle]}",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    return response.json()
