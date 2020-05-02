__author__ = 'Dmitry Ustalov'

import asyncio
import logging
import re
from collections import deque
from datetime import datetime, timezone
from ipaddress import ip_address
from typing import cast, Tuple, Union, Optional

import httpagentparser
import simplejson

from balcone.core import Balcone
from balcone.monetdb_dao import Entry, smallint

# nginx's output cannot be properly parsed by any parser I tried
NGINX_SYSLOG = re.compile(r'\A<[0-9]{1,3}>.*?: (?P<message>.+)\Z')


class SyslogProtocol(asyncio.DatagramProtocol):
    def __init__(self, balcone: Balcone):
        super().__init__()
        self.balcone = balcone
        self.transport: Optional[asyncio.BaseTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport):
        self.transport = transport

    def datagram_received(self, data: Union[bytes, str], addr: Tuple[str, int]):
        try:
            message = data.decode('utf-8') if isinstance(data, bytes) else data
        except UnicodeDecodeError:
            logging.info(f'Malformed UTF-8 received from {addr}')
            return

        match = NGINX_SYSLOG.match(message)

        if not match or not match.group('message'):
            logging.info(f'Missing payload from {addr}: {message}')
            return

        try:
            content = simplejson.loads(match.group('message'))
        except simplejson.JSONDecodeError:
            logging.info(f'Malformed JSON received from {addr}: {message}')
            return

        if 'service' not in content or not content['service']:
            logging.info(f'Missing service field from {addr}: {message}')
            return
        else:
            service = content['service'].strip().lower()

        if not self.balcone.check_service(service, should_exist=False):
            logging.info(f'Malformed service field from {addr}: {message}')
            return

        if service not in self.balcone.queue:
            if not self.balcone.dao.table_exists(service):
                self.balcone.dao.create_table(service)

            self.balcone.queue[service] = deque()

        current_datetime = datetime.fromisoformat(content['date']).astimezone(timezone.utc)

        user_agent = httpagentparser.detect(content['user_agent'])

        entry = Entry(
            datetime=current_datetime,
            date=current_datetime.date(),
            host=content['host'],
            method=content['method'],
            path=content['path'],
            status=cast(smallint, int(content['status'])),
            length=int(content['length']),
            generation_time=float(content['generation_time_milli']),
            referer=content['referrer'],
            ip=ip_address(content['ip']),
            country_iso_code=Balcone.iso_code(self.balcone.geoip, content['ip']),
            platform_name=user_agent.get('platform', {}).get('name', None),
            platform_version=user_agent.get('platform', {}).get('version', None),
            browser_name=user_agent.get('browser', {}).get('name', None),
            browser_version=user_agent.get('browser', {}).get('version', None),
            is_robot=user_agent.get('bot', None)
        )

        self.balcone.queue[service].append(entry)
