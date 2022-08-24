venv := ".tox/venv"
src := "loganalyst"

default:
    @just --list

clean:
    rm -fr {{venv}}/lib/python3.10/site-packages/loganalyst

typing: clean
    {{venv}}/bin/mypy  {{src}}

style: clean
    {{venv}}/bin/isort {{src}}
    {{venv}}/bin/black {{src}}

coverage: clean
    {{venv}}/bin/vulture {{src}}
