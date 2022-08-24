#!/usr/bin/env just --justfile

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
    journalctl -b 5 -o short-iso | {{venv}}/bin/loga -s correlators/sample.toml -
