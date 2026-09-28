#!/usr/bin/env python3
"""Simple script to get value from ii-wrapper's config file.

Fetched value is printed on STDOUT. Only one value can be fetched at the time.
Prints "parser-error" on STDOUT on exception eg. config file cannot be parsed,
section or option not found etc. While not user friendly, this is in order to
simplify check for errors.
Exception are printed on STDERR.

Crimes Against Software Engineering

2026/Sep/28 @ Zdenek Styblik <stybla@turnovfree.net>
"""
import argparse
import sys
import tomllib
from typing import Any
from typing import Dict

SERVICE = "config_lookup"


def fetch_value(
    config_file: str,
    config_section: str,
    config_option: str,
) -> Any:
    """Fetch value from config file and return it."""
    data = load_config_file(config_file)
    ptr = data
    chunks = config_section.split(".")
    sub_search = False
    idx = 0
    for chunk in chunks:
        idx += 1
        if chunk == "*" and idx == len(chunks):
            sub_search = True
            break

        if chunk not in ptr:
            raise KeyError(
                "part '{}' of config section not found".format(chunk)
            )

        ptr = ptr[chunk]

    if sub_search:
        # NOTE(zstyblik): hack in order to be able to fetch list of channels.
        # Let's hope it won't be needed for long ... (10 years later)
        collected = [
            data[config_option]
            for data in ptr.values()
            if config_option in data
        ]
        value = ",".join(collected)
    else:
        if config_option not in ptr:
            raise KeyError(
                "config option '{}' not found under '{}'".format(
                    config_option,
                    config_section,
                )
            )

        value = ptr[config_option]

    return value


def load_config_file(fname: str) -> Dict[Any, Any]:
    """Read TOML file and return its contents as a dictionary."""
    with open(fname, "rb") as fhandle:
        data = tomllib.load(fhandle)

    return data


def main():
    """Parse CLI args, load config file and return desired value from it."""
    args = parse_args()
    try:
        value = fetch_value(
            args.config_file,
            args.config_section,
            args.config_option,
        )
        print("{}".format(value))
    except Exception as exc:
        print("{}".format(exc), file=sys.stderr)
        print("parser-error")
        raise


def parse_args() -> argparse.Namespace:
    """Return parsed CLI args."""
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description="Fetch value from config file and print it on STDOUT.",
        epilog="{:s}, Unlicense".format(SERVICE),
    )
    parser.add_argument(
        "--config-file",
        "-f",
        required=True,
        type=str,
        help="ii-wrapper's config file to parse.",
    )
    parser.add_argument(
        "--config-section",
        "-s",
        required=True,
        type=str,
        help="Name of section in config file.",
    )
    parser.add_argument(
        "--config-option",
        "-o",
        required=True,
        type=str,
        help="Option to fetch from given section in config file.",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
