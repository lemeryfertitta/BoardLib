import argparse
import csv
import getpass
import os
import pathlib
import sys

import boardlib.api.aurora
import boardlib.api.moon
import boardlib.db.aurora


LOGBOOK_FIELDS = ("board", "angle", "climb_name", "date", "logged_grade", "displayed_grade", "difficulty", "tries", "is_mirror", "sessions_count", "tries_total", "is_repeat", "is_ascent", "comment")


def logbook_entries(board, username, password, grade_type="font", database=None):
    api = (
        boardlib.api.moon
        if board.startswith("moon")
        else boardlib.api.aurora
        if board in boardlib.api.aurora.HOST_BASES
        else None
    )
    if api:
        yield from api.logbook_entries(board, username, password, grade_type, database)

    else:
        raise ValueError(f"Unknown board {board}")



def write_entries(output_file, entries, no_headers=False, fields=LOGBOOK_FIELDS):
    writer = csv.DictWriter(output_file, fieldnames=fields)
    if not no_headers:
        writer.writeheader()
    writer.writerows(entries)


def handle_database_command(args):
    if not args.database_path.exists():
        args.database_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading database to {args.database_path}")
        boardlib.db.aurora.download_database(args.board, args.database_path)

    print(f"Synchronizing database at {args.database_path}")
    row_counts = boardlib.db.aurora.sync_shared_tables(args.board, args.database_path)
    for table_name, row_count in row_counts.items():
        print(f"Synchronized {row_count} rows in {table_name}")


def handle_logbook_command(args):
    env_var = f"{args.board.upper()}_PASSWORD"
    password = os.environ.get(env_var)
    if not password:
        password = getpass.getpass("Password: ")
    entries = boardlib.api.aurora.logbook_entries(args.board, args.username, password, args.grade_type, args.database)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            write_entries(output_file, entries.to_dict(orient="records"), args.no_headers, fields=LOGBOOK_FIELDS)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        write_entries(sys.stdout, entries.to_dict(orient="records"), args.no_headers, fields=LOGBOOK_FIELDS)


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
    logbook_parser.add_argument("-u", "--username", help="Username", required=True)
    logbook_parser.add_argument("-o", "--output", help="Output file", required=False)
    logbook_parser.add_argument(
        "--no-headers", help="Don't write headers", action="store_true", required=False
    )
    logbook_parser.add_argument(
        "-g",
        "--grade-type",
        help="Grade type",
        choices=("font", "hueco"),
        default="font",
        required=False,
    )
    logbook_parser.add_argument(
        "-d",
        "--database",
        help="Path to the local database (optional). Using a local database will significantly speed up the logbook generation and is required to retrieve 'displayed_grade' and 'difficulty'. Create a local database with the 'database' command.",
        type=pathlib.Path,
        required=False,
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
