import json
import requests
from functools import partial, wraps
from .serialization import JSONDecoder, JSONEncoder


dumps = partial(json.dumps, cls=JSONEncoder)
loads = partial(json.loads, object_hook=JSONDecoder())


class ServerError(Exception):
    pass


def json_response(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        rv = function(*args, **kwargs)
        if not rv.status_code == requests.codes.ok:
            raise ServerError(loads(rv.content))
        return loads(rv.content)
    return wrapper


class Client(object):

    def __init__(self, subdomain, api_key):
        self.subdomain = subdomain
        self.api_key = api_key
        self.base_url = 'https://%s.fulfil.io/api/v1' % self.subdomain

        self.session = requests.Session()
        self.session.headers.update({'x-api-key': api_key})

        self.context = {}
        self.refresh_context()

    def refresh_context(self):
        """
        Get the default context of the user and save it
        """
        User = self.model('res.user')

        self.context = User.get_preferences(True)
        return self.context

    def today(self):
        Date = self.model('ir.date')
        rv = Date.today()
        return rv

    def model(self, name):
        return Model(self, name)

    def record(self, model_name, id):
        return Record(self.model(model_name), id)


class Record(object):
    def __init__(self, model, id):
        self.model = model
        self.id = id

    def __getattr__(self, name):
        return getattr(self.model, name)

    def update(self, data=None, **kwargs):
        """
        Update the record right away.

        :param data: dictionary of changes
        :param kwargs: possibly a list of keyword args to change
        """
        if data is None:
            data = {}
        data.update(kwargs)
        return self.model.write([self.id], data)


class Model(object):

    def __init__(self, client, model_name):
        self.client = client
        self.model_name = model_name

    def __getattr__(self, name):
        @json_response
        def proxy_method(*args, **kwargs):
            context = kwargs.pop('context', self.client.context)
            return self.client.session.put(
                self.path + '/%s' % name,
                dumps(args),
                params={
                    'context': dumps(context),
                }
            )
        return proxy_method

    @property
    def path(self):
        return '%s/model/%s' % (self.client.base_url, self.model_name)

    @json_response
    def get(self, id, context=None):
        ctx = self.client.context.copy()
        ctx.update(context or {})
        return self.client.session.get(
            self.path + '/%d' % id,
            params={
                'context': dumps(ctx),
            }
        )

    @json_response
    def find(self, filter=None, page=1, per_page=10, fields=None, context=None):
        """
        Find records that match the filter.

        Pro Tip: The fields could have nested fields names if the field is
        a relationship type. For example if you were looking up an order
        and also want to get the shipping address country then fields would be:

            `['shipment_address', 'shipment_address.country']`

        but country in this case is the ID of the country which is not very
        useful if you don't already have a map. You can fetch the country code
        by adding `'shipment_address.country.code'` to the fields.

        :param filter: A domain expression (Refer docs for domain syntax)
        :param page: The page to fetch to get paginated results
        :param per_page: The number of records to fetch per page
        :param fields: A list of field names to fetch.
        :param context: Any overrides to the context.
        """
        if filter is None:
            filter = []
        return self.client.session.get(
            self.path,
            params={
                'filter': dumps(filter or []),
                'page': page,
                'per_page': per_page,
                'field': fields,
                'context': dumps(context or self.client.context),
            }
        )
