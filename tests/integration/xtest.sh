#!/bin/bash
set -e
python -m pytest tests/integration --run-engine "$@"
