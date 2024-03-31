"""Unit tests for iicmd.py."""
import os
import sys
from unittest.mock import patch

import pytest

import iicmd  # noqa:I202

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "msg,expected",
    [
        # Expected invocation
        (
            "calc 1+1",
            "irc_user: my ALU is b0rked - does not compute.\n",
        ),
        # Missing formula which is required arg.
        (
            "calc",
            "irc_user: what are you on about? Me not understanding.\n",
        ),
        # Expected invocation
        (
            "echo hello there",
            "hello there\n",
        ),
        # Leading "/" should be stripped.
        (
            "echo /hello there",
            "hello there\n",
        ),
        (
            "echo //hello there",
            "hello there\n",
        ),
        # Expected invocation
        (
            "list",
            (
                "irc_user: supported commands are - calc, echo, fortune, "
                "list, ping, slap, url, whereami\n"
            ),
        ),
        # Extra args should be ignored.
        (
            "list abc efg",
            (
                "irc_user: supported commands are - calc, echo, fortune, "
                "list, ping, slap, url, whereami\n"
            ),
        ),
        # Expected invocation
        (
            "ping",
            "irc_user: pong! Ping-pong, get it?\n",
        ),
        # Extra args should be ignored.
        (
            "ping abc123",
            "irc_user: pong! Ping-pong, get it?\n",
        ),
        # Expected invocation
        (
            "slap",
            "irc_user: I'll slap your butt!\n",
        ),
        # Extra args should be ignored.
        (
            "slap foo",
            "irc_user: I'll slap your butt!\n",
        ),
        # Expected invocation
        (
            "whereami",
            "irc_user: this! is!! irc_channel!!!\n",
        ),
        # Extra args should be ignored.
        (
            "whereami WHERE?!",
            "irc_user: this! is!! irc_channel!!!\n",
        ),
        (
            "invalid_command",
            "irc_user: what are you on about? Me not understanding.\n",
        ),
        (
            "invalid_command and some message on the top",
            "irc_user: what are you on about? Me not understanding.\n",
        ),
    ],
)
def test_commands(msg, expected, capsys):
    """Test commands which don't require anything special and work OOTB."""
    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message={:s}".format(msg),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected
    assert captured.err == ""


@pytest.mark.parametrize(
    "msg",
    [
        "fortune",
        # Extra args should be ignored.
        "fortune abc123",
    ],
)
@patch("shutil.which")
def test_cmd_fortune(mock_shutil_which, msg, capsys):
    """Test cmd_fortune() under ideal conditions."""
    expected = "This is a fake fortune cookie\n"

    fake_fortune = os.path.join(SCRIPT_PATH, "files", "fake_fortune.sh")
    mock_shutil_which.return_value = fake_fortune

    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message={:s}".format(msg),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected
    assert captured.err == ""


@patch("shutil.which")
def test_cmd_fortune_not_present(mock_shutil_which, capsys):
    """Test case when fortune is not present on the system."""
    expected = "Damn, I'm out of fortune cookies! :(\n"
    mock_shutil_which.return_value = None

    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message=fortune",
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected
    assert captured.err == ""


@patch("shutil.which")
def test_cmd_fortune_retcode(mock_shutil_which, capsys, caplog):
    """Test case when fortune RC != 0."""
    expected = "Oh no, I've dropped my fortune cookie! :(\n"
    # NOTE: I don't want to import logging.
    expected_log_tuples = [
        ("root", 40, "fortune RC: 1"),
        ("root", 40, "fortune STDOUT: 'b'Unfortunate fate.\\n''"),
        ("root", 40, "fortune STDERR: 'b'Something went wrong.\\n''"),
    ]

    fake_fortune = os.path.join(SCRIPT_PATH, "files", "fake_fortune_error.sh")
    mock_shutil_which.return_value = fake_fortune

    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message=fortune",
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected
    assert captured.err == ""
    assert caplog.record_tuples == expected_log_tuples


def test_cmd_url_no_url_in_message(capsys):
    """Test case when there is no HTTP(S) to be matched in the message."""
    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message=url foo bar lar mar test message",
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    "url,expected_url",
    [
        (
            "https://www.youtube.com/watch?v=9G-fg6G738c",
            "http://youtube.com/embed/9G-fg6G738c",
        ),
        (
            "https://youtu.be/9G-fg6G738c?si=KD5OpJ_F2yTPIK4E",
            "http://youtube.com/embed/9G-fg6G738c?si=KD5OpJ_F2yTPIK4E",
        ),
    ],
)
def test_cmd_url_youtube_link_conversion(
    url, expected_url, capsys, fixture_mock_requests
):
    """Test conversion of YouTube links in cmd_url()."""
    expected_msg = "Title for {:s} - No title\n".format(expected_url)

    rsp_text = "No title here, just little <title>"
    mock_http_url = fixture_mock_requests.get(expected_url, text=rsp_text)

    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message=url foo bar {:s} message".format(url),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected_msg
    assert captured.err == ""

    assert mock_http_url.called is True


@pytest.mark.parametrize(
    "rsp_text,expected_title",
    [
        # No title
        (
            "No title here, just little <title>",
            "No title",
        ),
        # Test title
        (
            (
                "<html><head><title>Little title</title></head>"
                "<body></body></html>"
            ),
            "Little title",
        ),
    ],
)
def test_cmd_url_title(rsp_text, expected_title, capsys, fixture_mock_requests):
    """Test fetching of title in cmd_url()."""
    url = "https://www.example.org"
    expected_msg = "Title for {:s} - {:s}\n".format(url, expected_title)

    mock_http_url = fixture_mock_requests.get(url, text=rsp_text)

    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message=url foo bar {:s} message".format(url),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected_msg
    assert captured.err == ""

    assert mock_http_url.called is True


def test_cmd_url_two_links(capsys, fixture_mock_requests):
    """Test cmd_url() when there are multiple URLs in message.

    Only the last URL should be matched.
    """
    url = "https://www.example.org"
    expected_title = "Little title"
    expected_msg = "Title for {:s} - {:s}\n".format(url, expected_title)

    rsp_text = (
        "<html><head><title>Little title</title></head>" "<body></body></html>"
    )
    mock_http_url = fixture_mock_requests.get(url, text=rsp_text)

    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message=url foo bar http://ignored.url {:s} message".format(url),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected_msg
    assert captured.err == ""

    assert mock_http_url.called is True


@pytest.mark.parametrize(
    "irc_message",
    [
        "url https://www.example.org",
        "url https://www.example.org ~ here",
        "url https://www.example.org <<< here",
        "url bla bla https://www.example.org blablabla",
        "url blabla https://www.example.org",
        "url https://www.example.org also blabla",
    ],
)
def test_cmd_url_parse_url(irc_message, capsys, fixture_mock_requests):
    """Test extraction of URL in cmd_url() code path.

    Based on bug in iibot-ng when URL would be 'parsed out' completely from the
    message itself.
    """
    url = "https://www.example.org"
    expected_title = "Little title"
    expected_msg = "Title for {:s} - {:s}\n".format(url, expected_title)

    rsp_text = (
        "<html><head><title>Little title</title></head>" "<body></body></html>"
    )
    mock_http_url = fixture_mock_requests.get(url, text=rsp_text)

    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message={:s}".format(irc_message),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected_msg
    assert captured.err == ""

    assert mock_http_url.called is True


@pytest.mark.parametrize(
    "url,bitly_token,bitly_gid,bitly_rsp,bitly_called",
    [
        # URL is too short -> bit.ly shouldn't be called
        (
            "http://www.example.org",
            "token",
            "gid",
            "",
            False,
        ),
        # bit.ly should be called, but GID is not set
        (
            (
                "http://www.example.org/uGaiXaGh9aiz2kaejeiW0quahtheiwaiveenge"
                "Ghook2aeW6suk4phooc8PaiwooCeT1aep3ahzaiBae"
            ),
            "token",
            "",
            "",
            False,
        ),
        # bit.ly should be called, but TOKEN is not set
        (
            (
                "http://www.example.org/uGaiXaGh9aiz2kaejeiW0quahtheiwaiveenge"
                "Ghook2aeW6suk4phooc8PaiwooCeT1aep3ahzaiBae"
            ),
            "",
            "gid",
            "",
            False,
        ),
        # call bit.ly and try to get short URL
        (
            (
                "http://www.example.org/uGaiXaGh9aiz2kaejeiW0quahtheiwaiveenge"
                "Ghook2aeW6suk4phooc8PaiwooCeT1aep3ahzaiBae"
            ),
            "token",
            "gid",
            '{"message":"it is broken"}',
            True,
        ),
    ],
)
def test_cmd_url_no_bitly(
    url,
    bitly_token,
    bitly_gid,
    bitly_rsp,
    bitly_called,
    fixture_mock_requests,
    capsys,
    monkeypatch,
):
    """Test cmd_url() with bit.ly broken one way or another."""
    expected_msg = "Title for {:s} - No title\n".format(url)

    rsp_url_text = "No title here, just a little <title>"
    mock_http_url = fixture_mock_requests.get(url, text=rsp_url_text)

    bitly_api_url = "https://api-ssl.bitly.com/v4/shorten"
    mock_http_bitly = fixture_mock_requests.post(bitly_api_url, text=bitly_rsp)

    monkeypatch.setenv("IICMD_BITLY_GROUP_ID", bitly_gid)
    monkeypatch.setenv("IICMD_BITLY_API_TOKEN", bitly_token)

    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message=url foo bar {:s} message".format(url),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected_msg
    assert captured.err == ""

    assert mock_http_bitly.called is bitly_called
    assert mock_http_url.called is True


def test_cmd_url_with_bitly(fixture_mock_requests, capsys, monkeypatch):
    """Test cmd_url() with call to bit.ly."""
    url = (
        "http://www.example.org/uGaiXaGh9aiz2kaejeiW0quahtheiwaiveenge"
        "Ghook2aeW6suk4phooc8PaiwooCeT1aep3ahzaiBae"
    )
    short_url = "https://short.example.org/abc123"
    expected_msg = "Title for {:s} - No title\n".format(short_url)

    bitly_api_url = "https://api-ssl.bitly.com/v4/shorten"
    bitly_token = "token"
    bitly_gid = "gid"
    bitly_rsp = '{{"link":"{:s}"}}'.format(short_url)

    rsp_url_text = "No title here, just a little <title>"
    mock_http_url = fixture_mock_requests.get(url, text=rsp_url_text)

    monkeypatch.setenv("IICMD_BITLY_GROUP_ID", bitly_gid)
    monkeypatch.setenv("IICMD_BITLY_API_TOKEN", bitly_token)
    mock_http_bitly = fixture_mock_requests.post(bitly_api_url, text=bitly_rsp)

    args = [
        "./iicmd.py",
        "--nick=irc_user",
        "--message=url foo bar {:s} message".format(url),
        "--ircd=irc_ircd",
        "--network=irc_network",
        "--channel=irc_channel",
        "--self=irc_botuser",
    ]
    with patch.object(sys, "argv", args):
        iicmd.main()

    captured = capsys.readouterr()
    assert captured.out == expected_msg
    assert captured.err == ""

    assert mock_http_url.called is True
    assert mock_http_bitly.called is True
