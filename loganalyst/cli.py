#!/bin/env python

import argparse
import gzip
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Generator, Iterable, Match, Optional, Sequence, cast

import tomli
from dateutil.parser import isoparse, parse
from pydantic import BaseModel
from termcolor import colored

CEST = timezone(timedelta(hours=2))


class LogLine(BaseModel):
    timestamp: datetime
    prefix: str
    text: str
    extra: list[str] = []

    @property
    def localtime(self) -> datetime:
        return self.timestamp.astimezone(CEST)

    def __hash__(self) -> int:
        return hash(self.timestamp.isoformat())


def timeColor(sec: float) -> str:
    t = "%7.03f" % sec
    if sec < 0.4:
        return colored(t, "grey", "on_green")
    if sec < 1.0:
        return colored(t, "white", "on_blue")
    if sec < 5.0:
        return colored(t, "red", "on_yellow")
    return colored(t, "red", "on_yellow", attrs=["bold"])


class Correlation:
    def __init__(self, start: LogLine, end: LogLine):
        self.start = start
        self.end = end

    start: LogLine
    end: LogLine

    @property
    def duration(self) -> float:
        return (self.end.timestamp - self.start.timestamp).total_seconds()

    @property
    def pretty(self) -> str:
        return "%s - %s %s" % (
            timeColor(self.duration),
            self.start.text,
            colored("@ %s" % self.start.localtime, "blue"),
        )


def extractPattern(re_match: Match[str]) -> Sequence[str] | dict[str, str]:
    d = re_match.groupdict()
    if d:
        return d
    return re_match.groups()


class Correlator:
    lookup: dict[LogLine, Correlation] = {}

    def __init__(self, description: str, start_pat: str, end_pat: str):
        self.description = description
        self.start = re.compile(".*" + start_pat)
        self.end = re.compile(".*" + end_pat)
        self.items: dict[Sequence[str] | dict[str, str], LogLine | Correlation] = {}
        self.done_items: dict[Sequence[str] | dict[str, str], Correlation] = {}
        self.longest: Optional[Correlation] = None
        self.verbose = False

    def ingest(self, log: LogLine) -> None:
        m = self.start.match(log.text)
        if m:  # store logline if start matches
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
                    if isinstance(self.items[pat], LogLine):
                        if self.verbose:
                            print(f"END of {self.description} found: {pat} => {log.text}")
                        ll = cast(LogLine, self.items[pat])
                        c = Correlation(start=ll, end=log)
                        # correlation done, free the pattern space
                        Correlator.lookup[ll] = c
                        self.done_items[pat] = c
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
            print("Summary for %s:" % self.description)
            for cor in sorted(self.done_items.values(), key=lambda x: x.start.timestamp):
                print(cor.pretty)
            for cor in sorted(self.active_items, key=lambda x: x.start.timestamp):
                print(cor.pretty)


correlation_rules: list[Correlator] = []


def run() -> None:
    loglines = []
    parser = argparse.ArgumentParser(description="Parse some logs.")
    parser.add_argument("correlation_file", metavar="TOML_FILE", type=str, help="correlation rules to use")
    parser.add_argument("logfile", metavar="LOG_FILE", type=str, help="(possibly gzipped) log file")
    parser.add_argument(
        "--extra",
        default=False,
        type=bool,
        help="show extra log lines (non jsapp)",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "-s",
        default=False,
        type=bool,
        help="show summary",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "-n",
        default=False,
        type=bool,
        help="don't show log",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "-max",
        default=False,
        type=bool,
        help="show max durations",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument("-f", type=str, help="start from a date")
    parser.add_argument("-t", type=str, help="stop to a date")
    args = parser.parse_args()

    config: dict[str, str] = {
        "ts_lines_prefix": ".*",
        "ts_lines_suffix": "",
        "iso_regex": "(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d)",
    }

    for k, o in tomli.load(open(args.correlation_file, "rb")).items():
        if k == "loganalyst":  # configuration section
            config.update(o)
        else:  # rule
            c = Correlator(k, o["start"], o["end"])
            if o.get("debug"):
                c.verbose = True
            correlation_rules.append(c)

    if args.logfile == "-":
        source: Iterable[str] = sys.stdin.readlines()
    elif args.logfile.endswith("z"):
        source = gzip.open(args.logfile, "rt", encoding="utf-8", errors="replace")
    else:
        source = open(args.logfile, "rt", encoding="utf-8", errors="replace")

    refDateRe = re.compile(config["ts_lines_prefix"] + config["iso_regex"] + config["ts_lines_suffix"])
    start = parse(args.f + " +00 (%s)" % config["timezone"]) if args.f else None
    end = parse(args.t + " +00 (%s)" % config["timezone"]) if args.t else None
    finished = False

    for line in source:
        if finished:
            break
        # iso date is MUCH faster to parse, hence using an ISO ts
        m = refDateRe.match(line)
        if m:
            ts = isoparse(m.groups()[1])

            if start is not None:
                if start > ts:
                    continue
            if end is not None:
                if end < ts:
                    finished = True
                    continue
            entry = LogLine(
                prefix=line[: m.end() + 1].rstrip(),
                timestamp=ts,
                text=line[m.end() + 1 :].rstrip(),
            )
            loglines.append(entry)
            for cor in correlation_rules:
                cor.ingest(entry)
        elif loglines:
            loglines[-1].extra.append(line)

    for log in loglines:
        if not args.n:
            pfx = ""
            if Correlator.lookup.get(log):
                core = Correlator.lookup[log]
                pfx = timeColor(core.duration)
            print(pfx, log.text, colored(str(log.timestamp), "blue"))
        if args.extra:
            for e in log.extra:
                print(f"  ... {e}")
    print("***")
    if args.s:
        for cor in correlation_rules:
            cor.summary()
        print("***")
    if args.max:
        for cor in correlation_rules:
            print(f"Longest {cor.description}", end=": ")
            if cor.longest:
                print(cor.longest.duration, cor.longest.pretty)
            else:
                print("NONE FOUND")
        print("***")
    if loglines:
        print("Log period: %s - %s" % (loglines[0].localtime, loglines[-1].localtime))
