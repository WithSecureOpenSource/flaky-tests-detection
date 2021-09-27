#!/bin/sh

. .venv/bin/activate
flaky "$*"
deactivate
