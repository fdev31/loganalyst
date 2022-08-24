#!/bin/env python

import argparse
import gzip
import re
import sys
from typing import Iterable

import tomli
from dateutil.parser import isoparse, parse
from termcolor import colored

from .models import Correlator, LogLine
from .utils import timeColor

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
        help="show extra log lines (not matched by iso_regex)",
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
        "timezone": "CEST",
        "ts_lines_prefix": "",
        "ts_lines_suffix": "",
        "iso_regex": "(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+|\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d+|\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d+)(\+\d+)?",
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
            ts = isoparse("".join(m.groups()))

            if start is not None:
                if start > ts:
                    continue
            if end is not None:
                if end < ts:
                    finished = True
                    continue
            entry = LogLine(
                prefix=line[: m.end()].rstrip(),
                timestamp=ts,
                text=line[m.end():].rstrip(),
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
            summary = cor.longest.pretty if cor.longest else 'None found!'
            print(f"Longest {cor.description}: {summary}")
        print("***")
    if loglines:
        print("Log period: %s - %s" % (loglines[0].localtime, loglines[-1].localtime))
