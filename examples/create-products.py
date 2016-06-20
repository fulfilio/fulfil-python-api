#!/usr/bin/env python
# -*- coding: utf-8 -*-
from decimal import Decimal

from fulfil_client import Client
client = Client('<subdomain>', '<api_key>')


# ==========================
# Creating Product Template
# ==========================

Template = client.model('product.template')

iphone, = Template.create([{
    'name': 'iPhone',
    'account_category': True,
}])

# =================
# Creating Products
# =================

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


# ============================
# Creating Products (Advanced)
# ============================

# Create template and products in single call!
print Template.create([{
    'name': 'iPhone',
    'account_category': True,
    'products': [('create', [{
        'variant_name': 'iPhone 6',
        'code': 'IPHONE-6',
        'list_price': Decimal('699'),
        'cost_price': Decimal('599'),

    }, {
        'variant_name': 'iPhone 6S',
        'code': 'IPHONE-6S',
        'list_price': Decimal('899'),
        'cost_price': Decimal('699'),
    }])]
}])


# ======================
# Searching for Products
# ======================

# Search by SKU(exact match)
print Product.search([('code', '=', 'IPHONE-6')])

# Search by SKU(pattern match)
print Product.search([('code', 'ilike', '%IPHONE%')])

# Search by name(pattern match, case insensitive)
print Product.search([('name', 'ilike', '%Phone%')])

# Get a product by ID
print Product.get(iphone6s['id'])
