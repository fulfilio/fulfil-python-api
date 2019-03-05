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

Installation
------------

.. code:: sh

    pip install fulfil_client


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


Fetching an interactive report (sales by month)
-----------------------------------------------

The report data (including rendering) information can be fetched
over the API.

Below is the example code to fetch sales by month report.

.. code:: python

    report = client.interactive_report('sales_by_month.ireport')
    data = report.execute(start_date=date(2017,1,1), end_date=date(2017, 12,1))



Using Session Auth
------------------

.. code:: python

    from fulfil_client import Client, SessionAuth

    client = Client('subdomain')
    user_id, session = client.login('username', 'password')
    client.set_auth(SessionAuth(user_id, session))


Using Bearer Auth
-----------------

.. code:: python

    from fulfil_client import Client, BearerAuth

    client = Client('subdomain')
    client.set_auth(BearerAuth(bearer_token))


Using OAuth Session
-------------------

Flask example

.. code:: python

    from fulfil_client.oauth import Session
    from fulfil_client import Client, BearerAuth

    Session.setup(CLIENT_ID, CLIENT_SECRET)
    fulfil_session = Session('localhost')  # Provide subdomain

    @app.route('/')
    def index():
        callback_url = url_for('authorized')
        if 'oauth_token' not in session:
            authorization_url, state = fulfil_session.create_authorization_url(
                redirect_uri=callback_url, scope=['user_session']
            )
            session['oauth_state'] = state
            return redirect(authorization_url)
        client = Client('subdomain')
        client.set_auth(BearerAuth(session['oauth_token']['access_token']))
        Party = client.model('party.party')
        return jsonify(Party.find())

    @app.route('/authorized')
    def authorized():
        """Callback route to fetch access token from grant code
        """
        token = fulfil_session.get_token(code=request.args.get('code'))
        session['oauth_token'] = token
        return jsonify(oauth_token=token)


Testing
-------

The libary also provides a mocking function powered by the mock library
of python.

For example, if you want to test the function below

.. code-block:: python

    def api_calling_method():
        client = fulfil_client.Client('apple', 'apples-api-key')
        Product = client.model('product.product')
        products = Product.search_read_all([], None, ['id'])
        Product.write(
            [p['id'] for p in products],
            {'active': False}
        )
        return client


Then the test case can mock the API call

.. code-block:: python

    def test_mock_1():
        with MockFulfil('fulfil_client.Client') as mocked_fulfil:
            Product = mocked_fulfil.model('product.product')
            # Set the return value of the search call without
            # hitting the server.
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

The `Product` object returned is a `mock.Mock` object and supports all
of the `assertions supported
<https://docs.python.org/3/library/unittest.mock.html#unittest.mock.Mock.assert_called>`_
by python Mock objects.


Credits
---------

Fulfil.IO Inc.
