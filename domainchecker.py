# -*- coding: utf-8 -*-
import time
import sys
import urllib2
from beanstalk import serverconn
from threading import Thread
from BeautifulSoup import BeautifulSoup
import re
import csv

__author__="crh"
__date__ ="$2010-05-18 18:17:13$"

QUEUE = 'domains'
EXIT = '~!@#$%^&*'

class Domain(Thread):
    '''
    Domain class with information about:
        * page rank
        * alexa rank
        * domain created date
        * cached by google
    '''
    def __init__(self, name):
        Thread.__init__(self)
        self._name = name
        self._active = False
        self._cached_by_google = 0
        self._page_rank = 'n/a'
        self._alexa_rank = 'n/a'
        self._created = 'n/a'

    @staticmethod
    def _whois(name):
        '''
        Makes "who.is" url
        '''
        return 'http://who.is/whois/' + str(name) + '/'

    @staticmethod
    def _google_info(name):
        '''
        Makes "google info" url
        '''
        return 'http://webcache.googleusercontent.com/search?hl=en&q=cache%3A' + str(name)

    def _set_active(self, html):
        appears = 'appears to be available'
        self._active = False if appears in html else True

    def _set_created(self, items):
        for item in items:
            if re.match(r'^created:(.+)$', item):
                self._created = item.replace('created:', '').strip()
                break

    def _set_alexa_rank(self, items):
        for i, item in enumerate(items):
            if re.match(r'^Alexa Trend/Rank:$', item):
                self._alexa_rank = int(items[i+1].replace('1 Month:', '').strip().replace(',', ''))
                break

    def _set_cached_by_google(self):
        pass

    def _set_page_rank(self):
        pass

    def run(self):

        # ma trzy próby na pobranie informacji
        for i in [1,2,3]:
            try:
                html = urllib2.urlopen(self._whois(self.name))
            except urllib2.URLError, e:
                time.sleep(2 * i)
                print 'Ponowna (%s) próba odczytania informacji o %s' % (i, self.name)
            else:
                break

        bs = BeautifulSoup(html)
        self._set_active(bs.renderContents())
        site_info = BeautifulSoup(str(bs.find('div', { 'id': 'site_info' })))
        registry_info = BeautifulSoup(str(bs.find('span', { 'id': 'registry_whois' })))
        for info in [site_info, registry_info]:
            for tag in info.findAll(True):
                if tag.name in ['img', 'br', 'a']:
                    tag.extract()
        items = registry_info.renderContents().replace('&nbsp;', '').splitlines() + \
            site_info.renderContents().replace('&nbsp;', '').splitlines()
        self._set_created(items)
        self._set_alexa_rank(items)
        #self._set_cached_by_google()
        #self._set_page_rank()

    @property
    def name(self):
        '''
        Gets the domain name
        '''
        return self._name

    @property
    def page_rank(self):
        '''
        Gets the page rank
        '''
        return self._page_rank

    @property
    def alexa_rank(self):
        '''
        Gets the alexa rank
        '''
        return self._alexa_rank

    @property
    def created(self):
        '''
        Gets the domain age
        '''
        return self._created.split(' ')[0]

    @property
    def active(self):
        '''
        Is active?
        '''
        return self._active

    @property
    def cached_by_google(self):
        '''
        Gets true if page is cached by google
        '''
        return self._cached_by_google

class Base(object):
    def __init__(self, host, port):
        self._host = host
        self._port = int(port)
        self._conn = serverconn.ServerConn(host, port)

    @property
    def server(self):
        return self._conn

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    def run(self, filename):
        '''
        Runs something
        '''
        pass

class Loader(Base):
    '''
    Loader puts all domains into the beanstalkd
    '''
    def __init__(self, host, port):
        '''
        Loader init
        '''
        Base.__init__(self, host, int(port))

    def run(self, filename):
        '''
        Reads domains from file and puts them.
        '''
        self.server.use(QUEUE)
        with open(filename) as f:
            for domain in f:
                self.server.put(domain.strip())
                print domain.strip()
        self.exit()

    def exit(self):
        self.server.put(EXIT)

class Client(Base):
    '''
    Client reads domains from beanstalkd and checks information
    '''
    def __init__(self, host, port):
        Base.__init__(self, host, int(port))
        self._threads = []

    def run(self, filename):
        '''
        Read domains, check informations and make a raport.
        '''
        self.server.watch(QUEUE)
        self.server.ignore("default")
        try:
            while True:
                job = self.server.reserve()
                
                if job['data'] == EXIT:
                    self.server.delete(job['jid'])
                    break

                if job['bytes'] != 0:
                    domain = Domain(job['data'])
                    print 'Pobieranie danych o', domain.name
                    self._threads.append(domain)
                    domain.start()
                
                self.server.delete(job['jid'])
                time.sleep(1)

            output = []
            output = csv.writer(open(filename + '.csv', 'wb'))

            for domain in self._threads:
                domain.join()
                output.writerow([domain.name, domain.page_rank, domain.alexa_rank, domain.created, domain.cached_by_google])
                
        except KeyboardInterrupt, e:
            pass


if __name__ == "__main__":
    
    try:
        
        type, host, port, filename = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
        if type == 'loader':
            Loader(host, port).run(filename)
        elif type == 'client':
            Client(host, port).run(filename)

    except Exception, e:
        print e
        print "domainchecker.py loader [host] [port] [filename]"
        print "domainchecker.py client [host] [port] [filename]"

