#!/bin/env python

import gzip
import os
import re
import sys
from typing import Dict, Iterable, List

import tomli
from dateutil.parser import isoparse, parse
from termcolor import colored

from .models import CheckPointEvent, Correlator, LogLine
from .models import event_rules, correlation_rules, lineFactory

from .options import CLIOptions
from .utils import timeColor

try:
    twidth = os.get_terminal_size()[0]
except OSError:
    twidth = 80

SEP = "-" * twidth


def run(args: CLIOptions) -> None:
    loglines = []

    config: Dict[str, str] = {
        "timezone": "CEST",
        "ts_lines_prefix": "",
        "ts_lines_suffix": "",
        "iso_regex": r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?((?:[+-]\d\d:?\d\d)|Z)?",
    }

    for k, o in tomli.load(open(str(args.correlation_file), "rb")).items():
        if k == "loganalyst":  # configuration section
            config.update(o)
        else:  # rule
            if o.get("enable", True):
                lineFactory(k, o)

    logfile = str(args.logfile)
    if logfile == "-":
        source: Iterable[str] = sys.stdin
    elif logfile.endswith("z"):
        source = gzip.open(logfile, "rt", encoding="utf-8", errors="replace")
    else:
        source = open(logfile, "rt", encoding="utf-8", errors="replace")

    refDateRe = re.compile(config["ts_lines_prefix"] + config["iso_regex"] + config["ts_lines_suffix"])
    if config["timezone"]:
        start = parse(f"{args.begin} +00 ({config['timezone']})") if args.begin else None
        end = parse(f"{args.end} +00 ({config['timezone']})") if args.end else None
    else:
        start = parse(args.begin) if args.begin else None
        end = parse(args.end) if args.end else None
    finished = False

    # build the data set
    for line in source:
        if finished:
            break
        # iso date is MUCH faster to parse, hence using an ISO ts
        m = refDateRe.match(line)
        if m:
            ts = isoparse("".join(x for x in m.groups() if x))

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
                text=line[m.end() :].rstrip(),
            )
            loglines.append(entry)
            for cor in correlation_rules:
                cor.ingest(entry)
            for evt in event_rules:
                evt.ingest(entry)
        elif loglines:
            loglines[-1].extra.append(line)

    # output
    for log in loglines:
        if not args.nolog:
            pfx = ""
            sfx = ""
            if Correlator.lookup.get(log):
                core = Correlator.lookup[log]
                pfx = timeColor(core.duration)
                sfx = colored(core.src.description, "yellow")
            if CheckPointEvent.lookup.get(log):
                evt = CheckPointEvent.lookup[log]
                if sfx:
                    sfx += " + " + colored(evt.description, "yellow")
                else:
                    sfx = colored(evt.description, "yellow")
            print(pfx, log.text, colored(str(log.timestamp), "blue"), sfx)
        if args.extra:
            for e in log.extra:
                print(f"  ... {e}")
    print(SEP)
    if args.summary:
        for cor in correlation_rules:
            cor.summary()
        if event_rules and correlation_rules:
            print("events:")
        for evt in event_rules:
            evt.summary()
        print(SEP)
    if args.max:
        for cor in correlation_rules:
            summary = cor.longest.pretty if cor.longest else "not found!"
            print(f'Longest "{cor.description}" is {summary}')
        print(SEP)
    if loglines:
        print("Log period: %s - %s" % (loglines[0].localtime, loglines[-1].localtime))


def cli() -> None:
    args = CLIOptions().parse_args()
    run(args)
