#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fulfil_client import Client
client = Client('<subdomain>', '<api_key>')


# =============
# Creating Sale
# =============

# Sale requires customer(contact) and address id.
Contact = client.model('party.party')
Sale = client.model('sale.sale')

# Get the contact first
contacts = Contact.search([('name', 'ilike', '%Jon%')])
contact, = Contact.get(contacts[0]['id'])

sale, = Sale.create([{
    'party': contact['id'],
    'shipment_address': contact['addresses'][0],
    'invoice_address': contact['addresses'][0],
}])

# ===========================
# Adding items(line) to Sale
# ===========================

Product = client.model('product.product')
Line = client.model('sale.line')

products = Product.search([('code', '=', 'IPHONE-6')])
iphone6, = Product.get(products[0]['id'])

products = Product.search([('code', '=', 'IPHONE-6S')])
iphone6s, = Product.get(products[0]['id'])


line1, = Line.create([{
    'sale': sale['id'],
    'product': iphone6['id'],
    'description': iphone6['rec_name'],
    'unit': iphone6['default_uom'],
    'unit_price': iphone6['list_price'],
    'quantity': 3
}])

line2, = Line.create([{
    'sale': sale['id'],
    'product': iphone6s['id'],
    'description': iphone6s['rec_name'],
    'unit': iphone6s['default_uom'],
    'unit_price': iphone6s['list_price'],
    'quantity': 1

}])

# ============================
# Creating Sale (Advanced)
# ============================

# Create sale with lines in single call!
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
