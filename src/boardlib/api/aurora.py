import datetime

import bs4
import requests

import boardlib.util.grades

HOST_BASES = {
    "aurora": "auroraboardapp",
    "decoy": "decoyboardapp",
    "grasshopper": "grasshopperboardapp",
    "kilter": "kilterboardapp",
    "tension": "tensionboardapp2",
    "touchstone": "touchstoneboardapp",
}
API_HOSTS = {
    board: f"https://api.{host_base}.com" for board, host_base in HOST_BASES.items()
}
WEB_HOSTS = {
    board: f"https://{host_base}.com" for board, host_base in HOST_BASES.items()
}

GRADES = {
    10: "4A",
    11: "4B",
    12: "4C",
    13: "5A",
    14: "5B",
    15: "5C",
    16: "6A",
    17: "6A+",
    18: "6B",
    19: "6B+",
    20: "6C",
    21: "6C+",
    22: "7A",
    23: "7A+",
    24: "7B",
    25: "7B+",
    26: "7C",
    27: "7C+",
    28: "8A",
    29: "8A+",
    30: "8B",
    31: "8B+",
    32: "8C",
    33: "8C+",
    34: "9A",
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
        f"{API_HOSTS[board]}/v1/logins",
        json={"username": username, "password": password},
    )
    response.raise_for_status()
    return response.json()


def explore(board, token):
    response = requests.get(
        f"{API_HOSTS[board]}/explore",
        headers={"authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()


def get_logbook(board, token, user_id, types="ascent"):
    response = requests.get(
        f"{API_HOSTS[board]}/v1/users/{user_id}/logbook?types={types}",
        headers={"authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()["logbook"]


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


def get_climb(board, token, climb_id):
    response = requests.get(
        f"{API_HOSTS[board]}/v1/climbs/{climb_id}/info",
        headers={"authorization": f"Bearer {token}"},
        params={"angle": angle},
    )
    response.raise_for_status()


def get_climb_name(board, climb_id):
    response = requests.get(
        f"{WEB_HOSTS[board]}/climbs/{climb_id}",
    )
    response.raise_for_status()
    return bs4.BeautifulSoup(response.text, "html.parser").find("h1").text


def user_sync(
    board,
    token,
    user_id,
    tables=[],
    walls=[],
    wall_expungements=[],
    shared_syncs=[],
    user_syncs=[],
):
    """
    :param tables: list of tables to download. The following are valid:
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
        "users",
        "walls",
        "wall_expungements",
        "draft_climbs",
        "ascents",
        "bids",
        "tags",
        "circuits",

    :param walls: list of walls to upload
    :param wall_expungements: list of walls to delete
    :parm shared_syncs: list of {"table_name": <table_name>, "last_synchronized_at": <last_synchronized_at>}
        e.g. [{'table_name': 'climbs', 'last_synchronized_at': '2023-06-07 20:36:41.578003'}]
        It looks like the largest table (climbs) won't synchronize unless it has a shared_sync with last_synchronized_at set.
    """
    response = requests.post(
        f"{API_HOSTS[board]}/v1/sync",
        headers={"authorization": f"Bearer {token}"},
        json={
            "client": {
                "enforces_product_passwords": 1,
                "enforces_layout_passwords": 1,
                "manages_power_responsibly": 1,
                "ufd": 1,
            },
            "GET": {
                "query": {
                    "syncs": {
                        "shared_syncs": shared_syncs,
                        "user_syncs": user_syncs,
                    },
                    "tables": tables,
                    "user_id": user_id,
                    "include_multiframe_climbs": 1,
                    "include_all_beta_links": 1,
                    "include_null_climb_stats": 1,
                }
            },
            "PUT": {
                "walls": walls,
                "wall_expungements": wall_expungements,
            },
        },
    )
    response.raise_for_status()
    return response.json()


def shared_sync(
    board,
    tables=[],
    shared_syncs=[],
):
    """
    Shared syncs are used to download data from the board. They are not authenticated.

    :param tables: list of tables to download. The following are valid:
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
    """
    response = requests.post(
        f"{API_HOSTS[board]}/v1/sync",
        json={
            "client": {
                "enforces_product_passwords": 1,
                "enforces_layout_passwords": 1,
                "manages_power_responsibly": 1,
                "ufd": 1,
            },
            "GET": {
                "query": {
                    "syncs": {
                        "shared_syncs": shared_syncs,
                    },
                    "tables": tables,
                    "include_multiframe_climbs": 1,
                    "include_all_beta_links": 1,
                    "include_null_climb_stats": 1,
                }
            },
        },
    )
    response.raise_for_status()
    return response.json()


def logbook_entries(board, username, password, grade_type="font"):
    login_info = login(board, username, password)
    raw_entries = get_logbook(board, login_info["token"], login_info["user_id"])
    for raw_entry in raw_entries:
        font_grade = GRADES[raw_entry["difficulty"]]
        attempt_id = raw_entry["attempt_id"]
        yield {
            "board": board,
            "angle": raw_entry["angle"],
            "name": get_climb_name(board, raw_entry["climb_uuid"]),
            "date": datetime.datetime.strptime(
                raw_entry["climbed_at"], "%Y-%m-%d %H:%M:%S"
            )
            .date()
            .isoformat(),
            "grade": (
                font_grade
                if grade_type == "font"
                else boardlib.util.grades.FONT_TO_HUECO[font_grade]
            ),
            "tries": attempt_id if attempt_id else raw_entry["bid_count"],
            "is_mirror": raw_entry["is_mirror"],
        }


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
