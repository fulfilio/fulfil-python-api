===============================
fulfil_client
===============================

.. image:: https://img.shields.io/pypi/v/fulfil_client.svg
        :target: https://pypi.python.org/pypi/fulfil_client

.. image:: https://img.shields.io/travis/fulfilio/fulfil_client.svg
        :target: https://travis-ci.org/fulfilio/fulfil-python-api

.. image:: https://readthedocs.org/projects/fulfil-python-api/badge/?version=latest
        :target: https://readthedocs.org/projects/fulfil-python-api/?badge=latest
        :alt: Documentation Status


Fulfil REST API Client in Python

* Free software: ISC license
* Documentation: https://fulfil-python-api.readthedocs.org.

Features
--------

* Ability to call models

Quickstart
----------

::

    from fulfil_client import Client

    client = Client('<subdomain>', '<api_key>')

    Product = client.model('product.product')
    iphones = Product.search(['name', 'ilike', 'iphone'])


Credits
---------

Fulfil.IO Inc.
