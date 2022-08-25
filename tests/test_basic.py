from loganalyst.cli import run
from loganalyst.options import CLIOptions
import pytest


def test_args():
    args = CLIOptions().parse_args(["tests/basic.toml", "tests/basic.log", "--summary", "--max"])
    run(args)
