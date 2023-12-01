# BoardLib

Utilities for interacting with (undocumented) climbing board APIs. Currently, the primary use case for this library is to retreive your logbook entries across multiple climbing boards in a unified format. There are also some APIs which could also be used for retrieving climb data, rankings, etc. Contributions are welcome for filling out additional API calls and use cases.

## Installation

`pip install boardlib`

## Usage

To download your logbook entries for a given board:

`boardlib <board_name> --username=<username> --output=<output_file_name>.csv --grade-type="hueco"`

This outputs a CSV file with the following fields:

```json
["board", "angle", "name", "date", "grade", "tries"]
```

For example, the command

`boardlib moon2017 --username="Luke EF" --output="moon2017.csv" --grade-type="hueco"`

would output a file named `moon2017.csv` with the following contents:

```
board,angle,name,date,grade,tries
moon2017,40,C3PO,2021-07-13,V5,1
moon2017,40,LITTLE BLACK SUBMARINE,2021-07-13,V5,2
moon2017,40,MOUNTAIN GOAT HARD,2021-07-13,V5,1
...
```

See `boardlib --help` for a full list of supported board names and feature flags.

## Supported Boards

Currently all [Aurora Climbing](https://auroraclimbing.com/) based boards (Kilter, Tension, etc.) and all variations of the [Moonboard](https://moonboard.com/) should be supported.

## Bugs and Feature Requests

Please create an issue in the [issue tracker](https://github.com/lemeryfertitta/BoardLib/issues) to report bugs or request additional features. Contributions are welcome and appreciated.
