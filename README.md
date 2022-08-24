# Log analyst

## Features

- parse log files
- filters by date / timestamps
- correlates log lines (start and end of some processing)
   - show total duration
- friendly colored output
- able to output short summaries

## Sample correlation

Note: the "loganalyst" section is a configuration, which is optional, use only in case overriding values is needed.

```ini
[loganalyst]
# patterns required before & after the ISO date to consider the log line valid
ts_lines_prefix = ".*"
ts_lines_suffix = ""
# What will be searched for in each line to extract the ISO date
iso_regex = '(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d)'
# timezone used in dates input by the user
timezone = "CEST"

["Basic pattern-less correlation"]
start = "this is the start"
end = "end over"

["Correlation using a pattern"]
start = 'starting request (\d+)'
end = 'request (\d+) ended.'
debug = true # adds some extra verbosity, useful when making new rules

["systemd units start"]
start = 'systemd\[\d+\]: Starting (.*?)[.]+'
end = 'systemd\[\d+\]: Started (.*)\.$'

["systemd units sockets"]
start = 'systemd\[\d+\]: Listening on (.*?)[.]+'
end = 'systemd\[\d+\]: Closed (.*)\.$'

["systemd units duration"]
start = 'systemd\[\d+\]: Started (.*?) ?[.]+$'
end = 'systemd\[\d+\]: Stopped (.*)\.$'
```
