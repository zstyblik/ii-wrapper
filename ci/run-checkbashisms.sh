#!/usr/bin/env bash
set -e
set -u

cd "$(dirname "${0}")/.."

find . \( -name '*.sh' -or -name iibot-ng \) -print0 | \
    xargs -0 -- checkbashisms --newline --force --lint --extra
