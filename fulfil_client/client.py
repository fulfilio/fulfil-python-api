import base64
import json
import logging
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from functools import partial, wraps

import requests
from .serialization import JSONDecoder, JSONEncoder
from .exceptions import (
    UserError, ClientError, ServerError, AuthenticationError
)
from .signals import response_received


request_logger = logging.getLogger('fulfil_client.request')
dumps = partial(json.dumps, cls=JSONEncoder)
loads = partial(json.loads, object_hook=JSONDecoder())


def json_response(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        rv = function(*args, **kwargs)
        if rv.status_code != requests.codes.ok:
            if rv.status_code == 400:
                # Usually an user error
                error = loads(rv.text)
                if error.get('type') == 'UserError':
                    # These are error messages meant to be displayed to the
                    # user.
                    raise UserError(error.get('message'), error.get('code'))
                else:
                    # Some unknown error type. Raise a generic client error
                    # with everything we have
                    raise ClientError(error, rv.status_code)
            elif rv.status_code == 401:
                # Bearer tokens may have expired or the user may have
                # logged out. Either way raise this error so the app
                # can decide how to handle logouts.
                raise AuthenticationError(loads(rv.text), rv.status_code)
            elif 402 <= rv.status_code and rv.status_code < 500:
                # 4XX range errors always have a JSON response
                # with a code, message and description.
                error = rv.text
                if rv.headers.get('Content-Type') == 'application/json':
                    error = loads(rv.text).get('message', error)
                raise ClientError(
                    error,
                    rv.status_code
                )
            else:
                # 5XX Internal Server errors
                raise ServerError(
                    rv.text, rv.status_code, rv.headers.get('X-Sentry-ID')
                )
        return loads(rv.text)
    return wrapper


class SessionAuth(requests.auth.AuthBase):
    "Session Authentication"
    type_ = 'Session'

    def __init__(self, login, user_id, session):
        self.login = login
        self.user_id = user_id
        self.session = session

    def __call__(self, r):
        r.headers['Authorization'] = 'Session ' + base64.b64encode(
            '%s:%s:%s' % (self.login, self.user_id, self.session)
        )
        return r


class BearerAuth(requests.auth.AuthBase):
    "Bearer Authentication"
    type_ = 'BearerAuth'

    def __init__(self, access_token):
        self.access_token = access_token

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + self.access_token
        return r


class APIKeyAuth(requests.auth.AuthBase):
    "API key based Authentication"
    type_ = 'APIKey'

    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self, r):
        r.headers['x-api-key'] = self.api_key
        return r


class Client(object):

    def __init__(self, subdomain,
                 api_key=None, context=None, auth=None,
                 user_agent="Python Client"):
        self.subdomain = subdomain

        if self.subdomain == 'localhost':
            self.host = 'http://localhost:8000'
        else:
            self.host = 'https://%s.fulfil.io' % self.subdomain

        self.base_url = '%s/api/v1' % self.host

        self.session = requests.Session()
        if api_key is not None:
            self.set_auth(APIKeyAuth(api_key))
        else:
            self.set_auth(auth)

        self.session.headers.update({
            'User-Agent': user_agent,
        })

        self.context = {}
        if context is not None:
            self.context.update(context)
        if context is None and self.session.auth:
            # context is not defined, but auth is there.
            # try and get a context
            self.refresh_context()

    def set_auth(self, auth):
        self.session.auth = auth
        if auth is None:
            return
        if isinstance(auth, BearerAuth):
            self.base_url = '%s/api/v2' % self.host

    def set_user_agent(self, user_agent):
        self.session.headers.update({
            'User-Agent': user_agent
        })

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

    def report(self, name):
        return Report(self, name)

    def wizard(self, name):
        return Wizard(self, name)

    def interactive_report(self, name):
        return InteractiveReport(self, name)

    def login(self, login, password, set_auth=False):
        """
        Attempts a login to the remote server
        and on success returns user id and session
        or None

        Warning: Do not depend on this. This will be deprecated
        with SSO.

        param set_auth: sets the authentication on the client
        """
        rv = self.session.post(
            self.host,
            dumps({
                "method": "common.db.login",
                "params": [login, password]
            }),
        )
        rv = loads(rv.content)['result']
        if set_auth:
            self.set_auth(
                SessionAuth(login, *rv)
            )
        return rv

    def is_auth_alive(self):
        "Return true if the auth is not expired, else false"
        model = self.model('ir.model')
        try:
            model.search([], None, 1, None)
        except ClientError as err:
            if err and err.message['code'] == 403:
                return False
            raise
        except Exception:
            raise
        else:
            return True


class WizardSession(object):
    """An object to represent a specific session
    """
    def __init__(self, wizard, context):
        self.wizard = wizard

        if context is None:
            context = {}
        self.context = context
        self.session_id, self.start_state, self.end_state = self.wizard.create(
            context=context
        )

        # Local state variables
        self.data = defaultdict(dict)
        self.state = None

        # Start the session
        self.execute(self.start_state)

    def execute(self, state, context=None):
        ctx = self.context.copy()
        if context is not None:
            ctx.update(context)

        self.state = state
        while self.state != self.end_state:
            result = self.parse_result(
                self.wizard.execute(
                    self.session_id,
                    self.data,
                    self.state,
                    ctx
                )
            )
            if 'view' in result:
                return result
        return result

    def parse_result(self, result):
        if 'view' in result:
            view = result['view']
            self.data[view['state']].update(
                view['defaults']
            )
        else:
            self.state = self.end_state
        return result

    def delete(self):
        """
        Delete the session
        """
        self.wizard.delete(self.session_id)


class Wizard(object):

    def __init__(self, client, wizard_name, **kwargs):
        self.client = client
        self.wizard_name = wizard_name
        self.context = kwargs.get('context', {})

    @contextmanager
    def session(self, **context):
        _session = WizardSession(self, context)
        yield _session
        _session.delete()

    @property
    def path(self):
        return '%s/wizard/%s' % (self.client.base_url, self.wizard_name)

    @json_response
    def execute(self, session_id, data, state, context=None):
        ctx = self.client.context.copy()
        ctx.update(context or {})
        request_logger.debug(
            "Wizard::%s.execute::%s" % (self.wizard_name, state)
        )
        rv = self.client.session.put(
            self.path + '/execute',
            dumps([session_id, data, state]),
            params={'context': dumps(ctx)}
        )
        # Call response signal
        return rv

    @json_response
    def create(self, context=None):
        ctx = self.client.context.copy()
        ctx.update(context or {})
        request_logger.debug("Wizard::%s.create" % (self.wizard_name,))
        rv = self.client.session.put(
            self.path + '/create',
            dumps([]),
            params={'context': dumps(ctx)}
        )
        # Call response signal
        return rv

    @json_response
    def delete(self, session_id):
        request_logger.debug("Wizard::%s.delete" % (self.wizard_name,))
        rv = self.client.session.put(
            self.path + '/delete',
            dumps([session_id])
        )
        # Call response signal
        return rv


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
            context = self.client.context.copy()
            context.update(kwargs.pop('context', {}))
            request_logger.debug(
                "%s.%s::%s::%s" % (
                    self.model_name, name, args, kwargs
                )
            )
            rv = self.client.session.put(
                self.path + '/%s' % name,
                dumps(args),
                params={
                    'context': dumps(context),
                }
            )
            response_received.send(rv)
            return rv
        return proxy_method

    @property
    def path(self):
        return '%s/model/%s' % (self.client.base_url, self.model_name)

    @json_response
    def get(self, id, context=None):
        ctx = self.client.context.copy()
        ctx.update(context or {})
        rv = self.client.session.get(
            self.path + '/%d' % id,
            params={
                'context': dumps(ctx),
            }
        )
        response_received.send(rv)
        return rv

    def search_read_all(self, domain, order, fields, batch_size=500,
                        context=None, offset=0, limit=None):
        """
        An endless iterator that iterates over records.

        :param domain: A search domain
        :param order: The order clause for search read
        :param fields: The fields argument for search_read
        :param batch_size: The optimal batch size when sending paginated
                           requests
        """
        if context is None:
            context = {}

        if limit is None:
            # When no limit is specified, all the records
            # should be fetched.
            record_count = self.search_count(domain, context=context)
            end = record_count + offset
        else:
            end = limit + offset

        for page_offset in range(offset, end, batch_size):
            if page_offset + batch_size > end:
                batch_size = end - page_offset
            for record in self.search_read(
                    domain, page_offset, batch_size,
                    order, fields, context=context):
                yield record

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
        rv = self.client.session.get(
            self.path,
            params={
                'filter': dumps(filter or []),
                'page': page,
                'per_page': per_page,
                'field': fields,
                'context': dumps(context or self.client.context),
            }
        )
        response_received.send(rv)
        return rv

    def attach(self, id, filename, url):
        """Add an attachmemt to record from url

        :param id: ID of record
        :param filename: File name of attachment
        :param url: Public url to download file from.
        """
        Attachment = self.client.model('ir.attachment')
        return Attachment.add_attachment_from_url(
            filename, url, '%s,%s' % (self.model_name, id)
        )


class Report(object):

    def __init__(self, client, report_name):
        self.client = client
        self.report_name = report_name

    @property
    def path(self):
        return '%s/report/%s' % (self.client.base_url, self.report_name)

    @json_response
    def execute(self, records=None, data=None, **kwargs):
        context = self.client.context.copy()
        context.update(kwargs.pop('context', {}))
        rv = self.client.session.put(
            self.path,
            json={
                'objects': records or [],
                'data': data or {},
            },
            params={
                'context': dumps(context),
            }
        )
        response_received.send(rv)
        return rv


class InteractiveReport(object):

    def __init__(self, client, model_name):
        self.client = client
        self.model_name = model_name

    @property
    def path(self):
        return '%s/model/%s/execute' % (
            self.client.base_url, self.model_name
        )

    @json_response
    def execute(self, **kwargs):
        context = self.client.context.copy()
        context.update(kwargs.pop('context', {}))
        rv = self.client.session.put(
            self.path,
            dumps([kwargs]),
            params={
                'context': dumps(context),
            }
        )
        response_received.send(rv)
        return rv


class AsyncResult(object):
    """
    When the server returns an AsyncResult (usually for long running tasks),
    an instance of this class is created in the response. The object provides
    a convenient wrapper with which you can poll for the status of the task
    and result.
    """

    PENDING = 'PENDING'
    STARTED = 'STARTED'
    FAILURE = 'FAILURE'
    SUCCESS = 'SUCCESS'
    RETRY = 'RETRY'

    def __init__(self, task_id, token, client):
        self.task_id = task_id
        self.token = token
        self.client = client
        self.result = None
        self.state = self.PENDING
        self.start_time = datetime.utcnow()

    @property
    def path(self):
        return '%s/async-result' % (self.client.base_url)

    def bind(self, client):
        self.client = client
        return self

    @json_response
    def _fetch_result(self):
        if self.client is None:
            raise Exception(
                "Unbound AsyncResults cannot refresh status.\n"
                "Hint: Bind `result.bind(client)` and try again."
            )
        rv = self.client.session.post(
            self.path,
            json={
                'tasks': [
                    [self.task_id, self.token]
                ]
            },
        )
        response_received.send(rv)
        return rv

    def refresh_if_needed(self):
        """
        Refresh the status of the task from server if required.
        """
        if self.state in (self.PENDING, self.STARTED):
            try:
                response, = self._fetch_result()['tasks']
            except (KeyError, ValueError):
                raise Exception(
                    "Unable to find results for task."
                )

            if 'error' in response:
                self.state == self.FAILURE
                raise ServerError(response['error'])

            if 'state' in response:
                self.state = response['state']
                self.result = response['result']

    def failed(self):
        """
        Returns true of the task failed
        """
        self.refresh_if_needed()
        return self.state == self.FAILURE

    def ready(self):
        """
        Returns True if the task has been executed.

        If the task is still running, pending, or is waiting for retry then
        False is returned.
        """
        self.refresh_if_needed()
        return self.state == self.SUCCESS

    def wait(self, timeout=None):
        """
        Wait until task is ready, and return its result.

        Not implemented yet
        """
        raise Exception("Not implemented yet")

    @property
    def time_lapsed(self):
        """
        Time lapsed since the task was started

        Returned only when the task is still in progress
        """
        return datetime.utcnow() - self.start_time
