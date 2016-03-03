import json
import requests
from functools import partial
from trytond.protocols.jsonrpc import JSONDecoder, JSONEncoder


dumps = partial(json.dumps, cls=JSONEncoder)
loads = partial(json.loads, object_hook=JSONDecoder())


class Client(object):

    def __init__(self, subdomain, api_key):
        self.subdomain = subdomain
        self.api_key = api_key
        self.base_url = 'https://%s.fulfil.io/api/v1' % self.subdomain

        self.session = requests.Session()
        self.session.headers.update({'x-api-key': api_key})

    def model(self, name):
        return Model(self, name)


class Model(object):

    def __init__(self, client, model_name):
        self.client = client
        self.model_name = model_name

    @property
    def path(self):
        return '%s/model/%s' % (self.client.base_url, self.model_name)

    def get(self, id):
        return loads(
            self.client.session.get(
                self.path + '/%d' % id
            ).content
        )

    def search(self, filter, page=1, per_page=10, fields=None):
        response = self.client.session.get(
            self.path,
            params={
                'filter': dumps(filter or []),
                'page': page,
                'per_page': per_page,
                'field': fields,
            }
        )
        return loads(response.content)

    def create(self, data):
        response = self.client.session.post(
            self.path,
            data=dumps(data)
        )
        return loads(response.content)
