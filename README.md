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

## Configuration file

Example of configuration file:

```
net:irc.example.com:#chan1 #chan2
nickname:testme
ircdir:$HOME/ii/
# Enable/disable iicmd eg. if you have two bots in the same channel(s).
# iicmd is enabled by default.
# `iicmd_enabled:false` to disable it.
iicmd_enabled:true
bitly_api_token:api_token
bitly_group_id:group_id
```

## UnLicense

Since the original is [UnLicense]-d, I've decided to follow the suit.

[ii]: https://tools.suckless.org/ii/
[iibot]: https://github.com/c00kiemon5ter/iibot
[c00kiemon5ter]: https://github.com/c00kiemon5ter
[UnLicense]: https://unlicense.org
