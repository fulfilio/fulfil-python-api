"""
Translate fulfil requests to curl.

Need to have the following installed

pip install curlify blinker
"""
import os
import curlify
from fulfil_client import Client
from fulfil_client.signals import response_received, signals_available

fulfil = Client(os.environ['FULFIL_SUBDOMAIN'], os.environ['FULFIL_API_KEY'])

print("Signal Available?:", signals_available)

Product = fulfil.model('product.product')

products = Product.find([])

@response_received.connect
def curlify_response(response):
    print('=' * 80)
    print(curlify.to_curl(response.request))
    print('=' * 80)
    print(response.content)
    print('=' * 80)


print Product.get_next_available_date(
    products[0]['id'],
    1,
    4,
    True
)
