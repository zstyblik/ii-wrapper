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
from typing import List

SERVICE = "config_lookup"


def config_check(config_file: str) -> (int, List[str]):
    """Perform basic configuration check and report errors."""
    retcode = 0
    errors = []
    try:
        data = load_config_file(config_file)
    except Exception as exc:
        retcode = 1
        error = "Failed to parse config file '{}': {}".format(config_file, exc)
        errors.append(error)
        return retcode, errors

    if "ii" not in data:
        retcode = 1
        error = "Key 'ii' not found in config file '{}'".format(config_file)
        errors.append(error)
        return retcode, errors

    if "settings" not in data["ii"]:
        retcode = 1
        error = "Key 'ii.settings' not found in config file '{}'".format(
            config_file
        )
        errors.append(error)
        return retcode, errors

    settings = data["ii"]["settings"]
    if "server" not in settings or not settings["server"]:
        retcode = 1
        errors.append("Config option 'ii.settings.server' must be set")

    if "ircdir" not in settings or not settings["ircdir"]:
        retcode = 1
        errors.append("Config option 'ii.settings.ircdir' must be set")

    if "nickname" not in settings or not settings["nickname"]:
        retcode = 1
        errors.append("Config option 'ii.settings.nickname' must be set")

    return retcode, errors


def config_lookup(
    config_file: str,
    config_section: str,
    config_option: str,
) -> None:
    """Lookup value in configuration file and print it on STDOUT.

    On error, prints "parser-error" on STDOUT, errors on STDERR and raises
    exception.
    """
    try:
        value = fetch_value(config_file, config_section, config_option)
        print("{}".format(value))
    except Exception as exc:
        print("{}".format(exc), file=sys.stderr)
        print("parser-error")
        raise


def fetch_value(
    config_file: str,
    config_section: str,
    config_option: str,
) -> Any:
    """Fetch value from config file and return it."""
    if not config_section:
        raise KeyError("config section to lookup must be given")

    if not config_option:
        raise ValueError("config option to lookup must be given")

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
    if args.config_check:
        retcode, errors = config_check(args.config_file)
        for error in errors:
            print(error, file=sys.stderr)

        sys.exit(retcode)
    else:
        config_lookup(args.config_file, args.config_section, args.config_option)


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
        default="",
        type=str,
        help="Name of section in config file.",
    )
    parser.add_argument(
        "--config-option",
        "-o",
        default="",
        type=str,
        help="Option to fetch from given section in config file.",
    )
    parser.add_argument(
        "--check",
        dest="config_check",
        action="store_true",
        default=False,
        help="Check configuration file. Other arguments will be ignored.",
    )
    args = parser.parse_args()
    if not args.config_check and (
        not args.config_section or not args.config_option
    ):
        parser.error(
            "Config section and option are required except for config check."
        )

    return args


if __name__ == "__main__":
    main()
