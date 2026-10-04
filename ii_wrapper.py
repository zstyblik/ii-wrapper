#!/usr/bin/env python3
"""Simple script to build ii command from ii-wrapper's config file.

Crimes Against Software Engineering

2026/Sep/28 @ Zdenek Styblik <stybla@turnovfree.net>
"""
import argparse
import os
import shlex
import sys
import tomllib
from dataclasses import dataclass
from typing import Any
from typing import Dict

DEFAULT_II_FPATH = "/usr/bin/ii"
SERVICE = "ii_wrapper"


@dataclass
class IICommand:
    """Class holds all the necessary information for command to be executed."""

    env: dict
    ii_path: str
    arg0: str
    args: dict


def build_command(cfg: Dict[Any, Any], ii_path: str) -> IICommand:
    """Build ii command based on config file and return it."""
    if "ii" not in cfg:
        raise KeyError("ii key not found in config")

    if "settings" not in cfg["ii"]:
        raise KeyError("ii.settings key not found in config")

    ii_settings = cfg["ii"]["settings"]
    if "server" not in ii_settings:
        raise KeyError("ii.settings.server not found in config file")

    if not ii_settings["server"]:
        raise ValueError("ii.settings.server must not be empty")

    new_env = {}
    cmd_args = {
        "-s": None,
        "-p": None,
        "-u": None,
        "-i": None,
        "-n": None,
        "-f": None,
        "-k": None,
    }
    cmd_args["-s"] = get_option(ii_settings, "server")
    # NOTE: has default
    cmd_args["-p"] = get_option(ii_settings, "port")
    # NOTE: optional
    cmd_args["-u"] = get_option(ii_settings, "sockname")
    # NOTE: has default
    cmd_args["-i"] = get_option(ii_settings, "ircdir")
    # NOTE: has default
    cmd_args["-n"] = get_option(ii_settings, "nickname")
    # NOTE: optional
    cmd_args["-f"] = get_option(ii_settings, "realname")
    # NOTE: optional
    if "server_password" in ii_settings and ii_settings["server_password"]:
        # NOTE(zstyblik): if server_password is set, then signal it can be read
        # in IPASS env variable. Also, put password into ENV variable.
        cmd_args["-k"] = "IIPASS"
        new_env["IIPASS"] = get_option(ii_settings, "server_password")

    cmd_args_clean = {
        key: shlex.quote("{}".format(value))
        for key, value in cmd_args.items()
        if value
    }
    return IICommand(
        env=new_env,
        ii_path=ii_path,
        arg0=os.path.basename(ii_path),
        args=cmd_args_clean,
    )


def exec_command(cmd: IICommand) -> None:
    """Execs and replaces itself with given command."""
    try:
        new_environment = os.environ.copy()
        for env_key, env_value in cmd.env.items():
            new_environment[env_key] = env_value

        args = [cmd.arg0]
        for key, value in cmd.args.items():
            args.append(key)
            args.append(value)

        print("{}, {}".format(cmd.ii_path, args), file=sys.stderr)
        os.execle(cmd.ii_path, *args, new_environment)
        raise RuntimeError("If you see this, the execution failed")
    except FileNotFoundError as exc:
        print(
            "{}: could not find '{}': {}".format(SERVICE, cmd.ii_path, exc),
            file=sys.stderr,
        )
        sys.exit(1)
    except RuntimeError as exc:
        print(
            "{}: exec failure '{}': {}".format(SERVICE, cmd.ii_path, exc),
            file=sys.stderr,
        )
        sys.exit(1)


def get_option(ii_settings: Dict[Any, Any], key: str) -> str:
    """If key exists in settings and has value, return it.

    If key doesn't exist or has no value, return an empty string.
    """
    if key not in ii_settings:
        return ""

    if not ii_settings[key]:
        return ""

    return str(ii_settings[key])


def load_config_file(fname: str) -> Dict[Any, Any]:
    """Read TOML file and return its contents as a dictionary."""
    with open(fname, "rb") as fhandle:
        data = tomllib.load(fhandle)

    return data


def main():
    """Parse CLI args, load config file, build command and exec it."""
    args = parse_args()
    try:
        cfg = load_config_file(args.config_file)
        ii_cmd = build_command(cfg, args.ii_path)
        exec_command(ii_cmd)
    except Exception as exc:
        print(
            "{}: something went wrong: {}".format(SERVICE, exc),
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


def parse_args() -> argparse.Namespace:
    """Return parsed CLI args."""
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description="Build ii command based on configuration file and exec it.",
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
        "--ii-path",
        default=DEFAULT_II_FPATH,
        type=str,
        help="Full path to ii. Defaults to '%(default)s'.",
    )
    args = parser.parse_args()
    args.ii_path = shlex.quote(args.ii_path)
    return args


if __name__ == "__main__":
    main()
