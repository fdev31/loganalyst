#!/usr/bin/env just --justfile
# mostly for devs: quick tests

venv := ".tox/venv"
src := "loganalyst"

default:
    @just --list

do: typing style coverage test

fix:
    scripts/install_editable {{venv}}

typing: fix
    {{venv}}/bin/mypy  {{src}}

style: fix
    {{venv}}/bin/isort .
    {{venv}}/bin/black .

coverage: fix
    {{venv}}/bin/vulture {{src}}

test: fix
    journalctl -b 5 -o short-iso | {{venv}}/bin/loga --max --summary --extra correlators/sample.toml -
    {{venv}}/bin/pytest tests/

shorttest: fix
    journalctl -b 5 -o short-iso | {{venv}}/bin/loga --max --summary --nolog correlators/sample.toml -
    {{venv}}/bin/pytest tests/

help: fix
    {{venv}}/bin/loga -h
