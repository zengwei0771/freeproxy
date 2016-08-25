#!/usr/bin/env python
#encoding=utf-8


from tornado import ioloop, web
from redis import Redis
from config import SERVER_SECRET, SERVER_PORT, REDIS_HOST, REDIS_PORT, REDIS_DB
from proxy import ProxyProcess
import sys
import logging
from logging import FileHandler, Formatter
import json


logging.basicConfig(
    filename="./logs/server.log",
    filemode="w",
    format="%(asctime)s-%(name)s-%(levelname)s-%(message)s",
    level=logging.WARN
)


class PsHtmlHandler(web.RequestHandler):
    def get(self):
        rs = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        alives = rs.hgetall('alives')
        results = []
        for p in alives:
            alives[p] = json.loads(alives[p])
            if alives[p]['status'] == 'living':
                results.append({
                    'host': p[7:].split(':')[0],
                    'port': p[7:].split(':')[1],
                    'address': alives[p]['address'],
                    'nm': alives[p]['nm'],
                    'type': alives[p]['type'],
                })
        self.render('proxys.html', results=results)


class PsJsonHandler(web.RequestHandler):
    def get(self):
        rs = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        alives = rs.hgetall('alives')
        results = []
        for p in alives:
            alives[p] = json.loads(alives[p])
            if alives[p]['status'] == 'living':
                results.append({
                    'host': p[7:].split(':')[0],
                    'port': p[7:].split(':')[1],
                    'address': alives[p]['address'],
                    'nm': alives[p]['nm'],
                    'type': alives[p]['type'],
                })
        self.write(json.dumps(results))


def start_server(debug):
    app = web.Application([
        (r"/", web.RedirectHandler, {"url": "/proxys.html"}),
        (r"/proxys.html", PsHtmlHandler),
        (r"/proxys.json", PsJsonHandler),
    ], **{
        "debug": debug,
        "cookie_secret": SERVER_SECRET,
        "static_path": "./static",
        "compress_response": True,
        "xsrf_cookies": True,
        "template_path": "./templates",
    })
    app.listen(SERVER_PORT)
    ioloop.IOLoop.current().start()


if __name__ == "__main__":
    p = ProxyProcess()
    p.daemon = True
    p.start()
    start_server(True if 'debug' in sys.argv else False)
