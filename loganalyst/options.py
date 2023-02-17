from pathlib import Path
from typing import Optional

from tap import Tap


class CLIOptions(Tap):
    correlation_file: Path  # correlation rules to use
    logfile: Path  # (possibly gzipped) log file
    extra: bool = False  # show extra log lines (not matched by iso_regex)
    summary: bool = False  # show summary
    nolog: bool = False  # don't show log
    max: bool = False  # show max durations
    begin: Optional[str] = None  # start from a date
    end: Optional[str] = None  # stop to a date

    def configure(self) -> None:
        self.add_argument("correlation_file", metavar="TOML_FILE", type=str)
        self.add_argument("logfile", metavar="LOG_FILE", type=str)
        self.add_argument(
            "--extra",
        )
        self.add_argument(
            "--summary",
        )
        self.add_argument(
            "--nolog",
        )
        self.add_argument("-b", "--begin", metavar="DATE", type=str)
        self.add_argument("-e", "--end", metavar="DATE", type=str)
