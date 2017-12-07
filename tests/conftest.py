# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""
import os

import pytest
from mockredis import mock_strict_redis_client

from fulfil_client import Client
from fulfil_client.model import model_base


@pytest.fixture
def client():
    return Client('demo', os.environ['FULFIL_API_KEY'])


@pytest.fixture
def Model(client):
    return model_base(client)


@pytest.fixture
def ModelWithCache(client):
    return model_base(
        client,
        cache_backend=mock_strict_redis_client()
    )
