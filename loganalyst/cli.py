#!/bin/env python

import argparse
import gzip
import re
from datetime import datetime, timedelta, timezone

from dateutil.parser import isoparse, parse
from pydantic import BaseModel
from termcolor import colored

CEST = timezone(timedelta(hours=2))

HUMAN_RE = re.compile("(\d+)/(\d+)/(\d+)@(\d+):(\d+)")
ISO_RE = "(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+Z)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\dZ)|(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\dZ)"
jsDateRe = re.compile(".*JS - ." + ISO_RE)


class LogLine(BaseModel):
    timestamp: datetime
    prefix: str
    text: str
    extra: list[str] = []

    @property
    def localtime(self):
        return self.timestamp.astimezone(CEST)

    def __hash__(self):
        return self.timestamp.second


def timeColor(sec):
    t = "%7.03f" % sec
    if sec < 0.4:
        return colored(t, "grey", "on_green")
    if sec < 1.0:
        return colored(t, "white", "on_blue")
    if sec < 5.0:
        return colored(t, "red", "on_yellow")
    return colored(t, "red", "on_yellow", attrs=["bold"])


class Correlation:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    start: LogLine
    end: LogLine

    @property
    def duration(self):
        return (self.end.timestamp - self.start.timestamp).total_seconds()


class Correlator:
    lookup: dict[LogLine, Correlation] = {}

    def __init__(self, description, start_pat, end_pat):
        self.description = description
        self.start = re.compile(".*" + start_pat)
        self.end = re.compile(".*" + end_pat)
        self.items: dict[str, LogLine | Correlation] = {}

    def ingest(self, log: LogLine):
        m = self.start.match(log.text)
        if m:  # store logline if start matches
            pat = m.groups()[0]
            self.items[pat] = log
        else:
            m = self.end.match(log.text)
            if m:  # store the correlation
                pat = m.groups()[0]
                if pat not in self.items:
                    print(f"Ignoring {pat} (truncated)")
                else:
                    assert isinstance(
                        self.items[pat], LogLine
                    ), f"Conflict found for {pat}"
                    c = Correlation(start=self.items[pat], end=log)
                    Correlator.lookup[self.items[pat]] = c
                    self.items[pat] = c

    @property
    def valid_items(self):
        return (item for item in self.items.values() if isinstance(item, Correlation))

    def summary(self):
        if self.items:
            print("Summary for %s:" % self.description)
            for cor in sorted(self.valid_items, key=lambda x: x.start.timestamp):
                if isinstance(cor, Correlation):
                    print(
                        "%s - %s %s"
                        % (
                            timeColor(cor.duration),
                            cor.start.text,
                            colored("@ %s" % cor.start.localtime, "blue"),
                        )
                    )


correlations = [
    Correlator(
        "Websocket calls", "sendWS -> (\S+-\d+)", "sendWS -> onSuccess -> (\S+-\d+)"
    ),
    Correlator(
        "Downloads",
        "Request::download \(START\) -> (\S+)",
        "Request::download \(FINISHED\) -> (\S+)",
    ),
]


def run():
    loglines = []
    parser = argparse.ArgumentParser(description="Parse some logs.")
    parser.add_argument("logfile", metavar="FILE", type=str, help="gzipped log file")
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
    parser.add_argument("-f", type=str, help="start from a date")
    parser.add_argument("-t", type=str, help="stop to a date")
    args = parser.parse_args()

    start = parse(args.f + " +00 (CEST)") if args.f else None
    end = parse(args.t + " +00 (CEST)") if args.t else None

    finished = False

    for line in gzip.open(args.logfile, "rt", encoding="utf-8", errors="replace"):
        if finished:
            break
        # iso date is MUCH faster to parse, hence using an ISO ts
        m = jsDateRe.match(line)
        if m:
            ts = isoparse(m.groups()[0])

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
            for cor in correlations:
                cor.ingest(entry)
        elif loglines:
            loglines[-1].extra.append(line)

    for log in loglines:
        if not args.n:
            pfx = ""
            if Correlator.lookup.get(log):
                c = Correlator.lookup.get(log)
                pfx = timeColor(c.duration)
            print(pfx, log.text, colored(log.timestamp, "blue"))
        if args.extra:
            for e in log.extra:
                print(f"  ... {e}")
    print("***")
    if args.s:
        for cor in correlations:
            cor.summary()
        print("***")
    if loglines:
        print("Log period: %s - %s" % (loglines[0].localtime, loglines[-1].localtime))