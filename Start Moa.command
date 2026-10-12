#!/bin/zsh
MOA_ROOT="${0:A:h}"
cd "$MOA_ROOT"
exec "$MOA_ROOT/.venv/bin/python" -m api.run
