# -*- coding: utf-8 -*-

import unittest

from domainchecker import Loader, Client, QUEUE, EXIT

DOMAINS = [
    'wp.pl',
    'clearcode.cc',
    'google.com',
    'facebook.com',
    'nasza-klasa.pl',
    'grono.net',
    'chce.to',
    'onet.pl'
]

HOST = 'localhost'
PORT = 11300

class  ClientTestCase(unittest.TestCase):
    def setUp(self):
        self.loader = Loader(HOST, PORT)
        self.loader.server.use(QUEUE)
        for domain in DOMAINS:
            self.loader.server.put(domain)
        self.loader.exit()

    def test_default_domains(self):
        client = Client(HOST, PORT)
        client.run('testowy')

if __name__ == '__main__':
    unittest.main()

