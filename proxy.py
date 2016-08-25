#!/usr/bin/env python
#encoding=utf-8

__author__ = 'lucky'


import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import sys
import threading
from Queue import Queue
from redis import Redis
from config import *
import time
import json
from multiprocessing import Process
from logging import FileHandler, Formatter


logging.basicConfig(
    filename="./logs/proxy.log",
    filemode="w",
    format="%(asctime)s-%(name)s-%(levelname)s-%(message)s",
    level=logging.WARN
)

DEAD_TIME = 600
CHECK_TIME = 600


class Proxys(object):

    @staticmethod
    def test_proxy(proxy):
        try:
            s = requests.Session()
            r = s.get('http://weixin.sogou.com/',
                      proxies={'http':proxy},
                      headers=HEADERS,
                      timeout=8
            )
            if r.status_code == 200:
                return True
            return False
        except Exception, e:
            return False

    @staticmethod
    def fetch_xici(req=requests):
        proxys = []
        try:
            for page in range(1, 6):
                r = req.get('http://www.xicidaili.com/nn/%d' % page,
                            headers=HEADERS, timeout=8)
                dom = BeautifulSoup(r.content, "html5lib", from_encoding="UTF-8")
                for tr in dom.find('table', id='ip_list').findAll('tr'):
                    tds = tr.findAll('td')
                    if len(tds) == 0:
                        continue
                    host = tds[1].text.strip()
                    port = int(tds[2].text.strip())
                    proxys.append({
                        'host': host,
                        'port': port,
                        'address': tds[3].text.strip(),
                        'nm': tds[4].text.strip(),
                        'type': 'http',
                    })
            for page in range(1, 6):
                r = req.get('http://www.xicidaili.com/qq/%d' % page,
                            headers=HEADERS, timeout=8)
                dom = BeautifulSoup(r.content, "html5lib", from_encoding="UTF-8")
                for tr in dom.find('table', id='ip_list').findAll('tr'):
                    tds = tr.findAll('td')
                    if len(tds) == 0:
                        continue
                    host = tds[1].text.strip()
                    port = int(tds[2].text.strip())
                    proxys.append({
                        'host': host,
                        'port': port,
                        'address': tds[3].text.strip(),
                        'nm': tds[4].text.strip(),
                        'type': 'socks',
                    })
        except Exception, e:
            logging.error(str(e))
        return proxys

    @staticmethod
    def fetch_kuai(req=requests):
        proxys = []
        try:
            for page in range(1, 11):
                r = requests.get('http://www.kuaidaili.com/free/inha/%d/' % page,
                                 headers=HEADERS, timeout=8)
                dom = BeautifulSoup(r.content, 'html5lib', from_encoding="UTF-8")
                for tr in dom.find('div', id='list').findAll('tr'):
                    tds = tr.findAll('td')
                    if len(tds) == 0 or tds[3].text.strip() != 'HTTP':
                        continue
                    host = tds[0].text.strip()
                    port = int(tds[1].text.strip())
                    proxys.append({
                        'host': host,
                        'port': port,
                        'address': tds[4].text.strip(),
                        'nm': '高匿',
                        'type': 'http'
                    })
        except Exception, e:
            logging.error(str(e))
        return proxys

    @staticmethod
    def fetch_big(req=requests):
        proxys = []
        try:
            for page in range(1, 11):
                r = req.get('http://www.bigdaili.com/dailiip/1/%d.html' % page,
                                 headers=HEADERS, timeout=8)
                dom = BeautifulSoup(r.content, "html5lib", from_encoding="UTF-8")
                for tr in dom.find('table').findAll('tr'):
                    tds = tr.findAll('td')
                    if len(tds) == 0 or tds[3].text.strip() != 'HTTP':
                        continue
                    host = tds[0].text.strip()
                    port = int(tds[1].text.strip())
                    proxys.append({
                        'host': host,
                        'port': port,
                        'address': tds[5].text.strip(),
                        'nm': '高匿',
                        'type': 'http' if 'http' in tds[3].text.strip() else 'socks',
                    })
        except Exception, e:
            logging.error(str(e))
        return proxys

    @staticmethod
    def fetch_goubanjia(req=requests):
        proxys = []
        try:
            r = req.get('http://proxy.goubanjia.com/free/gngn/index.shtml',
                             headers=HEADERS, timeout=8)
            dom = BeautifulSoup(r.content, "html5lib", from_encoding="UTF-8")
            for tr in dom.find('table').findAll('tr'):
                tds = tr.findAll('td')
                if len(tds) == 0 or tds[3].text.strip() != 'http':
                    continue
                host = ''
                for item in tds[0].children:
                    if item.get('style') and ('display: none' in item.get('style') or 'display:none' in item.get('style')):
                        continue
                    host += item.text.strip()
                port = int(tds[1].text.strip())
                proxys.append({
                    'host': host,
                    'port': port,
                    'address': tds[5].text.strip(),
                    'nm': '高匿',
                    'type': 'http' if 'http' in tds[3].text.strip() else 'socks',
                })
        except Exception, e:
            logging.error(str(e))
        return proxys


class ProxysRequest(object):

    def __init__(self, proxys):
        self.proxys = {}
        for p in proxys[:100]:
            self.proxys[p] = {
                'valid': True,
                'priority': 0
            }

    def get(self, url, headers, timeout=8):
        if len(self.proxys) == 0:
            return None

        ps = sorted([i for i in self.proxys.items() if i[1]['valid']],
                    key=lambda x:x[1]['priority'])
        for p in ps:
            s = requests.Session()
            try:
                r = s.get(url,
                          headers=headers,
                          proxies={'http': p[0]},
                          timeout=timeout)
                if r.status_code == 200:
                    p[1]['priority'] += 1
                    return r
            except Exception, e:
                logging.warn('Proxy dead. %s. %s' % (p, str(e)))
            p[1]['valid'] = False
        return None

    def update(self, proxys):
        for p in proxys[:100]:
            if not self.proxys.get(p) or not self.proxys[p]['valid']:
                self.proxys[p] = {'valid': True, 'priority': 0}


class CheckProxyThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        self.worker_num = 20

    def run(self):

        def check(in_):
            while True:
                proxy = in_.get()
                if proxy is None:
                    break

                r = Proxys.test_proxy(proxy)
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if r:
                    values = self.redis.hget('alives', proxy)
                    if values:
                        values = json.loads(values)
                        values['status'] = 'living'
                        values['time'] = now
                        self.redis.hset('alives',
                                        proxy,
                                        json.dumps(values))
                else:
                    self.redis.hdel('alives', proxy)
                    self.redis.hset('deads', proxy, now)

        in_ = Queue()
        workers = []
        for i in range(self.worker_num):
            w = threading.Thread(target=check, args=(in_,))
            w.setDaemon(True)
            w.start()
            workers.append(w)

        while True:
            if in_.empty():
                alives = self.redis.hgetall('alives')
                now = datetime.now()
                tochecks = []
                for p in alives:
                    alives[p] = json.loads(alives[p])
                    if alives[p]['status'] == 'init' or datetime.strptime(alives[p]['time'], '%Y-%m-%d %H:%M:%S') < now - timedelta(seconds=CHECK_TIME):
                        tochecks.append(p)

                [in_.put(p) for p in tochecks]

            time.sleep(5)

        [in_.put(None) for i in range(self.worker_num)]
        [workers[i].join() for i in range(self.worker_num)]


class ProxyProcess(Process):
    
    def run(self):
        rs = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        #rs.delete('alives')
        #rs.delete('deads')
        pr = ProxysRequest([])

        cpt = CheckProxyThread()
        cpt.setDaemon(True)
        cpt.start()

        while True:
            alives = rs.hgetall('alives')
            deads = rs.hgetall('deads')
            proxys = []
            for p in alives:
                alives[p] = json.loads(alives[p])
                if alives[p]['status'] != 'init':
                    proxys.append(p)
            if len(proxys) > 16:
                pr.update(proxys)
                ps = Proxys.fetch_xici(pr) + Proxys.fetch_kuai(pr) + \
                        Proxys.fetch_big(pr)
            else:
                ps = Proxys.fetch_xici() + Proxys.fetch_kuai() + Proxys.fetch_big()

            now = datetime.now()
            for p in ps:
                url = 'http://%s:%d' % (p['host'], p['port'])
                if not alives.get(url) and not deads.get(url):
                    rs.hset('alives', url, json.dumps({'status':'init', 'address':p['address'], 'nm':p['nm'], 'type':p['type']}))
                elif deads.get(url) and datetime.strptime(deads[url], '%Y-%m-%d %H:%M:%S') < now - timedelta(seconds=DEAD_TIME):
                    rs.hdel('deads', url)
                    rs.hset('alives', url, json.dumps({'status':'init', 'address':p['address'], 'nm':p['nm'], 'type':p['type']}))

            time.sleep(600)


if __name__ == '__main__':
    ProxyProcess().run()
