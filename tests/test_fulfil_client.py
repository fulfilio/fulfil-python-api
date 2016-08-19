#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_fulfil_client
----------------------------------

Tests for `fulfil_client` module.
"""
import pytest
from fulfil_client import ServerError


def test_find(client):
    IRModel = client.model('ir.model')
    ir_models = IRModel.find([])
    assert len(ir_models) > 0
    assert ir_models[0]['id']
    assert ir_models[0]['rec_name']


def test_find_no_filter(client):
    IRModel = client.model('ir.model')
    ir_models = IRModel.find()
    assert len(ir_models) > 0
    assert ir_models[0]['id']
    assert ir_models[0]['rec_name']


def test_raises_server_error(client):
    Model = client.model('ir.model')
    with pytest.raises(ServerError):
        Model.search([], context=1)
