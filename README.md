# Balcone

Balcone is a server-side log collector for Web analytics.

## Requirements

* Python 3.6
* [LevelDB](https://github.com/google/leveldb)
* [Cap'n Proto](https://capnproto.org/)

## Installation

```nginx
log_format balcone_json_petrovich escape=json
    '{'
    '"service": "petrovich", '
    '"args": "$args", '
    '"body_bytes_sent": "$body_bytes_sent", '
    '"content_length": "$content_length", '
    '"content_type": "$content_type", '
    '"host": "$host", '
    '"http_referrer": "$http_referrer", '
    '"http_user_agent": "$http_user_agent", '
    '"http_x_forwarded_for": "$http_x_forwarded_for", '
    '"remote_addr": "$remote_addr", '
    '"request_method": "$request_method", '
    '"request_time": "$request_time", '
    '"status": "$status", '
    '"upstream_addr": "$upstream_addr", '
    '"uri": "$uri"'
    '}';

    access_log syslog:server=127.0.0.1:65140 balcone_json_petrovich;
```

## Copyright

Copyright &copy; 2020 Dmitry Ustalov. See [LICENSE](LICENSE) for details.