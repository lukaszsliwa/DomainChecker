# -*- coding: utf-8 -*-

import unittest
import types
from domainchecker import Domain

class  DomainTestCase(unittest.TestCase):

    def test_domain(self):
        domain = Domain('cziki.pl')
        domain.run()
        self.assertEquals(domain.name, 'cziki.pl')
        self.assertEquals(domain.active, True)
        self.assertEquals(domain.created, '2009.04.10')
        assert type(domain.alexa_rank) is types.IntType

    def test_empty_domain(self):
        domain = Domain('')
        domain.run()
        self.assertEquals(domain.name, '')

    def test_not_existed_domain(self):
        domain = Domain('adjkasd22wkfdlskfldskf.pl')
        domain.run()
        self.assertEquals(domain.name, 'adjkasd22wkfdlskfldskf.pl')
        self.assertEquals(domain.active, False)
        self.assertEquals(domain.created, 'n/a')

    def test_threading(self):
        domain = Domain('cziki.pl')
        domain.start()
        domain.join()

if __name__ == '__main__':
    unittest.main()

