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
usage: loga [--extra] [--summary] [--nolog] [--max] [-b DATE] [-e DATE] [-h]
            TOML_FILE LOG_FILE

positional arguments:
  TOML_FILE             (Path, default=None) correlation rules to use
  LOG_FILE              (Path, default=None) (possibly gzipped) log file

options:
  --extra               (bool, default=False) show extra log lines (not
                        matched by iso_regex)
  --summary             (bool, default=False) show summary
  --nolog               (bool, default=False) don't show log
  --max                 (bool, default=False) show max durations
  -b DATE, --begin DATE
                        (Optional[str], default=None) start from a date
  -e DATE, --end DATE   (Optional[str], default=None) stop to a date
  -h, --help            show this help message and exit
```

For instance, with systemd logs:

```
journalctl -b 5 -o short-iso | loga --summary --nolog correlators/sample.toml -
```

## Sample correlation


*Note*: the "loganalyst" section is a configuration, which is optional, use only in case overriding values is needed.

Use the documented correlation file in [correlators/sample.toml](https://github.com/fdev31/loganalyst/blob/main/correlators/sample.toml). You can also [download the file](https://raw.githubusercontent.com/fdev31/loganalyst/main/correlators/sample.toml).
