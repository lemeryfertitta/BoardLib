import datetime
import uuid
import sqlite3
import bs4
import requests
import pandas as pd

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


def get_logbook(board, token, user_id):
    sync_results = user_sync(board, token, user_id, tables=["ascents"])
    return sync_results["PUT"]["ascents"]


def get_grades(board):
    sync_results = shared_sync(board, tables=["difficulty_grades"])
    return sync_results["PUT"]["difficulty_grades"]


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

# Add a function to get climb name from local database
def get_climb_name_from_db(database, climb_uuid):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM climbs WHERE uuid = ?", (climb_uuid,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


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


def logbook_entries(board, username, password, grade_type="font", database=None):
    login_info = login(board, username, password)
    raw_entries = get_logbook(board, login_info["token"], login_info["user_id"])
    grades = get_grades(board)
    for raw_entry in raw_entries:
        if not raw_entry["is_listed"]:
            continue
        attempt_id = raw_entry["attempt_id"]
        if database:
            climb_name = get_climb_name_from_db(database, raw_entry["climb_uuid"])
        else:
            climb_name = get_climb_name(board, raw_entry["climb_uuid"])
        yield {
            "board": board,
            "angle": raw_entry["angle"],
            "name": climb_name if climb_name else "Unknown Climb",
            "date": datetime.datetime.strptime(
                raw_entry["climbed_at"], "%Y-%m-%d %H:%M:%S"
            )
            .date()
            .isoformat(),
            "grade": (
                grades[raw_entry["difficulty"]]["french_name"]
                if grade_type == "font"
                else grades[raw_entry["difficulty"]]["verm_name"]
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


def get_bids_logbook(board, token, user_id):
    sync_results = user_sync(board, token, user_id, tables=["bids"])
    return sync_results["PUT"]["bids"]




def bids_logbook_entries(board, username, password, db_path=None):
    login_info = login(board, username, password)
    raw_entries = get_bids_logbook(board, login_info["token"], login_info["user_id"])
    
    for raw_entry in raw_entries:
        if db_path:
            climb_name = get_climb_name_from_db(db_path, raw_entry["climb_uuid"])
        else:
            climb_name = get_climb_name(board, raw_entry["climb_uuid"])
        
        yield {
            "uuid": raw_entry["uuid"],
            "user_id": raw_entry["user_id"],
            "climb_uuid": raw_entry["climb_uuid"],
            "climb_name": climb_name if climb_name else "Unknown Climb",
            "angle": raw_entry["angle"],
            "is_mirror": raw_entry["is_mirror"],
            "bid_count": raw_entry["bid_count"],
            "comment": raw_entry["comment"],
            "climbed_at": raw_entry["climbed_at"],
            "created_at": raw_entry["created_at"],
        }

def total_logbook_entries(board, username, password, grade_type="font", db_path=None):
    # Get bids and ascents data
    login_info = login(board, username, password)
    token = login_info["token"]
    user_id = login_info["user_id"]
    
    bids_entries = list(bids_logbook_entries(board, username, password, db_path))
    raw_ascents_entries = get_logbook(board, token, user_id)
    
    # Convert bids entries to DataFrame
    bids_df = pd.DataFrame(bids_entries)
    bids_df['climbed_at'] = pd.to_datetime(bids_df['climbed_at'])
    
    # Process raw ascents entries and convert to DataFrame
    ascents_entries = []
    grades = get_grades(board)

    # Convert grades to dictionary for easy lookup
    grades_dict = {grade['difficulty']: grade for grade in grades}

    for raw_entry in raw_ascents_entries:
        if not raw_entry["is_listed"]:
            continue
        if db_path:
            climb_name = get_climb_name_from_db(db_path, raw_entry["climb_uuid"])
        else:
            climb_name = get_climb_name(board, raw_entry["climb_uuid"])
        
        grade_info = grades_dict.get(raw_entry["difficulty"], {})
        grade = grade_info.get("french_name" if grade_type == "font" else "verm_name", "Unknown")
        
        ascents_entries.append({
            "board": board,
            "angle": raw_entry["angle"],
            "name": climb_name if climb_name else "Unknown Climb",
            "date": datetime.datetime.strptime(raw_entry["climbed_at"], "%Y-%m-%d %H:%M:%S"),
            "logged_grade": grade,
            "tries": raw_entry["attempt_id"] if raw_entry["attempt_id"] else raw_entry["bid_count"],
            "is_mirror": raw_entry["is_mirror"]
        })
    
    ascents_df = pd.DataFrame(ascents_entries)
    
    # Summarize the bids table
    bids_summary = bids_df.groupby(['climb_name', bids_df['climbed_at'].dt.date, 'is_mirror', 'angle']).agg({
        'bid_count': 'sum'
    }).reset_index().rename(columns={'climbed_at': 'date'})
    
    # Create a new column for is_ascent
    bids_summary['is_ascent'] = False
    bids_summary['tries'] = bids_summary['bid_count']
    
    # Check for ascents and update the logbook
    final_logbook = []

    for _, ascent_row in ascents_df.iterrows():
        ascent_date = ascent_row['date'].date()
        ascent_climb_name = ascent_row['name']
        ascent_is_mirror = ascent_row['is_mirror']
        ascent_angle = ascent_row['angle']
        
        # Find corresponding bids entries
        bid_match = bids_summary[
            (bids_summary['climb_name'] == ascent_climb_name) & 
            (bids_summary['date'] == ascent_date) & 
            (bids_summary['is_mirror'] == ascent_is_mirror) &
            (bids_summary['angle'] == ascent_angle)
        ]
        
        if not bid_match.empty:
            bid_row = bid_match.iloc[0]
            total_tries = ascent_row['tries'] + bid_row['tries']
            final_logbook.append({
                'board': ascent_row['board'],
                'angle': ascent_row['angle'],
                'climb_name': ascent_row['name'],
                'date': ascent_row['date'],
                'logged_grade': ascent_row['logged_grade'],
                'tries': total_tries,
                'is_mirror': ascent_row['is_mirror'],
                'is_ascent': True
            })
            bids_summary = bids_summary.drop(bid_match.index)  # Remove matched bids
        else:
            final_logbook.append({
                'board': ascent_row['board'],
                'angle': ascent_row['angle'],
                'climb_name': ascent_row['name'],
                'date': ascent_row['date'],
                'logged_grade': ascent_row['logged_grade'],
                'tries': ascent_row['tries'],
                'is_mirror': ascent_row['is_mirror'],
                'is_ascent': True
            })
    
    # Add remaining bids that do not have corresponding ascents
    for _, bid_row in bids_summary.iterrows():
        final_logbook.append({
            'board': board,
            'angle': bid_row['angle'],
            'climb_name': bid_row['climb_name'],
            'date': bid_row['date'],
            'logged_grade': 'NA',  # We don't have grade information for bids
            'tries': bid_row['tries'],
            'is_mirror': bid_row['is_mirror'],
            'is_ascent': False
        })
    
    # Convert to DataFrame
    final_logbook_df = pd.DataFrame(final_logbook, columns=['board', 'angle', 'climb_name', 'date', 'logged_grade', 'tries', 'is_mirror', 'is_ascent'])
    
    # Ensure all dates are converted to Timestamps
    final_logbook_df['date'] = pd.to_datetime(final_logbook_df['date'])
    
    # Sort the DataFrame by date
    final_logbook_df = final_logbook_df.sort_values(by='date')

    # Calculate sessions_count and tries_total
    def calculate_sessions_count(group):
        group = group.sort_values(by='date')
        unique_dates = group['date'].dt.date.drop_duplicates().reset_index(drop=True)
        sessions_count = unique_dates.rank(method='dense').astype(int)
        sessions_count_map = dict(zip(unique_dates, sessions_count))
        group['sessions_count'] = group['date'].dt.date.map(sessions_count_map)
        return group
    
    final_logbook_df = final_logbook_df.groupby(['climb_name', 'is_mirror', 'angle']).apply(calculate_sessions_count).reset_index(drop=True)
    
    def calculate_tries_total(group):
        group = group.sort_values(by='date')
        group['tries_total'] = group['tries'].cumsum()
        return group

    final_logbook_df = final_logbook_df.groupby(['climb_name', 'is_mirror', 'angle']).apply(calculate_tries_total).reset_index(drop=True)
    
    # Add is_repeat column
    final_logbook_df['is_repeat'] = final_logbook_df.duplicated(subset=['climb_name', 'is_mirror', 'angle'], keep='first')
    
    return final_logbook_df

'''
ToDo:
* Get Grade from grade_stats
    Either average_grade or displayed grade.
    Solution for local db and API calls needed
'''