===============================
Fulfil IO Python Client
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
* Examples: https://github.com/fulfilio/fulfil-python-api/tree/master/examples.

Features
--------

* Ability to call models

Quickstart
----------

.. code:: python

    from fulfil_client import Client

    client = Client('<subdomain>', '<api_key>')

    Product = client.model('product.product')

    # find products
    some_products = Product.find()

    # find products that have a name similar to iphone
    iphones = Product.find(['name', 'ilike', 'iphone'])



Contacts
--------

Contact can have multiple addresses and contact mechanisms i.e. phone,
email.

.. code:: python

    from fulfil_client import Client
    client = Client('<subdomain>', '<api_key>')

    Contact = client.model('party.party')
    Country = client.model('country.country')
    Subdivision = client.model('country.subdivision')

    country_usa, = Country.find([('code', '=', 'US')])
    state_california, = Subdivision.find([('code', '=', 'US-CA')])

    # Creating a contact with address and contact mechanisms
    contact, = Contact.create([{
        'name': 'Jon Doe',
        'addresses': [('create', [{
            'name': 'Jone Doe Apartment',
            'street': '9805 Kaiden Grove',
            'city': 'New Leland',
            'zip': '57726',
            'country': country_usa['id'],
            'subdivision': state_california['id']
        }])],
        'contact_mechanisms': [('create', [{
            'type': 'phone',
            'value': '243243234'
        }, {
            'email': 'email',
            'value': 'hello@jondoe.com'
        }])]
    }])
    print contact

    # Searching for a contact
    contact, = Contact.find([('name', '=', 'Jon Doe')])
    print contact

    # Get a contact by ID
    contact = Contact.get(contact['id'])
    print contact


Products
--------

Products are grouped by templates, which have common information shared by
products a.k.a. variants.

.. code:: python

    from decimal import Decimal

    # Creating a Product Template
    Template = client.model('product.template')

    iphone, = Template.create([{
        'name': 'iPhone',
        'account_category': True,
    }])

    # Creating products
    Product = client.model('product.product')
    iphone6, = Product.create([{
        'template': iphone['id'],
        'variant_name': 'iPhone 6',
        'code': 'IPHONE-6',
        'list_price': Decimal('699'),
        'cost_price': Decimal('599'),
    }])

    # Another variation
    iphone6s, = Product.create([{
        'template': iphone['id'],
        'variant_name': 'iPhone 6S',
        'code': 'IPHONE-6S',
        'list_price': Decimal('899'),
        'cost_price': Decimal('699'),
    }])


Sale
----

.. code:: python

    contact = Contact.get(contact['id'])
    iphone6 = Product.get(iphone6['id'])
    iphone6s = Product.get(iphone6s['id'])

    # Creating a Sale
    Sale = client.model('sale.sale')
    sale, = Sale.create([{
        'party': contact['id'],
        'shipment_address': contact['addresses'][0],
        'invoice_address': contact['addresses'][0],
        'lines': [('create', [{
            'product': iphone6['id'],
            'description': iphone6['rec_name'],
            'unit': iphone6['default_uom'],
            'unit_price': iphone6['list_price'],
            'quantity': 3
        }, {
            'product': iphone6s['id'],
            'description': iphone6s['rec_name'],
            'unit': iphone6['default_uom'],
            'unit_price': iphone6s['list_price'],
            'quantity': 1
        }])]
    }])


Credits
---------

Fulfil.IO Inc.
