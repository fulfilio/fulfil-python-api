#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_fulfil_client
----------------------------------

Tests for `fulfil_client` module.
"""
import pytest
from fulfil_client import Client, ClientError, ServerError


def test_find(client):
    IRModel = client.model('ir.model')
    ir_models = IRModel.find([])
    assert len(ir_models) > 0
    assert ir_models[0]['id']
    assert ir_models[0]['rec_name']


def test_search_read_all(client):
    IRModel = client.model('ir.model')
    total_records = IRModel.search_count([])
    ir_models = list(
        IRModel.search_read_all([], None, ['rec_name'], batch_size=50)
    )

    # the default batch size is 500 and the total records
    # being greater than that is an important part of the test.
    assert total_records > 500
    assert total_records == len(set([r['id'] for r in ir_models]))

    assert len(ir_models) == total_records
    assert len(ir_models) > 10
    assert ir_models[0]['id']
    assert ir_models[0]['rec_name']

    first_record = ir_models[0]

    # Offset and then fetch
    ir_models = list(
        IRModel.search_read_all(
            [], None, ['rec_name'], offset=10
        )
    )
    assert len(ir_models) == total_records - 10
    assert ir_models[0]['id'] != first_record['id']

    # Smaller batch size and offset
    ir_models = list(
        IRModel.search_read_all(
            [], None, ['rec_name'], batch_size=5, offset=10
        )
    )
    assert len(ir_models) == total_records - 10
    assert ir_models[0]['id'] != first_record['id']

    # Smaller batch size and limit
    ir_models = list(
        IRModel.search_read_all(
            [], None, ['rec_name'], batch_size=5, limit=10
        )
    )
    assert len(ir_models) == 10
    assert ir_models[0]['id'] == first_record['id']

    #  default batch size and limit
    ir_models = list(
        IRModel.search_read_all(
            [], None, ['rec_name'], limit=10
        )
    )
    assert len(ir_models) == 10
    assert ir_models[0]['id'] == first_record['id']

    # small batch size and limit and offset
    ir_models = list(
        IRModel.search_read_all(
            [], None, ['rec_name'],
            batch_size=5, limit=10, offset=5
        )
    )
    assert len(ir_models) == 10
    assert ir_models[0]['id'] != first_record['id']

    # default batch size and limit and offset
    ir_models = list(
        IRModel.search_read_all(
            [], None, ['rec_name'],
            limit=10, offset=5
        )
    )
    assert len(ir_models) == 10
    assert ir_models[0]['id'] != first_record['id']


def test_find_no_filter(client):
    IRModel = client.model('ir.model')
    ir_models = IRModel.find()
    assert len(ir_models) > 0
    assert ir_models[0]['id']
    assert ir_models[0]['rec_name']


def test_raises_server_error(client):
    Model = client.model('ir.model')
    with pytest.raises(ServerError):
        Model.search(1)


def test_raises_client_error():
    with pytest.raises(ClientError):
        Client('demo', 'wrong-api-key')
