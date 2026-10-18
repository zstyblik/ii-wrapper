# ii-wrapper

Wrapper and a bot for [ii] IRC client inspired by and based on [iibot] by
[c00kiemon5ter]. Unlike the original, this one is leaning towards Python for
better or worse.

_Why?_ Why not? Bash, cURL, calc - all of these are dependencies in the same way
as Python and friends are.

ii v1.8 or newer(probably) is required due to change in log output format.

Features:

* commands
* configuration file in order to support multiple instances of bot
* auto reconnect
* auto voice/op

## Configuration file

Structure of configuration file in TOML format is currently experimental,
unstable and subject to change. Example of configuration file:

```
[ii.settings]
ircdir = "/some/path/irc"
server = "irc.example.com"
nickname = "mynick"

# Enable/disable support for commands.
[ii.cmd]
enabled = true

# Enable/disable support for auto voice/op.
[ii.friends]
enabled = true

# Joins #channel1 and #channel2 on startup.
[channel.arbitrarylabel1]
name = "#channel1"

[channel.arbitrarylabel2]
name = "#channel2"

# In order to enable URL shortening API token and group ID must be given.
[bitly]
api_token = ""
group_id = ""
```

## UnLicense

Since the original is [UnLicense]-d, I've decided to follow the suit.

[ii]: https://tools.suckless.org/ii/
[iibot]: https://github.com/c00kiemon5ter/iibot
[c00kiemon5ter]: https://github.com/c00kiemon5ter
[UnLicense]: https://unlicense.org
