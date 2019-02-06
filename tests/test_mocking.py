#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import fulfil_client
from fulfil_client.contrib.mocking import MockFulfil


def api_calling_method():
    client = fulfil_client.Client('apple', 'apples-api-key')
    Product = client.model('product.product')
    products = Product.search_read_all([], None, ['id'])
    Product.write(
        [p['id'] for p in products],
        {'active': False}
    )
    return client


def test_mock_1():
    with MockFulfil('fulfil_client.Client') as mocked_fulfil:
        Product = mocked_fulfil.model('product.product')
        Product.search_read_all.return_value = [
            {'id': 1},
            {'id': 2},
            {'id': 3},
        ]

        # Call the function
        api_calling_method()

        # Now assert
        Product.search_read_all.assert_called()
        Product.search_read_all.assert_called_with([], None, ['id'])
        Product.write.assert_called_with(
            [1, 2, 3], {'active': False}
        )


def test_mock_context():
    "Ensure that old mocks die with the context"
    with MockFulfil('fulfil_client.Client') as mocked_fulfil:
        Product = mocked_fulfil.model('product.product')
        api_calling_method()
        Product.search_read_all.assert_called()

    # Start new context
    with MockFulfil('fulfil_client.Client') as mocked_fulfil:
        Product = mocked_fulfil.model('product.product')
        Product.search_read_all.assert_not_called()


def test_mock_different_return_vals():
    "Return different values based on mock side_effect"
    def lookup_products(domain):
        client = fulfil_client.Client('apple', 'apples-api-key')
        Product = client.model('product.product')
        return Product.search(domain)

    def fake_search(domain):
        # A fake search method that returns ids based on
        # domain.
        if domain == []:
            return [1, 2, 3, 4, 5]
        elif domain == [('salable', '=', True)]:
            return [1, 2, 3]

    with MockFulfil('fulfil_client.Client') as mocked_fulfil:
        Product = mocked_fulfil.model('product.product')
        Product.search.side_effect = fake_search
        assert lookup_products([]) == [1, 2, 3, 4, 5]
        assert lookup_products([('salable', '=', True)]) == [1, 2, 3]
