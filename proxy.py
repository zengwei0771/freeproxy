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


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)


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
                dom = BeautifulSoup(r.content, "html.parser", from_encoding="UTF-8")
                for tr in dom.find('table', id='ip_list').findAll('tr'):
                    tds = tr.findAll('td')
                    if len(tds) == 0 or tds[5].text.strip() != 'HTTP':
                        continue
                    host = tds[1].text.strip()
                    port = int(tds[2].text.strip())
                    proxys.append('http://%s:%d' % (host, port))
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
                dom = BeautifulSoup(r.content, "html.parser", from_encoding="UTF-8")
                for tr in dom.find('div', id='list').findAll('tr'):
                    tds = tr.findAll('td')
                    if len(tds) == 0 or tds[3].text.strip() != 'HTTP':
                        continue
                    host = tds[0].text.strip()
                    port = int(tds[1].text.strip())
                    proxys.append('http://%s:%d' % (host, port))
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
                dom = BeautifulSoup(r.content, "html.parser", from_encoding="UTF-8")
                for tr in dom.find('table').findAll('tr'):
                    tds = tr.findAll('td')
                    if len(tds) == 0 or tds[3].text.strip() != 'HTTP':
                        continue
                    host = tds[0].text.strip()
                    port = int(tds[1].text.strip())
                    proxys.append('http://%s:%d' % (host, port))
        except Exception, e:
            logging.error(str(e))
        return proxys

    @staticmethod
    def fetch_goubanjia(req=requests):
        proxys = []
        try:
            r = req.get('http://proxy.goubanjia.com/free/gngn/index.shtml',
                             headers=HEADERS, timeout=8)
            dom = BeautifulSoup(r.content, "html.parser", from_encoding="UTF-8")
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
                proxys.append('http://%s:%d' % (host, port))
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


class FetchProxyThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        self.pr = ProxysRequest([])

    def run(self):
        self.redis.delete('alives')
        self.redis.delete('deads')

        while True:
            alives = self.redis.hgetall('alives')
            deads = self.redis.hgetall('deads')
            proxys = []
            for p in alives:
                alives[p] = json.loads(alives[p])
                if alives[p]['status'] != 'init':
                    proxys.append(p)
            if len(proxys) > 10:
                self.pr.update(proxys)
                ps = Proxys.fetch_xici(self.pr) + Proxys.fetch_kuai(self.pr) + \
                        Proxys.fetch_big(self.pr)
            else:
                ps = Proxys.fetch_xici() + Proxys.fetch_kuai() + Proxys.fetch_big()
            print self.pr.proxys

            now = datetime.now()
            for p in ps:
                if not alives.get(p) and not deads.get(p):
                    self.redis.hset('alives', p, json.dumps({'status':'init'}))
                elif deads.get(p) and datetime.strptime(deads[p], '%Y-%m-%d %H:%M:%S') < now - timedelta(seconds=600):
                    self.redis.hdel('deads', p)
                    self.redis.hset('alives', p, json.dumps({'status':'init'}))

            time.sleep(600)


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

                if Proxys.test_proxy(proxy):
                    self.redis.hset('alives',
                                    proxy,
                                    json.dumps({'status':'living', 'time':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}))
                else:
                    self.redis.hdel('alives', proxy)
                    self.redis.hset('deads', proxy, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

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
                    if alives[p]['status'] == 'init' or datetime.strptime(alives[p]['time'], '%Y-%m-%d %H:%M:%S') < now - timedelta(seconds=600):
                        tochecks.append(p)

                [in_.put(p) for p in tochecks]

            time.sleep(5)

        [in_.put(None) for i in range(self.worker_num)]
        [workers[i].join() for i in range(self.worker_num)]


def main():
    cpt = CheckProxyThread()
    cpt.setDaemon(True)
    cpt.start()

    fpt = FetchProxyThread()
    fpt.setDaemon(True)
    fpt.start()

    time.sleep(100000000)


if __name__ == '__main__':
    #print Proxys.get_proxys()
    #print Proxys.test_proxy('http://39.88.192.207:81')
    #print Proxys.fetch_xici(['http://60.13.74.143:80'])
    main()
