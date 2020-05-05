#!/usr/bin/env python3

__author__ = 'Dmitry Ustalov'

import argparse
import asyncio
import logging
import os
import sys
from contextlib import suppress

import aiohttp_jinja2
import jinja2
import monetdblite
from aiohttp import web
from geolite2 import geolite2

from ballcone import __version__
from ballcone.core import Ballcone
from ballcone.monetdb_dao import MonetDAO
from ballcone.syslog_protocol import SyslogProtocol
from ballcone.web_ballcone import WebBallcone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version', version=f'Ballcone v{__version__}')
    parser.add_argument('-sh', '--syslog-host', default='127.0.0.1', help='syslog host to bind')
    parser.add_argument('-sp', '--syslog-port', default=65140, type=int, help='syslog UDP port to bind')
    parser.add_argument('-wh', '--web-host', default='127.0.0.1', help='Web interface host to bind')
    parser.add_argument('-wp', '--web-port', default=8080, type=int, help='Web interface TCP port to bind')
    parser.add_argument('-m', '--monetdb', default='monetdb', help='Path to MonetDB database')
    parser.add_argument('-ms', '--monetdb-schema', default='ballcone', help='MonetDB schema name')
    parser.add_argument('-p', '--period', default=5, type=int, help='Persistence period, in seconds')
    parser.add_argument('-t', '--top-limit', default=5, type=int, help='Limit for top-n queries')
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

    connection = monetdblite.make_connection(args.monetdb)

    dao = MonetDAO(connection, args.monetdb_schema)

    if not dao.schema_exists():
        dao.create_schema()

    geoip = geolite2.reader()

    ballcone = Ballcone(dao, geoip, args.top_limit, args.period)

    asyncio.ensure_future(ballcone.persist_timer())

    loop = asyncio.get_event_loop()

    syslog = loop.create_datagram_endpoint(lambda: SyslogProtocol(ballcone),
                                           local_addr=(args.syslog_host, args.syslog_port))
    loop.run_until_complete(syslog)

    # PyInstaller
    if getattr(sys, 'frozen', False):
        # noinspection PyProtectedMember
        jinja2_loader = jinja2.FileSystemLoader(os.path.join(sys._MEIPASS, 'templates'))
    else:
        jinja2_loader = jinja2.PackageLoader('ballcone')

    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2_loader)
    handler = WebBallcone(ballcone)
    app.router.add_get('/', handler.root, name='root')
    app.router.add_get('/services', handler.services, name='services')
    app.router.add_get('/services/{service}', handler.service, name='service')
    app.router.add_get('/services/{service}/{query}', handler.query, name='query')
    app.router.add_get('/sql', handler.sql, name='sql')
    app.router.add_post('/sql', handler.sql, name='sql')
    app.router.add_get('/nginx', handler.nginx, name='nginx')
    web.run_app(app, host=args.web_host, port=args.web_port)

    try:
        loop.run_forever()
    finally:
        all_tasks_func = asyncio.all_tasks if hasattr(asyncio, 'all_tasks') else asyncio.Task.all_tasks  # Python 3.6

        with suppress(RuntimeError):
            for task in all_tasks_func():
                task.cancel()

                with suppress(asyncio.CancelledError):
                    loop.run_until_complete(task)

        geoip.close()

        try:
            ballcone.persist()
        finally:
            connection.close()


if __name__ == '__main__':
    sys.exit(main())
