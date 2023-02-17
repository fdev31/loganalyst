from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, Generator, Optional, Sequence, Union, cast, Any

from termcolor import colored

from .utils import extractPattern, timeColor

CEST = timezone(timedelta(hours=2))

class LogLine:
    timestamp: datetime
    prefix: str
    text: str
    extra: list[str]

    def __init__(self, prefix: str, timestamp: datetime, text: str):
        self.extra = []
        self.text = text
        self.timestamp = timestamp
        self.prefix = prefix

    @property
    def localtime(self) -> datetime:
        return self.timestamp.astimezone(CEST)

    def __hash__(self) -> int:
        return hash(self.timestamp.isoformat())

def lineFactory(name: str, options: dict[str,Any]) -> None:
    c : Correlator|CheckPointEvent|None = None

    if options.get('start'):
        c = Correlator(name, options["start"], options["end"])
        correlation_rules.append(c)
    else:
        c = CheckPointEvent(name, options["event"])
        c.unique = options.get("unique", c.unique)
        event_rules.append(c)
    c.verbose = options.get("debug", c.verbose)

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


def extractExtras(startLine: str, extraLines: list[str]) -> list[str]:
    extras = []
    brackets = (
        ("[", "]"),
        ("{", "}"),
    )
    for oB, cB in brackets:
        diff = startLine.count(oB) - startLine.count(cB)
        if diff > 0:
            for e in extraLines:
                diff += e.count(oB)
                diff -= e.count(cB)
                extras.append(e[:-1])
                if diff <= 0:
                    break
    return extras


class CheckPointEvent:
    lookup: dict[LogLine, CheckPointEvent] = {}

    def __init__(self, description: str, event_pat: str):
        self.description = description
        self.event = re.compile(".*" + event_pat)
        self.verbose = False
        self.count = 0
        self.unique: bool = False
        self.instances: list[LogLine] = []

    def ingest(self, log: LogLine) -> None:
        m = self.event.match(log.text)
        if m:  # store logline if start matches
            if self.unique and self.instances and log.text == self.instances[-1].text:
                return
            self.count += 1
            if self.verbose:
                print(f'Event "{self.description}" found: {log.text}')
            self.lookup[log] = self
            self.instances.append(log)

    def summary(self) -> None:
        if self.instances:
            print(
                colored(
                    "Summary for %s (occurred %d times):" % (self.description, self.count),
                    "white",
                    "on_blue",
                )
            )
            for log in self.instances:
                print(
                    log.text,
                    colored("@ %s" % log.timestamp, "blue"),
                )
                for extra in extractExtras(log.text, log.extra):
                    print(" ... " + extra)


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

event_rules: list[CheckPointEvent] = []
correlation_rules: list[Correlator] = []
