# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""
import pytest
import redis

from fulfil_client import Client, BearerAuth
from fulfil_client.model import model_base


@pytest.fixture
def client():
    return Client('demo', 'test-api-key')


@pytest.fixture
def oauth_client():
    return Client(
        'demo', auth=BearerAuth('user-test-token')
    )


@pytest.fixture
def Model(client):
    return model_base(client)


@pytest.fixture
def ModelWithCache(client):
    return model_base(
        client,
        cache_backend=redis.StrictRedis(host='localhost', port=6379, db=0)
    )
