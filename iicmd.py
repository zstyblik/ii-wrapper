#!/usr/bin/env python3
# Workaround https://github.com/psf/black/issues/4175
"""Python implementation of commands for iibot.

2024/Mar/14 @ Zdenek Styblik <stybla@turnovfree.net>
"""
import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import traceback

import requests

# List of supported commands and whether command requires user input or not.
COMMANDS = {
    "calc": True,
    "echo": True,
    "fortune": False,
    "list": False,
    "ping": False,
    "slap": False,
    "url": True,
    "whereami": False,
}

HTTP_MAX_REDIRECTS = 2
HTTP_TIMEOUT = 30  # seconds


def cmd_fortune():
    """Try to get a fortune cookie."""
    fortune_fpath = shutil.which("fortune", mode=os.F_OK | os.X_OK)
    if not fortune_fpath:
        print("Damn, I'm out of fortune cookies! :(")
        return

    with subprocess.Popen(
        [fortune_fpath, "-osea"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as fortune_proc:
        fortune_out, fortune_err = fortune_proc.communicate()

    if fortune_proc.returncode != 0:
        logging.error("fortune RC: %s", fortune_proc.returncode)
        logging.error("fortune STDOUT: '%s'", fortune_out)
        logging.error("fortune STDERR: '%s'", fortune_err)
        print("Oh no, I've dropped my fortune cookie! :(")
        return

    print("{:s}".format(fortune_out.decode("utf-8").rstrip("\n")))


def get_url_short(url, bitly_gid, bitly_token):
    """Convert URL to a shorter one through bit.ly.

    See https://dev.bitly.com/ for API documentation.
    """
    short_url = url
    try:
        user_agent = "iicmd_{:d}".format(int(time.time()))
        headers = {
            "Authorization": "Bearer {:s}".format(bitly_token),
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        }
        data = {
            "long_url": url,
            "domain": "bit.ly",
            "group_guid": bitly_gid,
        }

        rsp_short = requests.post(
            "https://api-ssl.bitly.com/v4/shorten",
            headers=headers,
            data=json.dumps(data),
            timeout=HTTP_TIMEOUT,
        )
        rsp_short.raise_for_status()
        if "link" not in rsp_short.json():
            raise KeyError("Expected key 'link' not found in rsp from bit.ly")

        short_url = rsp_short.json()["link"]
    except Exception:
        # NOTE: this isn't exactly great, but it simplifies the code.
        logging.error(
            "Failed to get short URL of '%s' due to: %s",
            url,
            traceback.format_exc(),
        )

    return short_url


def get_url_title(url):
    """Try to get and return title of given URL."""
    url_title = "No title"
    try:
        session = requests.Session()
        session.max_redirects = HTTP_MAX_REDIRECTS
        user_agent = "iicmd_{:d}".format(int(time.time()))
        headers = {"User-Agent": user_agent}
        rsp_title = session.get(url, headers=headers, timeout=HTTP_TIMEOUT)
        rsp_title.raise_for_status()

        match = re.search(r"<title>(?P<title>[^<]*)<\/title>", rsp_title.text)
        if match:
            url_title = match.group("title")
        else:
            logging.debug("No title for '{:s}'".format(url))
    except Exception:
        # NOTE: this isn't exactly great, but it simplifies the code.
        # No title then.
        logging.error(
            "HTTP req to '%s' has failed: %s", url, traceback.format_exc()
        )

    return url_title


def cmd_url(extra):
    """Process URL and print-out the result."""
    match = re.search(r".*(?P<url>http[^ ]*).*", extra)
    if not match:
        logging.debug("No URL detected in '%s'", extra)
        return

    url = match.group("url")
    # Convert YouTube URLs
    url = re.sub(
        r".*youtube\..*v=([^&]+).*", r"http://youtube.com/embed/\1", url
    )
    url = re.sub(r".*youtu\.be/(.+)", r"http://youtube.com/embed/\1", url)
    # Try to get URL's title
    url_title = get_url_title(url)
    bitly_gid = os.getenv("IICMD_BITLY_GROUP_ID", None)
    bitly_token = os.getenv("IICMD_BITLY_API_TOKEN", None)
    if len(url) > 80 and bitly_gid and bitly_token:
        url = get_url_short(url, bitly_gid, bitly_token)

    print("Title for {:s} - {:s}".format(url, url_title))


def main():
    """Run iibot command."""
    logging.basicConfig(stream=sys.stderr, encoding="utf-8")
    args = parse_args()

    cmd = args.message.split(" ")[0]
    extra = " ".join(args.message.split(" ")[1:])
    # Strip leading/trailing whitespace and check, if we have any "extra" left
    # TODO: what about newlines?
    extra = extra.strip(" ")
    if not extra and cmd in COMMANDS and COMMANDS[cmd] is True:
        cmd = "invalid"

    if cmd == "list":
        print(
            "{:s}: supported commands are - {:s}".format(
                args.nick, ", ".join(sorted(list(COMMANDS.keys())))
            )
        )
    elif cmd == "calc":
        # TODO: this will be big pain and huge amount of LOC to implement
        # See https://stackoverflow.com/a/11952343
        print("{:s}: my ALU is b0rked - does not compute.".format(args.nick))
    elif cmd == "echo":
        print("{:s}".format(extra.lstrip("/")))
    elif cmd == "fortune":
        cmd_fortune()
    elif cmd == "ping":
        print("{:s}: pong! Ping-pong, get it?".format(args.nick))
    elif cmd == "slap":
        print("{:s}: I'll slap your butt!".format(args.nick))
    elif cmd == "url":
        cmd_url(extra)
    elif cmd == "whereami":
        print("{:s}: this! is!! {:s}!!!".format(args.nick, args.channel))
    else:
        print(
            "{:s}: what are you on about? Me not understanding.".format(
                args.nick
            )
        )


def parse_args():
    """Return parsed CLI args."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nick",
        type=str,
        required=True,
        help="Nickname of user who sent the message.",
    )
    parser.add_argument(
        "--message",
        type=str,
        required=True,
        help="ii message to be processed.",
    )
    parser.add_argument(
        "--ircd",
        type=str,
        required=True,
        help="Full path to IRC/ii directory.",
    )
    parser.add_argument(
        "--network",
        type=str,
        required=True,
        help="Name of IRC network message came from.",
    )
    parser.add_argument(
        "--channel",
        type=str,
        required=True,
        help="Name of channel message came from.",
    )
    parser.add_argument(
        "--self",
        type=str,
        required=True,
        help="Bot's nickname.",
    )
    args = parser.parse_args()

    if not args.nick:
        args.nick = "unknown.stranger"

    if not args.ircd:
        parser.error("Argument 'ircd' must not be empty")

    if not args.network:
        parser.error("Argument 'network' must not be empty")

    if not args.channel:
        parser.error("Argument 'channel' must not be empty")

    return args


if __name__ == "__main__":
    main()
