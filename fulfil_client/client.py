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

    _local_methods = [
        'create', 'search', 'get'
    ]

    def __init__(self, client, model_name):
        self._client = client
        self._model_name = model_name

    @property
    def _path(self):
        return '%s/model/%s' % (self._client.base_url, self._model_name)

    def __getattribute__(self, name):
        if name.startswith('_') or name in self._local_methods:
            return object.__getattribute__(self, name)
        else:
            return partial(self._run, name)

    def _run(self, method_name, *args, **kwargs):
        id = kwargs.pop('id', None)
        if id:
            path = "%s/%s/%s" % (self._path, id, method_name)
        else:
            path = "%s/%s" % (self._path, method_name)
        response = self._client.session.put(
            path,
            data=dumps(args)
        )
        return loads(response.content)

    def get(self, id):
        return loads(
            self._client.session.get(
                self._path + '/%d' % id
            ).content
        )

    def search(self, filter, page=1, per_page=10, fields=None):
        response = self._client.session.get(
            self._path,
            params={
                'filter': dumps(filter or []),
                'page': page,
                'per_page': per_page,
                'field': fields,
            }
        )
        return loads(response.content)

    def create(self, data):
        response = self._client.session.post(
            self._path,
            data=dumps(data)
        )
        return loads(response.content)
