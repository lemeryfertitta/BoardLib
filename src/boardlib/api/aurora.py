import datetime
import uuid
import sqlite3
import bs4
import requests
import pandas as pd
from itertools import zip_longest
from urllib.parse import unquote


HOST_BASES = {
    "aurora": "auroraboardapp",
    "decoy": "decoyboardapp",
    "grasshopper": "grasshopperboardapp",
    "kilter": "kilterboardapp",
    "soill": "soillboardapp",
    "tension": "tensionboardapp2",
    "touchstone": "touchstoneboardapp",
}
API_HOSTS = {
    board: f"https://api.{host_base}.com" for board, host_base in HOST_BASES.items()
}
WEB_HOSTS = {
    board: f"https://{host_base}.com" for board, host_base in HOST_BASES.items()
}


SHARED_TABLES = [
    "products",
    "product_sizes",
    "holes",
    "leds",
    "products_angles",
    "layouts",
    "product_sizes_layouts_sets",
    "placements",
    "sets",
    "placement_roles",
    "climbs",
    "climb_stats",
    "beta_links",
    "attempts",
    "kits",
]

USER_TABLES = [
    "users",
    "walls",
    "wall_expungements",
    "draft_climbs",
    "ascents",
    "bids",
    "tags",
    "circuits",
]


def login(board, username, password):
    response = requests.post(
        f"{WEB_HOSTS[board]}/sessions",
        json={
            "username": username,
            "password": password,
            "tou": "accepted",
            "pp": "accepted",
            "ua": "app",
        },
    )
    response.raise_for_status()
    return response.json()["session"]


def explore(board, token):
    response = requests.get(
        f"{API_HOSTS[board]}/explore",
        headers={"authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()


def get_logbook(board, token):
    return sync(board, token, tables=["ascents"]).get("ascents", [])


def get_gyms(board):
    """
    :return:
        {
            "gyms": [
                {
                    'id': 373656,
                    'username': '<username>',
                    'name': '<name>',
                    'latitude': 48.10135,
                    'longitude': 11.30113
                },
                ...
            ]
        }
    """
    response = requests.get(f"{API_HOSTS[board]}/v1/pins?types=gym")
    response.raise_for_status()
    return response.json()


def get_user(board, token, user_id):
    response = requests.get(
        f"{API_HOSTS[board]}/v2/users/{user_id}",
        headers={"authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()


def get_climb_stats(board, token, climb_id, angle):
    response = requests.get(
        f"{API_HOSTS[board]}/v1/climbs/{climb_id}/info",
        headers={"authorization": f"Bearer {token}"},
        params={"angle": angle},
    )
    response.raise_for_status()
    return response.json()


def get_climb_name(board, climb_id):
    response = requests.get(
        f"{WEB_HOSTS[board]}/climbs/{climb_id}",
    )
    response.raise_for_status()
    return bs4.BeautifulSoup(response.text, "html.parser").find("h1").text


def get_climb_name_from_db(database, climb_uuid):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM climbs WHERE uuid = ?", (climb_uuid,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


def sync(board, token=None, tables=[], sync_date=[], max_pages=100):
    payload = {}
    for table, sync_date in zip(tables, sync_date):
        payload[table] = sync_date if sync_date else "1970-01-01 00:00:00.000000"

    result = {}
    page_count = 0
    cookies = {} if not token else {"token": token}
    while not result.get("_complete") and page_count < max_pages:
        print(f"Retrieving sync results on page {page_count + 1}")
        response = requests.post(
            f"{WEB_HOSTS[board]}/sync",
            data=payload,
            cookies=cookies,
            headers={
                "Accep-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "Connection": "keep-alive",
            },
        )
        response.raise_for_status()
        response_json = response.json()
        for key, value in response_json.items():
            if key not in result:
                result[key] = value
            else:
                result[key] += value

        # Update payload with last sync date
        for user_sync in response_json.get("user_syncs", []):
            table_name = user_sync.get("table_name")
            last_synchronized_at = user_sync.get("last_synchronized_at")
            if table_name not in payload or not last_synchronized_at:
                continue

            payload[table_name] = last_synchronized_at

        for shared_sync in response_json.get("shared_syncs", []):
            table_name = shared_sync.get("table_name")
            last_synchronized_at = shared_sync.get("last_synchronized_at")
            if table_name not in payload or not last_synchronized_at:
                continue

            payload[table_name] = last_synchronized_at

        page_count += 1

    if (page_count >= max_pages) and not result.get("_complete"):
        print(
            f"Reached maximum page count of {max_pages} without completing sync. Re-run the previous command to continue syncing."
        )
    return result


def gym_boards(board):
    for gym in get_gyms(board)["gyms"]:
        yield {
            "name": gym["name"],
            "latitude": gym["latitude"],
            "longitude": gym["longitude"],
        }


def download_image(board, image_filename, output_filename):
    response = requests.get(
        f"{API_HOSTS[board]}/img/{image_filename}",
    )
    response.raise_for_status()
    with open(output_filename, "wb") as output_file:
        output_file.write(response.content)


def generate_uuid():
    return str(uuid.uuid4()).replace("-", "")


def save_ascent(
    board,
    token,
    user_id,
    climb_uuid,
    angle,
    is_mirror,
    attempt_id,
    bid_count,
    quality,
    difficulty,
    is_benchmark,
    comment,
    climbed_at,
):
    uuid = generate_uuid()
    response = requests.put(
        f"{API_HOSTS[board]}/v1/ascents/{uuid}",
        headers={"authorization": f"Bearer {token}"},
        json={
            "user_id": user_id,
            "uuid": uuid,
            "climb_uuid": climb_uuid,
            "angle": angle,
            "is_mirror": is_mirror,
            "attempt_id": attempt_id,
            "bid_count": bid_count,
            "quality": quality,
            "difficulty": difficulty,
            "is_benchmark": is_benchmark,
            "comment": comment,
            "climbed_at": climbed_at,
        },
    )
    response.raise_for_status()
    return response.json()


def save_attempt(
    board,
    token,
    user_id,
    climb_uuid,
    angle,
    is_mirror,
    bid_count,
    comment,
    climbed_at,
):
    uuid = generate_uuid()
    response = requests.put(
        f"{API_HOSTS[board]}/v1/bids/{uuid}",
        headers={"authorization": f"Bearer {token}"},
        json={
            "user_id": user_id,
            "uuid": uuid,
            "climb_uuid": climb_uuid,
            "angle": angle,
            "is_mirror": is_mirror,
            "bid_count": bid_count,
            "comment": comment,
            "climbed_at": climbed_at,
        },
    )
    response.raise_for_status()
    return response.json()


def save_climb(
    board,
    token,
    layout_id,
    setter_id,
    name,
    description,
    is_draft,
    frames,
    frames_count=1,
    frames_pace=0,
    angle=None,
):
    uuid = generate_uuid()
    data = {
        "uuid": uuid,
        "layout_id": layout_id,
        "setter_id": setter_id,
        "name": name,
        "description": description,
        "is_draft": is_draft,
        "frames_count": frames_count,
        "frames_pace": frames_pace,
        "frames": frames,
    }
    if angle:
        data["angle"] = angle

    response = requests.put(
        f"{API_HOSTS[board]}/v2/climbs/{uuid}",
        headers={"authorization": f"Bearer {token}"},
        json=data,
    )
    response.raise_for_status()
    return response.json()


def get_bids_logbook(board, token):
    return sync(board, token, tables=["bids"]).get("bids", [])


def bids_logbook_entries(board, token, db_path):
    raw_entries = get_bids_logbook(board, token)

    for raw_entry in raw_entries:
        climb_name = get_climb_name_from_db(db_path, raw_entry["climb_uuid"])

        yield {
            "climb_uuid": raw_entry["climb_uuid"],
            "user_id": raw_entry["user_id"],
            "climb_name": climb_name,
            "angle": raw_entry["angle"],
            "is_mirror": raw_entry["is_mirror"],
            "bid_count": raw_entry["bid_count"],
            "comment": raw_entry["comment"],
            "climbed_at": raw_entry["climbed_at"],
            "created_at": raw_entry["created_at"],
        }


def get_difficulty_from_db(database, climb_uuid, angle):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT display_difficulty FROM climb_stats WHERE climb_uuid = ? AND angle = ?",
        (climb_uuid, angle),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


def get_benchmark_from_db(database, climb_uuid, angle):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT benchmark_difficulty FROM climb_stats WHERE climb_uuid = ? AND angle = ?",
        (climb_uuid, angle),
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] is not None if row else False


def process_raw_ascent_entries(raw_ascents_entries, board, db_path):
    ascents_entries = []
    difficulty_mapping = get_difficulty_mapping_from_db(db_path)
    for raw_entry in raw_ascents_entries:
        if not raw_entry["is_listed"]:
            continue

        climb_name = get_climb_name_from_db(db_path, raw_entry["climb_uuid"])
        difficulty = get_difficulty_from_db(
            db_path, raw_entry["climb_uuid"], raw_entry["angle"]
        )
        is_benchmark = get_benchmark_from_db(
            db_path, raw_entry["climb_uuid"], raw_entry["angle"]
        )

        ascents_entries.append(
            {
                "board": board,
                "angle": raw_entry["angle"],
                "climb_uuid": raw_entry["climb_uuid"],
                "name": climb_name,
                "date": datetime.datetime.strptime(
                    raw_entry["climbed_at"], "%Y-%m-%d %H:%M:%S"
                ),
                "logged_grade": difficulty_to_grade(
                    difficulty_mapping, raw_entry["difficulty"]
                ),
                "displayed_grade": difficulty_to_grade(difficulty_mapping, difficulty),
                "is_benchmark": is_benchmark,
                "tries": (
                    raw_entry["attempt_id"]
                    if raw_entry["attempt_id"]
                    else raw_entry["bid_count"]
                ),
                "is_mirror": raw_entry["is_mirror"],
                "comment": raw_entry["comment"],
            }
        )
    return ascents_entries


def summarize_bids(bids_df, board):
    bids_summary = (
        bids_df.groupby(
            [
                "climb_uuid",
                "climb_name",
                bids_df["climbed_at"].dt.date,
                "is_mirror",
                "angle",
            ]
        )
        .agg({"bid_count": "sum"})
        .reset_index()
        .rename(columns={"climbed_at": "date"})
    )
    bids_summary["is_ascent"] = False
    bids_summary["tries"] = bids_summary["bid_count"]
    bids_summary["board"] = board  # Ensure the 'board' column is included
    return bids_summary


def combine_ascents_and_bids(ascents_df, bids_summary, db_path):
    final_logbook = []
    difficulty_mapping = get_difficulty_mapping_from_db(db_path)
    for _, ascent_row in ascents_df.iterrows():
        ascent_date = ascent_row["date"].date()
        ascent_climb_uuid = ascent_row["climb_uuid"]
        ascent_is_mirror = ascent_row["is_mirror"]
        ascent_angle = ascent_row["angle"]

        bid_match = bids_summary[
            (bids_summary["climb_uuid"] == ascent_climb_uuid)
            & (bids_summary["date"] == ascent_date)
            & (bids_summary["is_mirror"] == ascent_is_mirror)
            & (bids_summary["angle"] == ascent_angle)
        ]

        # Used for Climbdex to uniquely identify climbs at a particular angle
        climb_angle_uuid = f"{ascent_climb_uuid}-{ascent_angle}"

        if not bid_match.empty:
            bid_row = bid_match.iloc[0]
            total_tries = ascent_row["tries"] + bid_row["tries"]
            final_logbook.append(
                {
                    "climb_angle_uuid": climb_angle_uuid,
                    "climb_uuid": ascent_climb_uuid,
                    "board": ascent_row["board"],
                    "angle": ascent_row["angle"],
                    "climb_name": ascent_row["name"],
                    "date": ascent_row["date"],
                    "logged_grade": ascent_row["logged_grade"],
                    "displayed_grade": ascent_row.get("displayed_grade", None),
                    "is_benchmark": ascent_row.get("is_benchmark", None),
                    "tries": total_tries,
                    "is_mirror": ascent_row["is_mirror"],
                    "is_ascent": True,
                    "comment": ascent_row["comment"],
                }
            )
            bids_summary = bids_summary.drop(bid_match.index)
        else:
            final_logbook.append(
                {
                    "climb_angle_uuid": climb_angle_uuid,
                    "climb_uuid": ascent_climb_uuid,
                    "board": ascent_row["board"],
                    "angle": ascent_row["angle"],
                    "climb_name": ascent_row["name"],
                    "date": ascent_row["date"],
                    "logged_grade": ascent_row["logged_grade"],
                    "displayed_grade": ascent_row.get("displayed_grade", None),
                    "is_benchmark": ascent_row["is_benchmark"],
                    "tries": ascent_row["tries"],
                    "is_mirror": ascent_row["is_mirror"],
                    "is_ascent": True,
                    "comment": ascent_row["comment"],
                }
            )

    for _, bid_row in bids_summary.iterrows():
        climb_angle_uuid = f"{bid_row['climb_uuid']}-{bid_row['angle']}"

        difficulty = get_difficulty_from_db(
            db_path, bid_row["climb_uuid"], bid_row["angle"]
        )
        is_benchmark = get_benchmark_from_db(
            db_path, bid_row["climb_uuid"], bid_row["angle"]
        )

        final_logbook.append(
            {
                "climb_angle_uuid": climb_angle_uuid,
                "climb_uuid": bid_row["climb_uuid"],
                "board": bid_row["board"],
                "angle": bid_row["angle"],
                "climb_name": bid_row["climb_name"],
                "date": bid_row["date"],
                "logged_grade": None,
                "displayed_grade": difficulty_to_grade(difficulty_mapping, difficulty),
                "is_benchmark": is_benchmark,
                "tries": bid_row["tries"],
                "is_mirror": bid_row["is_mirror"],
                "is_ascent": False,
                "comment": bid_row.get(
                    "comment", None
                ),  # Use .get() to safely handle missing 'comment'
            }
        )
    return final_logbook


def calculate_sessions_count(group):
    group = group.sort_values(by="date")
    unique_dates = group["date"].dt.date.drop_duplicates().reset_index(drop=True)
    sessions_count = unique_dates.rank(method="dense").astype(int)
    sessions_count_map = dict(zip(unique_dates, sessions_count))
    group["sessions_count"] = group["date"].dt.date.map(sessions_count_map)
    return group


def calculate_tries_total(group):
    group = group.sort_values(by="date")
    group["tries_total"] = group["tries"].cumsum()
    return group


def logbook_entries(board, token, db_path):
    bids_entries = list(bids_logbook_entries(board, token, db_path))
    raw_ascents_entries = get_logbook(board, token)

    if not bids_entries and not raw_ascents_entries:
        return pd.DataFrame(
            columns=[
                "climb_uuid",
                "board",
                "angle",
                "climb_name",
                "date",
                "logged_grade",
                "displayed_grade",
                "is_benchmark",
                "tries",
                "is_mirror",
                "is_ascent",
                "comment",
            ]
        )

    if bids_entries:
        bids_df = pd.DataFrame(bids_entries)
        bids_df["climbed_at"] = pd.to_datetime(bids_df["climbed_at"])
        bids_summary = summarize_bids(bids_df, board)
    else:
        bids_summary = pd.DataFrame(
            columns=[
                "climb_uuid",
                "climb_name",
                "date",
                "is_mirror",
                "angle",
                "tries",
                "board",
            ]
        )

    if raw_ascents_entries:
        ascents_entries = process_raw_ascent_entries(
            raw_ascents_entries, board, db_path
        )
        ascents_df = pd.DataFrame(ascents_entries)
    else:
        ascents_df = pd.DataFrame(
            columns=[
                "board",
                "angle",
                "climb_uuid",
                "name",
                "date",
                "logged_grade",
                "displayed_grade",
                "is_benchmark",
                "tries",
                "is_mirror",
                "comment",
            ]
        )

    final_logbook = combine_ascents_and_bids(ascents_df, bids_summary, db_path)

    full_logbook_df = pd.DataFrame(
        final_logbook,
        columns=[
            "climb_angle_uuid",
            "board",
            "angle",
            "climb_name",
            "date",
            "logged_grade",
            "displayed_grade",
            "is_benchmark",
            "tries",
            "is_mirror",
            "is_ascent",
            "comment",
        ],
    )
    full_logbook_df["date"] = pd.to_datetime(full_logbook_df["date"])

    full_logbook_df = (
        full_logbook_df.groupby(["climb_name", "is_mirror", "angle"])
        .apply(calculate_sessions_count)
        .reset_index(drop=True)
    )
    full_logbook_df = (
        full_logbook_df.groupby(["climb_name", "is_mirror", "angle"])
        .apply(calculate_tries_total)
        .reset_index(drop=True)
    )

    full_logbook_df["is_repeat"] = full_logbook_df.duplicated(
        subset=["climb_name", "is_mirror", "angle"], keep="first"
    )
    full_logbook_df = full_logbook_df.sort_values(by="date")

    return full_logbook_df


def user_followers(board: str, token: str, user_id: int):
    """
    Get all accounts that follow the given user
    :param board:
    :param token:
    :param user_id:
    :return:
        {
            'users': [
                {
                    'id': int,
                    'username': str,
                    'name': optional str,
                    'avatar': optional str,
                },
                ...
            ]
        }
    """
    response = requests.get(
        f"{WEB_HOSTS[board]}/users/{user_id}/followers",
        headers={"cookie": f"token={token}"},
    )
    response.raise_for_status()
    return response.json()


def user_followees(board: str, token: str, user_id: int):
    """
    Get all accounts the given user follows
    :param board:
    :param token:
    :param user_id:
    :return:
        {
            'users': [
                {
                    'id': int,
                    'username': str,
                    'name': optional str,
                    'avatar': optional str,
                },
                ...
            ]
        }
    """
    response = requests.get(
        f"{WEB_HOSTS[board]}/users/{user_id}/followees",
        headers={"cookie": f"token={token}"},
    )
    response.raise_for_status()
    return response.json()


def follow(board: str, token: str, your_user_id: int, id_to_follow: int):
    """
    Follow a user
    """
    response = requests.post(
        f"{WEB_HOSTS[board]}/follows/save",
        headers={"cookie": f"token={token}"},
        data={
            "followee_id": id_to_follow,
            "follower_id": your_user_id,
            "state": "pending",
        },
    )
    response.raise_for_status()
    return response.json()


def unfollow(board: str, token: str, your_user_id: int, id_to_follow: int):
    """
    Unfollow a user
    """
    response = requests.post(
        f"{WEB_HOSTS[board]}/follows/save",
        headers={"cookie": f"token={token}"},
        data={
            "followee_id": id_to_follow,
            "follower_id": your_user_id,
            "state": "unfollowed",
        },
    )
    response.raise_for_status()
    return response.json()


def get_notifications(board: str, token: str, included_types: list[str] = None):
    """
    Get all notifications for the given user
    :param board:
    :param token:
    :param included_types: a list of notification types to include in the response. Optional values:
    :return:
        {
            'notifications': [
                {
                    '_type': str,
                    ...
                },
                ...
            ]
        }
    """

    if included_types is None:
        included_types = ["climbs", "follows", "users", "ascents", "likes"]

    response = requests.get(
        f"{WEB_HOSTS[board]}/notifications",
        params={t: 1 for t in included_types},
        headers={"cookie": f"token={token}"},
    )
    response.raise_for_status()
    return response.json()


def get_difficulty_mapping_from_db(database):
    connection = sqlite3.connect(database)
    return {
        row[0]: row[1]
        for row in connection.execute(
            "SELECT difficulty, boulder_name FROM difficulty_grades"
        )
    }


def difficulty_to_grade(difficulty_mapping, difficulty):
    return (
        difficulty_mapping.get(int(round(difficulty)), None)
        if difficulty is not None
        else None
    )
