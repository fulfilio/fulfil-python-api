#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fulfil_client import Client
client = Client('<subdomain>', '<api_key>')


# =================
# Creating Contacts
# =================

Contact = client.model('party.party')
contact, = Contact.create([{'name': 'Jon Doe'}])

# You can create multiple contacts in one request too ;-)
contacts = Contact.create([
    {
        'name': 'Jon Doe'
    }, {
        'name': 'Matt Bower'
    }, {
        'name': 'Joe Blow'
    }
])

# ================
# Creating Address
# ================

# Note: You need a contact id first to create an address
#
# Add an address to the contact created above
Address = client.model('party.address')
address, = Address.create([{
    'party': contact['id'],
    'name': 'Jone Doe Apartment',
    'street': '9805 Kaiden Grove',
    'city': 'New Leland',
    'zip': '57726',
}])

# Address with country and subdivision - you first need to fetch the
# id of country and subdivision.
Country = client.model('country.country')
Subdivision = client.model('country.subdivision')

country_usa, = Country.find([('code', '=', 'US')])
state_california, = Subdivision.find([('code', '=', 'US-CA')])

address, = Address.create([{
    'party': contact['id'],
    'name': 'Jone Doe Apartment',
    'street': '9805 Kaiden Grove',
    'city': 'New Leland',
    'zip': '57726',
    'country': country_usa['id'],
    'subdivision': state_california['id'],
}])


# ===========================
# Creating Contact Mechanism
# ===========================

# Creating a phone number for contact
ContactMechanism = client.model('party.contact_mechanism')

phone, = ContactMechanism.create([{
    'party': contact['id'],
    'type': 'phone',
    'value': '1321322143',
}])

# Creating an email address for contact
email, = ContactMechanism.create([{
    'party': contact['id'],
    'type': 'email',
    'value': 'hola@jondoe@example.com',
}])


# ============================
# Creating Contacts (Advanced)
# ============================

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


# ===================
# Searching a Contact
# ===================


# Search contact by name
print Contact.find([('name', '=', 'Jon Doe')])

# Get a contact by ID
print Contact.get(contact['id'])
