# Log analyst

## Features

- parse log files
- filters by date / timestamps
- correlates log lines (start and end of some processing)
   - show total duration
- friendly colored output
- able to output short summaries
- "folding" lines
   - keeps lines not matching an iso timestamp attached to the matching ones
- supports gzipped files

## Usage

```
usage: loga [-h] [--extra | --no-extra] [-s] [-n] [-max] [-f F] [-t T] TOML_FILE LOG_FILE

Parse some logs.

positional arguments:
  TOML_FILE            correlation rules to use
  LOG_FILE             (possibly gzipped) log file

options:
  -h, --help           show this help message and exit
  --extra, --no-extra  show extra log lines (not matched by iso_regex) (default: False)
  -s                   show summary (default: False)
  -n                   don't show log (default: False)
  -max                 show max durations (default: False)
  -f F                 start from a date
  -t T                 stop to a date
```

For instance, with systemd logs:

```
journalctl -b 5 -o short-iso | loga -s correlators/sample.toml -
```

## Sample correlation


*Note*: the "loganalyst" section is a configuration, which is optional, use only in case overriding values is needed.

Use the documented correlation file in [correlators/sample.toml](https://github.com/fdev31/loganalyst/blob/main/correlators/sample.toml). You can also [download the file](https://raw.githubusercontent.com/fdev31/loganalyst/main/correlators/sample.toml).
