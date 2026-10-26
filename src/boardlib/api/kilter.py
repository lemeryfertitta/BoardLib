"""
Kilter Board support for the app that replaced the Aurora-based one in March 2026.

Kilter left Aurora Climbing in March 2026 and shut down kilterboardapp.com, so the
Aurora functions in boardlib.api.aurora no longer work for the Kilter Board. The new
app signs in through Keycloak at idp.kiltergrips.com and serves the logbook from
portal.kiltergrips.com. Climb UUIDs were kept from the Aurora era.
"""

import collections
import datetime
import re

import requests


BOARD = "kilter"
HOST = "https://portal.kiltergrips.com"
TOKEN_URL = "https://idp.kiltergrips.com/realms/kilter/protocol/openid-connect/token"
CLIENT_ID = "kilter"
SCOPE = "openid offline_access"
GRADE_TYPES = {
    "boulder": "boulderDifficulty",
    "font": "fontScale",
    "hueco": "vScale",
}


def login(username, password):
    """
    Sign in with the email address and password of a Kilter account. The username
    of the old Aurora-based app does not work.

    :return: The OpenID Connect token response. For example:
        {
            "access_token": "<token>",
            "expires_in": 300,
            "refresh_token": "<token>",
            "token_type": "Bearer",
            ...
        }
    """
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "scope": SCOPE,
            "username": username,
            "password": password,
        },
        headers={"Accept": "application/json"},
    )
    if response.status_code == requests.codes["unauthorized"]:
        raise ValueError(
            "Invalid email or password. The Kilter app signs in with the email address "
            "of the account, not the username of the old Aurora-based app."
        )
    response.raise_for_status()
    return response.json()


def get_logs(token):
    """
    Get all logs of the signed-in user, newest first. A log is one or more attempts
    on a climb at an angle, with or without a top. climbRating is only present when
    the user has rated the climb, and can be for another angle.

    :return: list of logs. For example:
        [
            {
                "logUuid": "<uuid>",
                "userUuid": "<uuid>",
                "climbUuid": "<uuid>",
                "climbName": "<name>",
                "angle": 40,
                "attempts": 3,
                "topped": True,
                "flashed": False,
                "currentDifficultyId": 17,
                "createdAt": "2026-04-01T17:42:10.123456Z",
                "gymUuid": "<uuid>",
                "wallUuid": "<uuid>",
                "productLayoutUuid": "<uuid>",
                "climbRating": {
                    "angle": 40,
                    "difficultyGradeId": 18,
                    "rating": 3,
                    "comment": "<comment>",
                    ...
                },
            },
            ...
        ]
    """
    response = requests.get(
        f"{HOST}/api/logs",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    response.raise_for_status()
    return response.json()


def get_grades():
    """
    :return: list of grades. For example:
        [
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
            ...
        ]
    """
    response = requests.get(
        f"{HOST}/api/grades", headers={"Accept": "application/json"}
    )
    response.raise_for_status()
    return response.json()


def get_grade_names(grades, grade_type="boulder"):
    """
    :param grades: The grades from get_grades.
    :param grade_type: "boulder" (e.g. 6A+/V3), "font" (e.g. 6A+) or "hueco" (e.g. V3).
    :return: A dictionary mapping difficulty ids to grade names.
    """
    field = GRADE_TYPES[grade_type]
    return {grade["difficultyGradeId"]: grade[field] for grade in grades}


def difficulty_to_grade(grade_names, difficulty):
    return grade_names.get(int(round(difficulty))) if difficulty is not None else None


def parse_timestamp(timestamp, tz=None):
    """
    Convert a UTC timestamp from the API, such as "2026-04-01T17:42:10.123456Z", to a
    naive datetime in the given timezone, to the second.

    :param tz: The target timezone. Defaults to the local timezone.
    """
    # Before Python 3.11, fromisoformat needs an explicit offset and 3 or 6 fractional digits.
    timestamp = re.sub(
        r"\.(\d+)",
        lambda match: "." + match.group(1)[:6].ljust(6, "0"),
        timestamp.replace("Z", "+00:00"),
    )
    parsed = datetime.datetime.fromisoformat(timestamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(tz).replace(tzinfo=None, microsecond=0)


def log_to_entry(board, log, grade_names, tz=None):
    is_ascent = bool(log.get("topped") or log.get("flashed"))
    attempts = log.get("attempts") or 0
    # The user's own grade and comment, if they rated the climb at this angle
    rating = log.get("climbRating") or {}
    if rating.get("angle") != log.get("angle"):
        rating = {}

    return {
        "climb_angle_uuid": f"{log.get('climbUuid')}-{log.get('angle')}",
        "climb_uuid": log.get("climbUuid"),
        "board": board,
        "angle": log.get("angle"),
        "climb_name": log.get("climbName"),
        "date": parse_timestamp(log["createdAt"], tz),
        "logged_grade": difficulty_to_grade(
            grade_names, rating.get("difficultyGradeId")
        ),
        "displayed_grade": difficulty_to_grade(
            grade_names, log.get("currentDifficultyId")
        ),
        # The API has no benchmark or mirror information
        "is_benchmark": None,
        # A log is at least one try, even if the app recorded 0 attempts
        "tries": max(attempts, 1),
        "is_mirror": None,
        "is_ascent": is_ascent,
        "comment": rating.get("comment"),
    }


def climb_key(entry):
    return (
        entry["climb_uuid"] or entry["climb_name"],
        entry["is_mirror"],
        entry["angle"],
    )


def add_session_counts(logbook):
    """
    Add sessions_count, tries_total and is_repeat to date-sorted logbook entries, as
    for the Aurora boards. For each climb, angle and mirror setting: the number of
    days with an entry so far, the number of tries so far, and whether there is an
    earlier entry.
    """
    days = collections.defaultdict(set)
    tries_totals = collections.defaultdict(int)
    for entry in logbook:
        key = climb_key(entry)
        entry["is_repeat"] = key in tries_totals
        days[key].add(entry["date"].date())
        entry["sessions_count"] = len(days[key])
        tries_totals[key] += entry["tries"]
        entry["tries_total"] = tries_totals[key]
    return logbook


def process_logs(board, logs, grade_names, tz=None):
    """
    Turn logs from get_logs into logbook entries, sorted by date.

    Each log with a top is an ascent. The tries of logs without a top are added to the
    next ascent of the same climb at the same angle on the same day, like the attempts
    of the Aurora boards. Logs without a top after an ascent of the climb that day are
    left out, as the climb was already sent. Other logs without a top are summed into
    one entry with is_ascent False.

    :param grade_names: The grade names from get_grade_names.
    :param tz: The timezone for dates and days. Defaults to the local timezone.
    """
    entries = sorted(
        (log_to_entry(board, log, grade_names, tz) for log in logs),
        key=lambda entry: entry["date"],
    )

    logbook = []
    attempts = {}
    sent = set()
    for entry in entries:
        key = climb_key(entry) + (entry["date"].date(),)
        if entry["is_ascent"]:
            earlier_attempts = attempts.pop(key, None)
            if earlier_attempts:
                entry["tries"] += earlier_attempts["tries"]
            sent.add(key)
            logbook.append(entry)
        elif key in sent:
            continue
        elif key in attempts:
            attempts[key]["tries"] += entry["tries"]
        else:
            attempts[key] = entry

    logbook = sorted(logbook + list(attempts.values()), key=lambda entry: entry["date"])
    return add_session_counts(logbook)


def logbook_entries(board, username, password, grade_type="boulder", tz=None):
    """
    Sign in and download the logbook, with the same fields as the other boards. The
    new app only has the logs made with it, from late March 2026 on.

    :param board: The board name written to each entry, normally "kilter".
    :param username: The email address of the Kilter account.
    :param grade_type: "boulder" (e.g. 6A+/V3), "font" (e.g. 6A+) or "hueco" (e.g. V3).
    :param tz: The timezone for dates and days. Defaults to the local timezone.
    """
    token = login(username, password)["access_token"]
    grade_names = get_grade_names(get_grades(), grade_type)
    return process_logs(board, get_logs(token), grade_names, tz)
