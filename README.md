# Log analyst

## Features

- parse log files
- filters by date / timestamps
- correlates log lines (start and end of some processing)
   - show total duration
- friendly colored output
- able to output short summaries
- supports gzipped files

## Usage

For instance, with systemd logs:

```
journalctl -b 5 -o short-iso | loga -s correlators/sample.toml -
```

## Sample correlation


*Note*: the "loganalyst" section is a configuration, which is optional, use only in case overriding values is needed.

Use the documented correlation file in [correlators/sample.toml](https://github.com/fdev31/loganalyst/blob/main/correlators/sample.toml). You can also [download the file](https://raw.githubusercontent.com/fdev31/loganalyst/main/correlators/sample.toml).
