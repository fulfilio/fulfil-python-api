#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_fulfil_client
----------------------------------

Tests for `fulfil_client` module.
"""
import os
import unittest

from fulfil_client import Client, ServerError


class TestFulfilClient(unittest.TestCase):

    def setUp(self):
        try:
            self.client = Client('fulfil_demo', os.environ['FULFIL_API_KEY'])
        except KeyError:
            self.fail('No FULFIL_API_KEY in environment')

    def tearDown(self):
        pass

    def test_000_connection(self):
        Model = self.client.model('ir.model')
        self.assertTrue(len(Model.search([])) > 0)

    def test_010_connection(self):
        Model = self.client.model('ir.model')
        with self.assertRaises(ServerError):
            Model.search([], context=1)

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
