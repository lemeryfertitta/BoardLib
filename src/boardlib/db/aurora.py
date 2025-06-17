import collections
import io
import sqlite3
import zipfile

import requests


APP_PACKAGE_NAMES = {
    "aurora": "auroraboard",
    "decoy": "decoyboard",
    "grasshopper": "grasshopperboard",
    "kilter": "kilterboard",
    "soill": "soillboard",
    "tension": "tensionboard2",
    "touchstone": "touchstoneboard",
}


def download_database(board, output_file):
    """
    The sqlite3 database is stored in the assets folder of the APK files for the Android app of each board.

    This function downloads the latest APK file for the board's Android app and extracts the database from it.
    :param board: The board to download the database for.
    :param output_file: The file to write the database to.
    """
    response = requests.get(
        f"https://d.apkpure.net/b/APK/com.auroraclimbing.{APP_PACKAGE_NAMES[board]}",
        params={"version": "latest"},
        # Some user-agent is required, 403 if not included
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        },
    )
    response.raise_for_status()
    apk_file = io.BytesIO(response.content)
    with zipfile.ZipFile(apk_file, "r") as zip_file:
        with open(output_file, "wb") as output_file:
            output_file.write(zip_file.read("assets/db.sqlite3"))


def get_shared_syncs(database):
    """
    Retrieve the mapping of tables names to last sync dates for the shared (public) tables in the database.

    :param database: The path to the SQLite database file.
    :return: A dictionary mapping table names to their last synchronized date.
    """
    with sqlite3.connect(database) as connection:
        result = connection.execute(
            "SELECT table_name, last_synchronized_at FROM shared_syncs"
        )
        return {
            table_name: last_synchronized_at
            for table_name, last_synchronized_at in result.fetchall()
        }


def sync_shared_tables(database, sync_result):
    """
    Sync the shared tables in the database with the provided sync results from a sync API request.

    :param database: The path to the SQLite database file.
    :param row_counts: A dictionary mapping table names to number of rows inserted/updated/deleted.
    """
    with sqlite3.connect(database) as connection:
        row_counts = {}
        for table_name, rows in sync_result.items():
            ROW_INSERTERS.get(table_name, insert_rows_default)(
                connection, table_name, rows
            )
            row_counts[table_name] = len(rows)

        return row_counts


def insert_rows_default(connection, table_name, rows):
    """
    Insert or replace the given rows into the specified table
    :param connection: The SQLite connection object.
    :param table_name: The name of the table to insert rows into.
    :param rows: The list of rows to insert.
    """
    pragma_result = connection.execute(f"PRAGMA table_info('{table_name}')")
    value_params = ", ".join(f":{row[1]}" for row in pragma_result.fetchall())
    connection.executemany(
        f"INSERT OR REPLACE INTO {table_name} VALUES ({value_params})",
        (collections.defaultdict(lambda: None, row) for row in rows),
    )


def insert_rows_climb_stats(connection, table_name, rows):
    """
    Insert/replace/delete the given rows into the climb_stats table. When a row has no display_difficulty, this means the row should be deleted.
    :param connection: The SQLite connection object.
    :param table_name: The name of the table to insert rows into. Should be "climb_stats".
    :param rows: The list of rows to insert.
    """
    pragma_result = connection.execute(f"PRAGMA table_info('{table_name}')")
    value_params = ", ".join(f":{row[1]}" for row in pragma_result.fetchall())
    insert_rows = []
    delete_rows = []
    for row in rows:
        row_dict = collections.defaultdict(
            lambda: None,
            row,
            display_difficulty=(
                row["benchmark_difficulty"]
                if row.get("benchmark_difficulty")
                else row["difficulty_average"]
            ),
        )
        row_list = insert_rows if row_dict["display_difficulty"] else delete_rows
        row_list.append(row_dict)

    connection.executemany(
        f"INSERT OR REPLACE INTO {table_name} VALUES ({value_params})",
        insert_rows,
    )
    for row in delete_rows:
        connection.execute(
            f"DELETE FROM {table_name} WHERE climb_uuid = :climb_uuid AND angle = :angle",
            row,
        )


ROW_INSERTERS = {
    "climb_stats": insert_rows_climb_stats,
}


def get_difficulty(database, climb_uuid, angle):
    with sqlite3.connect(database) as connection:
        results = connection.execute(
            "SELECT display_difficulty, benchmark_difficulty FROM climb_stats WHERE climb_uuid = ? AND angle = ?",
            (climb_uuid, angle),
        )
        return next(results, [None, None])


def get_difficulty_mapping(database):
    with sqlite3.connect(database) as connection:
        return {
            row[0]: row[1]
            for row in connection.execute(
                "SELECT difficulty, boulder_name FROM difficulty_grades"
            )
        }


def get_climb_name(database, climb_uuid):
    with sqlite3.connect(database) as connection:
        results = connection.execute(
            "SELECT name FROM climbs WHERE uuid = ?", (climb_uuid,)
        )
        return next(results, [None])[0]
