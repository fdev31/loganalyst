#!/usr/bin/env just --justfile
# mostly for devs: quick tests

venv := ".tox/venv"
src := "loganalyst"

default:
    @just --list

fix:
    scripts/install_editable {{venv}}

typing: fix
    {{venv}}/bin/mypy  {{src}}

style: fix
    {{venv}}/bin/isort {{src}}
    {{venv}}/bin/black {{src}}

coverage: fix
    {{venv}}/bin/vulture {{src}}

test: fix
    journalctl -b 5 -o short-iso | {{venv}}/bin/loga --max -s -x correlators/sample.toml -
