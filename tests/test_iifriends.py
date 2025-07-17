#!/usr/bin/env python3
"""Unit tests for iifriends.py."""
import os
import sys
from unittest.mock import call
from unittest.mock import patch

import pytest

import iifriends  # noqa:I202

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "message,expected",
    [
        (
            "tester1(~test1@example.com) has joined #chan1",
            {"/mode #chan1 +o tester1\n"},
        ),
        (
            "tester1(~test1@example.com) has joined #chan2",
            {"/mode #chan2 +v tester1\n"},
        ),
        (
            "tester2(~test2@foo.example.com) has joined #chan1",
            {"/mode #chan1 +v tester2\n"},
        ),
        (
            "tester3(~test3@test3.example.com) has joined #chan1",
            {"/mode #chan1 +v tester3\n"},
        ),
    ],
)
@patch("iifriends.write_messages")
def test_iifriends_match(mock_write_messages, message, expected):
    """Run through iifriends, match is expected."""
    friends_file = os.path.join(SCRIPT_PATH, "files", "friends.txt")
    args = [
        "./iifriends.py",
        "--message={:s}".format(message),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--self=irc_botuser",
        "--friends-file={:s}".format(friends_file),
        "--verbose",
    ]
    with patch.object(sys, "argv", args):
        iifriends.main()

    expected_calls = [call("irc_ircd/irc_network/in", expected)]
    assert mock_write_messages.mock_calls == expected_calls


@pytest.mark.parametrize(
    "message",
    [
        ("tester3(~test3@test3.example.net) has joined #chan1"),
        ("tester3(~test3@abraka.example.net) has joined #chan2"),
        # ("", ""),
    ],
)
@patch("iifriends.write_messages")
def test_iifriends_no_match(mock_write_messages, message):
    """Run through iifriends, no match is expected."""
    friends_file = os.path.join(SCRIPT_PATH, "files", "friends.txt")
    args = [
        "./iifriends.py",
        "--message={:s}".format(message),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--self=irc_botuser",
        "--friends-file={:s}".format(friends_file),
        "--verbose",
    ]
    with patch.object(sys, "argv", args):
        iifriends.main()

    assert mock_write_messages.mock_calls == []
