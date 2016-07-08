# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""
import os

import pytest

from fulfil_client import Client


@pytest.fixture
def client():
    return Client('fulfil_demo', os.environ['FULFIL_API_KEY'])
