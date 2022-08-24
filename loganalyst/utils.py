from typing import Match, Sequence

from termcolor import colored


def extractPattern(re_match: Match[str]) -> Sequence[str] | dict[str, str]:
    d = re_match.groupdict()
    if d:
        return d
    return re_match.groups()


def timeColor(sec: float) -> str:
    t = "%7.03f" % sec
    if sec < 0.4:
        return colored(t, "grey", "on_green")
    if sec < 1.0:
        return colored(t, "white", "on_blue")
    if sec < 5.0:
        return colored(t, "red", "on_yellow")
    return colored(t, "red", "on_yellow", attrs=["bold"])
