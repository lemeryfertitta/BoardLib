# BoardLib 🧗‍♀️

Utilities for interacting with (undocumented) climbing board APIs.

## Installation 🦺

`python3 -m pip install boardlib`

## Usage ⌨️

### Databases 💾

To download the climb database for a given board:

`boardlib database <board_name> <database_path>`

This command will first download a [sqlite](https://www.sqlite.org/index.html) database file to the given path. After downloading, the database will then use the undocumented sync API to synchronize it with the latest available data. The database contains only the publicly available data. User data is not synchronized. If a database already exists as `database_path`, the command will skip the download step and only perform the synchronization.

NOTE: The Moonboard is not currently supported for the database command. Contributions are welcome.

#### Supported Boards 🛹

All [Aurora Climbing](https://auroraclimbing.com/) based boards (Kilter, Tension, etc.).

### Logbooks 📚

To download your logbook entries for a given board:

`boardlib logbook <board_name> --username=<username> --output=<output_file_name>.csv --grade-type="hueco" --database=<local_database_file>`

This outputs a CSV file with the following fields:

```json
["board", "angle", "climb_name", "date", "logged_grade", "displayed_grade", "difficulty", "tries", "is_mirror", "sessions_count", "tries_total", "is_repeat", "is_ascent", "comment"]
```

For example, the command

`boardlib tension --username="Luke EF" --output="tension.csv" --grade-type="hueco" --database="tension.db"`

would output a file named `tension.csv` with the following contents:

```
board,angle,climb_name,date,logged_grade,displayed_grade,difficulty,tries,is_mirror,sessions_count,tries_total,is_repeat,is_ascent,comment
tension,40,trash bag better,2024-06-17 16:21:23,V3,V3,16.0,3,False,1,3,False,True,
tension,40,Bumble,2024-06-17 16:28:23,V3,V3,16.0,1,True,1,1,False,True,
tension,40,sender2,2024-06-17 16:38:06,V5,V5,20.0,2,False,1,2,False,True,
...
```
When no local database is provided, displayed_grade and difficulty remain empty.
See `boardlib --help` for a full list of supported board names and feature flags.

#### Supported Boards 🛹

Currently all [Aurora Climbing](https://auroraclimbing.com/) based boards (Kilter, Tension, etc.) and all variations of the [Moonboard](https://moonboard.com/) should be supported.

## Bugs 🐞 and Feature Requests 🗒️

Please create an issue in the [issue tracker](https://github.com/lemeryfertitta/BoardLib/issues) to report bugs or request additional features. Contributions are welcome and appreciated.
