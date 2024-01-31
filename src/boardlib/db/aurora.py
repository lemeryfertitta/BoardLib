import collections
import io
import sqlite3
import zipfile

import requests

import boardlib.api.aurora


APP_PACKAGE_NAMES = {
    "aurora": "auroraboard",
    "decoy": "decoyboard",
    "grasshopper": "grasshopperboard",
    "kilter": "kilterboard",
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


def sync_shared_tables(board, database):
    """
    Syncs the public tables from the remote database to the local database.
    If the last sync is too old, it is possible that the remote will respond with an empty object.
    There appears to be some limit to the amount of data that can be transferred via a sync, but this limit is opaque.

    :param board: The board to sync the database for.
    :param database: The sqlite3 database file to sync.
    :returns: a mapping of synchronized table names to counts of inserted/updated/deleted rows.
    """
    with sqlite3.connect(database) as connection:
        result = connection.execute(
            "SELECT table_name, last_synchronized_at FROM shared_syncs"
        )
        shared_syncs = [
            {"table_name": table_name, "last_synchronized_at": last_synchronized_at}
            for table_name, last_synchronized_at in result.fetchall()
        ]
        shared_sync_result = boardlib.api.aurora.shared_sync(
            board, tables=boardlib.api.aurora.SHARED_TABLES, shared_syncs=shared_syncs
        )
        row_counts = {}
        for table_name, rows in shared_sync_result["PUT"].items():
            ROW_INSERTERS.get(table_name, insert_rows_default)(
                connection, table_name, rows
            )
            row_counts[table_name] = len(rows)

        return row_counts


def insert_rows_default(connection, table_name, rows):
    pragma_result = connection.execute(f"PRAGMA table_info('{table_name}')")
    value_params = ", ".join(f":{row[1]}" for row in pragma_result.fetchall())
    connection.executemany(
        f"INSERT OR REPLACE INTO {table_name} VALUES ({value_params})",
        (collections.defaultdict(lambda: None, row) for row in rows),
    )


def insert_rows_climb_stats(connection, table_name, rows):
    pragma_result = connection.execute(f"PRAGMA table_info('{table_name}')")
    value_params = ", ".join(f":{row[1]}" for row in pragma_result.fetchall())
    insert_rows = []
    delete_rows = []
    for row in rows:
        row_dict = collections.defaultdict(
            lambda: None,
            row,
            display_difficulty=row["benchmark_difficulty"]
            if row.get("benchmark_difficulty")
            else row["difficulty_average"],
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
