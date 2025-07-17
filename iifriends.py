#!/usr/bin/env python3
"""Script takes care of auto-op/voice.

Friends file format is of friends.pl script. However, not all features are
currently implemented and supported.

2025/Jul/14 @ Zdenek Styblik <stybla@turnovfree.net>
"""
import argparse
import logging
import os
import re
import signal
import stat
import sys
import time
import traceback
from dataclasses import dataclass
from typing import BinaryIO
from typing import Dict
from typing import List

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
DEFAULT_FRIENDS_FILE = os.path.join(SCRIPT_PATH, "friends.txt")
PIPE_OPEN_TIMEOUT = 60  # seconds
PIPE_WRITE_TIMEOUT = 5  # seconds
RE_LINE_COMMENT = re.compile(r"^#")


@dataclass
class Friend:
    """Class represents IRC friend and related data."""

    handle: str
    hosts: str
    globflags: str
    chanflags: str
    password: str
    comment: str

    def is_friend(self, user_nick: str, user_hostmask: str) -> bool:
        """Check whether given nick and hostmask matches any of hostmasks.

        Return True, if at least one match is found, otherwise return False.
        """
        if not self.hosts:
            return False

        user_ident = "{:s}!{:s}".format(user_nick, user_hostmask)
        logging.debug("Ident for nick '%s' is '%s'.", user_nick, user_ident)
        for hostmask in self.hosts.split(" "):
            hostmask = re.escape(hostmask)
            hostmask = hostmask.replace("\\*", ".*")
            hostmask = hostmask.replace("\\?", ".?")
            logging.debug("Try to match '%s' to '%s'.", user_ident, hostmask)
            try:
                re_hostmask = r"^{}$".format(hostmask)
                match = re.search(re_hostmask, user_ident)
                if match:
                    return True
            except re.error as exception:
                logging.error(
                    "Regexp %r failed due to: %s",
                    re_hostmask,
                    exception,
                )

        return False

    @staticmethod
    def _parse_chanflags(chanflags: str) -> List:
        """Parse chanflags and return triplet of channel, flags and delay.

        Examples of expected input:

          #channel,flags,delay
          #channel,flags,
        """
        splitted = chanflags.split(",")
        if len(splitted) > 1:
            flags = splitted[1]
        else:
            flags = ""

        if len(splitted) > 2:
            try:
                delay = splitted[2]
            except (TypeError, ValueError):
                delay = -1
        else:
            delay = -1

        channel = splitted[0]
        return channel, flags, delay

    @staticmethod
    def _eval_flag(flags: str, good_flag: str, bad_flag: str) -> bool:
        """Determine whether a good_flag should be granted or not."""
        if bad_flag is None:
            bad_flag = "dont_match_this"

        if good_flag in flags and bad_flag not in flags:
            return True

        return False

    def give_op(self, channel: str) -> tuple[bool, int]:
        """Determine whether +o should be granted in given channel."""
        if self.chanflags:
            for chanflags in self.chanflags.split(" "):
                chan, flags, delay = self._parse_chanflags(chanflags)
                if channel != chan:
                    continue
                # +auto, +op, -deop
                auto_ops = self._eval_flag(flags, "a", None)
                give_ops = self._eval_flag(flags, "o", "d")
                return (auto_ops and give_ops), delay

        # +auto, +op, -deop
        auto_ops = self._eval_flag(self.globflags, "a", None)
        give_ops = self._eval_flag(self.globflags, "o", "d")
        return (auto_ops and give_ops), -1

    def give_voice(self, channel: str) -> tuple[bool, int]:
        """Determine whether +v should be granted in given channel."""
        if self.chanflags:
            for chanflags in self.chanflags.split(" "):
                chan, flags, delay = self._parse_chanflags(chanflags)
                if channel != chan:
                    continue
                # +auto, +voice, -mute
                auto_voice = self._eval_flag(flags, "a", None)
                give_voice = self._eval_flag(flags, "v", "m")
                return (auto_voice and give_voice), delay

        # +auto, +voice, -mute
        auto_voice = self._eval_flag(self.globflags, "a", None)
        give_voice = self._eval_flag(self.globflags, "v", "m")
        return (auto_voice and give_voice), -1


def find_friends(friends, nick: str, hostmask: str):
    """Return handles of friends which match given nick and hostmask."""
    friends_found = set([])
    for handle, friend in friends.items():
        is_friend = friend.is_friend(nick, hostmask)
        if not is_friend:
            continue

        friends_found.add(handle)

    return friends_found


def main():
    """Run iifriends and set mode if appropriate."""
    args = parse_args()
    logging.basicConfig(
        level=args.log_level,
        stream=sys.stderr,
        encoding="utf-8",
    )
    logging.debug("Message %r.", args.message)
    message_chunks = parse_message(args.message)
    if len(message_chunks) != 3:
        logging.error("Unable to parse message '%s'.", args.message)
        return

    nick, hostmask, channel = message_chunks
    if nick == args.self:
        # Don't act on yourself.
        return

    logging.debug("Friends file '%s'.", args.friends_file)
    friends = parse_friends_file(args.friends_file)
    friends_found = find_friends(friends, nick, hostmask)
    logging.debug("Friends found: '%s'.", friends_found)
    modes = set([])
    for handle in friends_found:
        retval, _ = friends[handle].give_op(channel)
        if retval is True:
            mode = "/mode {:s} +o {:s}\n".format(channel, nick)
            modes.add(mode)

        retval, _ = friends[handle].give_voice(channel)
        if retval is True:
            mode = "/mode {:s} +v {:s}\n".format(channel, nick)
            modes.add(mode)

    if not modes:
        logging.debug("No modes to be set - quit.")
        return

    output = os.path.join(args.ircd, args.network, "in")
    logging.debug("Output destination '%s'.", output)
    write_messages(output, modes)


def parse_args() -> argparse.Namespace:
    """Return parsed CLI args."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--friends-file",
        type=str,
        default=DEFAULT_FRIENDS_FILE,
        required=False,
        help="File which contains users.",
    )
    parser.add_argument(
        "--ircd",
        type=str,
        required=True,
        help="Full path to IRC/ii directory.",
    )
    parser.add_argument(
        "--message",
        type=str,
        required=True,
        help="ii message to be processed.",
    )
    parser.add_argument(
        "--network",
        type=str,
        required=True,
        help="Name of IRC network message came from.",
    )
    parser.add_argument(
        "--self",
        type=str,
        required=True,
        help="Bot's nickname.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Set log level to DEBUG.",
    )
    args = parser.parse_args()

    if not args.ircd:
        parser.error("Argument 'ircd' must not be empty")

    if not args.network:
        parser.error("Argument 'network' must not be empty")

    args.log_level = logging.DEBUG if args.verbose is True else logging.ERROR
    return args


def parse_friends_file(fname: str):
    """Parse and return data in friends file."""
    friends = {}
    try:
        with open(fname, mode="r", encoding="utf-8") as fhandle:
            for line in fhandle.readlines():
                match = RE_LINE_COMMENT.search(line)
                if match:
                    logging.debug("Friends line is a comment %r.", line)
                    continue

                friends_data = parse_friends_line(line)
                if not friends_data:
                    logging.error("Failed to parse friends line %r.", line)
                    continue

                handle = friends_data.get("handle", None)
                if not handle:
                    logging.error("Friends handle cannot be empty %r.", line)
                    continue

                friends[handle] = Friend(
                    handle=friends_data.get("handle", ""),
                    hosts=friends_data.get("hosts", ""),
                    globflags=friends_data.get("globflags", ""),
                    chanflags=friends_data.get("chanflags", ""),
                    password=friends_data.get("password", ""),
                    comment=friends_data.get("comment", ""),
                )
    except Exception as exception:
        logging.error(
            "Parsing of friends file '%s' failed: %s",
            fname,
            exception,
        )

    return friends


def parse_friends_line(line: str) -> Dict[str, str]:
    """Return parsed line in friends file format."""
    match = RE_LINE_COMMENT.search(line)
    if match:
        return {}

    line = line.strip()
    line_splitted = line.split("%")
    friends_data = {}
    for chunk in line_splitted:
        chunk_splitted = chunk.split("=", 1)
        key = chunk_splitted[0]
        if not key:
            continue

        if len(chunk_splitted) == 2:
            value = chunk_splitted[1]
        else:
            value = ""

        friends_data[key] = value

    return friends_data


def parse_message(message: str) -> List[str]:
    """Parse channel join message and return nick, hostmask and channel.

    Returns an empty list on parse error.

    Expected message on input:

      nick(~user@example.com) has joined #channel
    """
    splitted = message.split(" has joined ")
    if len(splitted) != 2:
        return []

    channel = splitted[1].strip()
    splitted = splitted[0].split("(")
    if len(splitted) != 2:
        return []

    nick = splitted[0].strip()
    hostmask = splitted[1].rstrip(")").strip()
    return nick, hostmask, channel


def signal_handler(signum, frame):
    """Handle SIGALRM signal."""
    raise TimeoutError


def write_messages(output: str, messages: List, sleep: int = 2) -> None:
    """Send modes into the ii pipe."""
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(PIPE_OPEN_TIMEOUT)
    with open(output, "wb") as fhandle:
        signal.alarm(0)
        for message in messages:
            try:
                write_message(fhandle, message)
                time.sleep(sleep)
            except (TimeoutError, ValueError):
                logging.debug(
                    "Failed to write %r: %s", message, traceback.format_exc()
                )


def write_message(fhandle: BinaryIO, message: str) -> None:
    """Write message into file handle.

    Sets up SIGALRM and raises `TimeoutError` if alarm is due.
    """
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(PIPE_WRITE_TIMEOUT)
    try:
        fhandle_stat = os.fstat(fhandle.fileno())
        is_fifo = stat.S_ISFIFO(fhandle_stat.st_mode)
        if not is_fifo:
            raise ValueError("fhandle is expected to be a FIFO pipe")

        logging.debug("Will write %r.", message)
        fhandle.write(message.encode("utf-8"))
        signal.alarm(0)
    except Exception as exception:
        raise exception
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
