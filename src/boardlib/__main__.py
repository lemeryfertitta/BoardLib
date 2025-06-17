import argparse
import csv
import getpass
import os
import pathlib
import sys

import boardlib.api.aurora
import boardlib.api.moon
import boardlib.db.aurora


LOGBOOK_FIELDS = (
    "board",
    "angle",
    "climb_name",
    "date",
    "logged_grade",
    "displayed_grade",
    "is_benchmark",
    "tries",
    "is_mirror",
    "sessions_count",
    "tries_total",
    "is_repeat",
    "is_ascent",
    "comment",
)


def logbook_entries(board, username, password, database=None):
    api = (
        boardlib.api.moon
        if board.startswith("moon")
        else boardlib.api.aurora if board in boardlib.api.aurora.HOST_BASES else None
    )
    if api:
        yield from api.logbook_entries(board, username, password, database)

    else:
        raise ValueError(f"Unknown board {board}")


def write_entries(output_file, entries, no_headers=False, fields=LOGBOOK_FIELDS):
    cleaned_entries = (
        {k: v for k, v in entry.items() if k in fields} for entry in entries
    )
    writer = csv.DictWriter(output_file, fieldnames=fields)
    if not no_headers:
        writer.writeheader()
    writer.writerows(cleaned_entries)


def get_login_token(board, username):
    env_var = f"{board.upper()}_PASSWORD"
    password = os.environ.get(env_var)
    if not password:
        password = getpass.getpass("Password: ")

    login_info = boardlib.api.aurora.login(board, username, password)
    return login_info["token"]


def handle_database_command(args):
    if os.path.isdir(args.database_path):
        print("boardlib: error: download path should be a file, not a folder.")
        return
    if not args.database_path.exists():
        args.database_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading database to {args.database_path}")
        boardlib.db.aurora.download_database(args.board, args.database_path)

    print(f"Synchronizing database at {args.database_path}")
    tables_and_sync_dates = boardlib.db.aurora.get_shared_syncs(args.database_path)
    for sync_result in boardlib.api.aurora.sync(
        args.board,
        tables_and_sync_dates,
        token=get_login_token(args.board, args.username),
        max_pages=args.max_sync_pages,
    ):
        row_counts = boardlib.db.aurora.sync_shared_tables(
            args.database_path, sync_result
        )
        for table_name, row_count in row_counts.items():
            print(f"Synchronized {row_count} rows in {table_name}")


def handle_logbook_command(args):
    token = get_login_token(args.board, args.username)
    entries = boardlib.api.aurora.logbook_entries(args.board, token, args.database_path)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            write_entries(
                output_file,
                entries.to_dict(orient="records"),
                args.no_headers,
                fields=LOGBOOK_FIELDS,
            )
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        write_entries(
            sys.stdout,
            entries.to_dict(orient="records"),
            args.no_headers,
            fields=LOGBOOK_FIELDS,
        )


def add_database_parser(subparsers):
    database_parser = subparsers.add_parser(
        "database", help="Download and sync the database"
    )
    database_parser.add_argument(
        "board",
        help="Board name",
        choices=sorted(boardlib.api.aurora.HOST_BASES.keys()),
    )
    database_parser.add_argument(
        "database_path",
        help=(
            "Path for the database file. "
            "If the file does not exist, the database will be downloaded to the given path and synchronized. "
            "If it does exist, the database will just be synchronized",
        ),
        type=pathlib.Path,
    )
    database_parser.add_argument("-u", "--username", help="Username", required=True)
    database_parser.add_argument(
        "-m",
        "--max-sync-pages",
        help=("Maximum number of times to call the sync API. Defaults to 100.",),
        type=int,
        default=boardlib.api.aurora.DEFAULT_MAX_SYNC_PAGES,
    )
    database_parser.set_defaults(func=handle_database_command)


def add_logbook_parser(subparsers):
    logbook_parser = subparsers.add_parser(
        "logbook", help="Download full logbook entries (ascents and bids) to CSV"
    )
    logbook_parser.add_argument(
        "board",
        help="Board name",
        choices=sorted(
            boardlib.api.moon.BOARD_IDS.keys() | boardlib.api.aurora.HOST_BASES.keys()
        ),
    )
    logbook_parser.add_argument(
        "database_path",
        help=(
            "Path for the database file. Run the 'database' command first to download the database. ",
        ),
        type=pathlib.Path,
    )
    logbook_parser.add_argument("-u", "--username", help="Username", required=True)
    logbook_parser.add_argument("-o", "--output", help="Output file", required=False)
    logbook_parser.add_argument(
        "--no-headers", help="Don't write headers", action="store_true", required=False
    )
    logbook_parser.set_defaults(func=handle_logbook_command)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_logbook_parser(subparsers)
    add_database_parser(subparsers)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
