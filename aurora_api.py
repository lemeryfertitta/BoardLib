import bs4
import requests

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


def get_logbook(board, user_id, token, types="ascent"):
    response = requests.get(
        f"{API_HOSTS[board]}/v1/users/{user_id}/logbook?types={types}",
        headers={"authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()


def get_gyms(board):
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


def sync(host, token, user_id):
    response = requests.post(
        f"{host}/v1/sync",
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
                        "shared_syncs": [
                            # {
                            #     "table_name": "climbs",
                            #     "last_synchronized_at": 0,
                            # }
                        ],
                        "user_syncs": [
                            # {
                            #     "user_id": user_id,
                            #     "table_name": "ascents",
                            #     "last_synchronized_at": 0,
                            # }
                        ],
                    },
                    "tables": [
                        # "products",
                        # "product_sizes",
                        # "holes",
                        # "leds",
                        # "products_angles",
                        # "layouts",
                        # "product_sizes_layouts_sets",
                        # "placements",
                        # "sets",
                        # "placement_roles",
                        # "climbs",
                        "climb_stats",
                        # "beta_links",
                        # "attempts",
                        # "kits",
                        # "users",
                        # "walls",
                        # "wall_expungements",
                        # "draft_climbs",
                        # "ascents",
                        # "bids",
                        # "tags",
                        # "circuits",
                    ],
                    "user_id": user_id,
                    "include_multiframe_climbs": 1,
                    "include_all_beta_links": 1,
                    "include_null_climb_stats": 1,
                }
            },
            "PUT": {
                "walls": [],
                "wall_expungements": {},
            },
        },
    )
    response.raise_for_status()
    return response.json()
