#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a complete example where you have to push an order to Fulfil.IO. The
steps are:

    1. Fetch inventory for the products that have been sold
    2. Create new customer, address
    3. Process the order.
"""
from datetime import date
from decimal import Decimal

from fulfil_client import Client
client = Client('<subdomain>', '<api_key>')


def get_warehouses():
    """
    Return the warehouses in the system
    """
    StockLocation = client.model('stock.location')
    return StockLocation.search(
        [('type', '=', 'warehouse')],   # filter just warehouses
        fields=['code', 'name']         # Get the code and name fields
    )


def get_product_inventory(product_id, warehouse_ids):
    """
    Return the product inventory in each location. The returned response
    will look like::

        {
            12: {       // Product ID
                4: {    // Location ID
                    'quantity_on_hand': 12.0,
                    'quantity_available': 8.0
                },
                5: {    // Location ID
                    'quantity_on_hand': 8.0,
                    'quantity_available': 8.0
                },
            },
            126: {      // Product ID
                4: {    // Location ID
                    'quantity_on_hand': 16.0,
                    'quantity_available': 15.0
                },
                5: {    // Location ID
                    'quantity_on_hand': 9.0,
                    'quantity_available': 8.0
                },
            }
        }

    Read more:
    http://docs.fulfiliorestapi.apiary.io/#reference/product/product-inventory
    """
    Product = client.model('product.product')

    return Product.get_product_inventory(
        [product_id], warehouse_ids
    )[product_id]


def get_customer(code):
    """
    Fetch a customer with the code.
    Returns None if the customer is not found.
    """
    Party = client.model('party.party')
    results = Party.search([('code', '=', code)])
    if results:
        return results[0]['id']


def get_address(customer_id, data):
    """
    Easier to fetch the addresses of customer and then check one by one.

    You can get fancy by using some validation mechanism too
    """
    Address = client.model('party.address')

    addresses = Address.search(
        [('party', '=', customer_id)],
        fields=[
            'name', 'street', 'street_bis', 'city', 'zip',
            'subdivision.code', 'country.code'
        ]
    )
    for address in addresses:
        if (
                address['name'] == data['name'] and
                address['street'] == data['street'] and
                address['street_bis'] == data['street_bis'] and
                address['city'] == data['city'] and
                address['zip'] == data['zip'] and
                address['subdivision.code'].endswith(data['state']) and
                address['country.code'] == data['country']):
            return address['id']


def create_address(customer_id, data):
    """
    Create an address and return the id
    """
    Address = client.model('party.address')
    Country = client.model('country.country')
    Subdivision = client.model('country.subdivision')

    country, = Country.search([('code', '=', data['country'])])
    state, = Subdivision.search([
        ('code', 'ilike', '%-' + data['state']),    # state codes are US-CA, IN-KL
        ('country', '=', country['id'])
    ])

    address, = Address.create([{
        'party': customer_id,
        'name': data['name'],
        'street': data['street'],
        'street_bis': data['street_bis'],
        'city': data['city'],
        'zip': data['zip'],
        'country': country['id'],
        'subdivision': state['id'],
    }])
    return address['id']


def create_customer(name, email, phone):
    """
    Create a customer with the name.
    Then attach the email and phone as contact methods
    """
    Party = client.model('party.party')
    ContactMechanism = client.model('party.contact_mechanism')

    party, = Party.create([{'name': name}])

    # Bulk create the email and phone
    ContactMechanism.create([
        {'type': 'email', 'value': email, 'party': party},
        {'type': 'phone', 'value': phone, 'party': party},
    ])

    return party


def get_product(code):
    """
    Given a product code/sku return the product id
    """
    Product = client.model('product.product')
    return Product.search(
        [('code', '=', code)],  # Filter
        fields=['code', 'variant_name', 'cost_price']
    )[0]


def create_order(order):
    """
    Create an order on fulfil from order_details.
    See the calling function below for an example of the order_details
    """
    SaleOrder = client.model('sale.sale')
    SaleOrderLine = client.model('sale.line')

    # Check if customer exists, if not create one
    customer_id = get_customer(order['customer']['code'])
    if not customer_id:
        customer_id = create_customer(
            order['customer']['name'],
            order['customer']['email'],
            order['customer']['phone'],
        )

    # No check if there is a matching address
    invoice_address = get_address(
        customer_id,
        order['invoice_address']
    )
    if not invoice_address:
        invoice_address = create_address(
            customer_id,
            order['invoice_address']
        )

    # See if the shipping address exists, if not create it
    shipment_address = get_address(
        customer_id,
        order['shipment_address']
    )
    if not shipment_address:
        shipment_address = create_address(
            customer_id,
            order['shipment_address']
        )

    sale_order_id, = SaleOrder.create([{
        'reference': order['number'],
        'sale_date': order['date'],
        'party': customer_id,
        'invoice_address': invoice_address,
        'shipment_address': shipment_address,
    }])

    # fetch inventory of all the products before we create lines
    warehouses = get_warehouses()
    warehouse_ids = [warehouse['id'] for warehouse in warehouses]

    lines = []
    for item in order['items']:
        # get the product. We assume ti already exists.
        product = get_product(item['product'])

        # find the first location that has inventory
        product_inventory = get_product_inventory(product, warehouse_ids)
        for location, quantities in product_inventory.items():
            if quantities['quantity_available'] >= item['quantity']:
                break

        lines.append({
            'sale': sale_order_id,
            'product': product,
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'warehouse': location,
        })

    SaleOrderLine.create(lines)

    SaleOrder.quote([sale_order_id])
    SaleOrder.confirm([sale_order_id])


if __name__ == '__main__':
    create_order({
        'customer': {
            'code': 'A1234',
            'name': 'Sharoon Thomas',
            'email': 'st@fulfil.io',
            'phone': '650-999-9999',
        },
        'number': 'SO-12345',           # an order number
        'date': date.today(),           # An order date
        'invoice_address': {
            'name': 'Sharoon Thomas',
            'street': '444 Castro St.',
            'street2': 'STE 1200',
            'city': 'Mountain View',
            'zip': '94040',
            'state': 'CA',
            'country': 'US',
        },
        'shipment_address': {
            'name': 'Office Manager',
            'street': '444 Castro St.',
            'street2': 'STE 1200',
            'city': 'Mountain View',
            'zip': '94040',
            'state': 'CA',
            'country': 'US',
        },
        'items': [
            {
                'product': 'P123',
                'quantity': 2,
                'unit_price': Decimal('99'),
                'description': 'P123 is a fabulous product',
            },
            {
                'product': 'P456',
                'quantity': 1,
                'unit_price': Decimal('100'),
                'description': 'Yet another amazing product',
            },
        ]
    })
