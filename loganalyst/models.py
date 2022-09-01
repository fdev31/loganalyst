from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, Generator, Optional, Sequence, Union, cast

from termcolor import colored

from .utils import extractPattern, timeColor

CEST = timezone(timedelta(hours=2))


class LogLine:
    timestamp: datetime
    prefix: str
    text: str
    extra: list[str] = []

    def __init__(self, prefix: str, timestamp: datetime, text: str):
        self.text = text
        self.timestamp = timestamp
        self.prefix = prefix

    @property
    def localtime(self) -> datetime:
        return self.timestamp.astimezone(CEST)

    def __hash__(self) -> int:
        return hash(self.timestamp.isoformat())


class Correlation:
    def __init__(self, start: LogLine, end: LogLine, source: Correlator):
        self.start = start
        self.end = end
        self.src = source

    start: LogLine
    end: LogLine

    @property
    def duration(self) -> float:
        return (self.end.timestamp - self.start.timestamp).total_seconds()

    @property
    def pretty(self) -> str:
        return "%s %s %s" % (
            timeColor(self.duration),
            self.start.text,
            colored("@ %s" % self.start.localtime, "blue"),
        )


class Correlator:
    lookup: dict[LogLine, Correlation] = {}

    def __init__(self, description: str, start_pat: str, end_pat: str):
        self.description = description
        self.start = re.compile(".*" + start_pat)
        self.end = re.compile(".*" + end_pat)
        self.items: Dict[Union[Sequence[str], Dict[str, str]], Union[LogLine, Correlation]] = {}
        self.done_items: list[Correlation] = []
        self.longest: Optional[Correlation] = None
        self.verbose = False
        self.count_started = 0
        self.count_done = 0
        self.ongoing_correlations = 0
        self.max_ongoing = 0

    def ingest(self, log: LogLine) -> None:
        m = self.start.match(log.text)
        if m:  # store logline if start matches
            self.count_started += 1
            self.ongoing_correlations += 1
            self.max_ongoing = max(self.ongoing_correlations, self.max_ongoing)
            pat = extractPattern(m)
            if self.verbose:
                print(f'START of "{self.description}" found: {pat} => {log.text}')
            self.items[pat] = log
        else:
            m = self.end.match(log.text)
            if m:  # store the correlation
                pat = extractPattern(m)
                if pat not in self.items:
                    sys.stderr.write(f'Warning: No matching start [{pat}] of "{self.description}" on {log.text}\n')
                else:
                    self.count_done += 1
                    self.ongoing_correlations -= 1
                    if isinstance(self.items[pat], LogLine):
                        if self.verbose:
                            print(f"END of {self.description} found: {pat} => {log.text}")
                        start = cast(LogLine, self.items[pat])
                        c = Correlation(start=start, end=log, source=self)
                        # correlation done, free the pattern space
                        Correlator.lookup[start] = c
                        self.done_items.append(c)
                        del self.items[pat]

                        if self.longest is None:
                            self.longest = c
                        else:
                            if self.longest.duration < c.duration:
                                self.longest = c
                    else:
                        sys.stderr.write(
                            f"Warning: Conflict found parsing {self.description}, pattern '{pat}' exists (dup)\n"
                        )

    @property
    def active_items(self) -> Generator[Correlation, None, None]:
        return (item for item in self.items.values() if isinstance(item, Correlation))

    def summary(self) -> None:
        if self.items or self.done_items:
            print(
                colored(
                    "Summary for %s (%d/%d, max running: %d):"
                    % (self.description, self.count_done, self.count_started, self.max_ongoing),
                    "white",
                    "on_blue",
                )
            )
            for cor in sorted(self.done_items, key=lambda x: x.start.timestamp):
                print(cor.pretty)
            for cor in sorted(self.active_items, key=lambda x: x.start.timestamp):
                print(cor.pretty)
