# Log analyst

## Features

- parse log files
- filters by date / timestamps
- correlates log lines (start and end of some processing)
   - show total duration
- friendly colored output
- able to output quick summaries

## Sample correlation

```
["Basic pattern-less correlation"]
start = "this is the start"
end = "end over"

["Correlation using a pattern"]
start = "starting request (\d+)"
end = "request (\d+) ended."
debug = true # adds some extra verbosity, useful when making new rules
```
