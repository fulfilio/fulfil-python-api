# -*- coding: UTF-8 -*-
import datetime
from decimal import Decimal
from collections import namedtuple
from functools import partial
try:
    import simplejson as json
except ImportError:
    import json
import base64
import isodate


CONTENT_TYPE = 'application/vnd.fulfil.v3+json'


class JSONDecoder(object):

    decoders = {}

    @classmethod
    def register(cls, klass, decoder):
        assert klass not in cls.decoders
        cls.decoders[klass] = decoder

    def __call__(self, dct):
        if dct.get('__class__') in self.decoders:
            return self.decoders[dct['__class__']](dct)
        return dct


def register_decoder(klass):
    def decorator(decoder):
        assert klass not in JSONDecoder.decoders
        JSONDecoder.decoders[klass] = decoder
    return decorator


@register_decoder('datetime')
def datetime_decoder(v):
    if v.get('iso_string'):
        return isodate.parse_datetime(v['iso_string'])
    return datetime.datetime(
        v['year'], v['month'], v['day'],
        v['hour'], v['minute'], v['second'], v['microsecond']
    )


@register_decoder('date')
def date_decoder(v):
    if v.get('iso_string'):
        return isodate.parse_date(v['iso_string'])
    return datetime.date(
        v['year'], v['month'], v['day'],
    )


@register_decoder('time')
def time_decoder(v):
    if v.get('iso_string'):
        return isodate.parse_time(v['iso_string'])
    return datetime.time(
        v['hour'], v['minute'], v['second'], v['microsecond']
    )


@register_decoder('timedelta')
def timedelta_decoder(v):
    if v.get('iso_string'):
        return isodate.parse_duration(v['iso_string'])
    return datetime.timedelta(seconds=v['seconds'])


@register_decoder('bytes')
def _bytes_decoder(v):
    cast = bytearray if bytes == str else bytes
    return cast(base64.decodestring(v['base64'].encode('utf-8')))


@register_decoder('Decimal')
def decimal_decoder(v):
    return Decimal(v['decimal'])


dummy_record = namedtuple('Record', ['model_name', 'id', 'rec_name'])
JSONDecoder.register(
    'Model', lambda dct: dummy_record(
        dct['model_name'], dct['id'], dct.get('rec_name')
    )
)


def parse_async_result(dct):
    from .client import AsyncResult
    return AsyncResult(dct['task_id'], dct['token'], None)


JSONDecoder.register(
    'AsyncResult', parse_async_result
)


class JSONEncoder(json.JSONEncoder):

    serializers = {}

    def __init__(self, *args, **kwargs):
        super(JSONEncoder, self).__init__(*args, **kwargs)
        # Force to use our custom decimal with simplejson
        self.use_decimal = False

    @classmethod
    def register(cls, klass, encoder):
        assert klass not in cls.serializers
        cls.serializers[klass] = encoder

    def default(self, obj):
        marshaller = self.serializers.get(
            type(obj),
            super(JSONEncoder, self).default
        )
        return marshaller(obj)


JSONEncoder.register(
    datetime.datetime,
    lambda o: {
        '__class__': 'datetime',
        'iso_string': o.isoformat(),
    }
)
JSONEncoder.register(
    datetime.date,
    lambda o: {
        '__class__': 'date',
        'iso_string': o.isoformat(),
    }
)
JSONEncoder.register(
    datetime.time,
    lambda o: {
        '__class__': 'time',
        'iso_string': o.isoformat(),
    }
)
JSONEncoder.register(
    datetime.timedelta,
    lambda o: {
        '__class__': 'timedelta',
        'iso_string': isodate.duration_isoformat(o),
    }
)
_bytes_encoder = lambda o: {  # noqa
    '__class__': 'bytes',
    'base64': base64.encodestring(o).decode('utf-8'),
}
JSONEncoder.register(bytes, _bytes_encoder)
JSONEncoder.register(bytearray, _bytes_encoder)
JSONEncoder.register(
    Decimal,
    lambda o: {
        '__class__': 'Decimal',
        'decimal': str(o),
    }
)


dumps = partial(json.dumps, cls=JSONEncoder)
loads = partial(json.loads, object_hook=JSONDecoder())
