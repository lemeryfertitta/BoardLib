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

`boardlib logbook <board_name> --username=<username> --output=<output_file_name>.csv --grade-type="hueco"`

This outputs a CSV file with the following fields:

```json
["board", "angle", "name", "date", "grade", "tries", "is_mirror"]
```

For example, the command

`boardlib moon2017 --username="Luke EF" --output="moon2017.csv" --grade-type="hueco"`

would output a file named `moon2017.csv` with the following contents:

```
board,angle,name,date,grade,tries, is_mirror
moon2017,40,C3PO,2021-07-13,V5,1, False
moon2017,40,LITTLE BLACK SUBMARINE,2021-07-13,V5,2, False
moon2017,40,MOUNTAIN GOAT HARD,2021-07-13,V5,1, False
...
```

See `boardlib --help` for a full list of supported board names and feature flags.

#### Supported Boards 🛹

Currently all [Aurora Climbing](https://auroraclimbing.com/) based boards (Kilter, Tension, etc.) and all variations of the [Moonboard](https://moonboard.com/) should be supported.

## Bugs 🐞 and Feature Requests 🗒️

Please create an issue in the [issue tracker](https://github.com/lemeryfertitta/BoardLib/issues) to report bugs or request additional features. Contributions are welcome and appreciated.
