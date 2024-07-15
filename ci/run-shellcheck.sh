#!/usr/bin/env bash
set -e
set -u

find . \( -name '*.sh' -or -name iibot-ng \) -print0 | \
    xargs -0 -- shellcheck
