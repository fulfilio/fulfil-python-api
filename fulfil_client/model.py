# -*- coding: utf-8 -*-
"""
Fulfil.IO Model Helper

A collection of model layer APIs to write lesser code
and better
"""
import six
import logging
import functools
import warnings
from datetime import datetime, date
from copy import copy
from decimal import Decimal
from money import Money

import fulfil_client
from fulfil_client.client import loads, dumps

if six.PY2:
    from future_builtins import zip


cache_logger = logging.getLogger('fulfil_client.cache')


class BaseType(object):
    """
    A django field like object that implements a descriptor.
    """

    # Eager load this field
    eager = True

    def __init__(self, cast, required=False, default=None):
        # this will be auto discovered by a meta class
        self.name = None

        self.cast = cast
        self.default = default
        self.required = required

    def __get__(self, instance, owner):
        if instance:
            return instance._values.get(self.name, self.default)
        else:
            return self

    def convert(self, value):
        if value is None:
            return
        if isinstance(value, self.cast):
            return value
        return self.cast(value)

    def __set__(self, instance, value):
        instance._values[self.name] = self.convert(value)

    def __delete__(self, instance):
        del instance._values[self.name]


class IntType(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', int)
        super(IntType, self).__init__(*args, **kwargs)


class BooleanType(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', bool)
        super(BooleanType, self).__init__(*args, **kwargs)


class StringType(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', six.text_type)
        super(StringType, self).__init__(*args, **kwargs)


class DecimalType(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', Decimal)
        super(DecimalType, self).__init__(*args, **kwargs)


class FloatType(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', float)
        super(FloatType, self).__init__(*args, **kwargs)


class DateTime(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', datetime)
        super(DateTime, self).__init__(*args, **kwargs)


class Date(BaseType):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cast', date)
        super(Date, self).__init__(*args, **kwargs)


class One2ManyType(BaseType):

    def __init__(self, model_name, cache=False, *args, **kwargs):
        self.model_name = model_name
        self.cache = cache
        kwargs.setdefault('cast', list)
        super(One2ManyType, self).__init__(*args, **kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if instance._values.get(self.name):
            model = instance.__modelregistry__[self.model_name]
            if self.cache:
                return model.from_cache(instance._values.get(self.name))
            return model.from_ids(instance._values.get(self.name))
        return instance._values.get(self.name)


class MoneyType(DecimalType):
    """
    Built on top of the decimal field, but also understands the
    currency with which the amount is defined.

    Usage examples:

        sale.total_amount.amount

    Formatting for web

        sale.total_amount.format()

    :param currency_field: Name of the field that will have the 3 char
                           currency code
    """

    def __init__(self, currency_field, *args, **kwargs):
        self.currency_field = currency_field
        super(MoneyType, self).__init__(*args, **kwargs)

    def __get__(self, instance, owner):
        if instance:
            if instance._values.get(self.name, self.default) is None:
                return None
            return Money(
                instance._values.get(self.name, self.default),
                getattr(instance, self.currency_field)
            )
        else:
            return self


class ModelType(IntType):
    """
    Builds a field that represents a Foreign Key relationship to another
    model.

    :param model_name: Name of the model to which this model has a FK
    :param cache: If set, it looks up the record in the cache backend of the
                  underlying model before querying the server to fetch records.
    """
    def __init__(self, model_name, cache=False, *args, **kwargs):
        self.model_name = model_name
        self.cache = cache
        super(ModelType, self).__init__(*args, **kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if instance._values.get(self.name):
            model = instance.__modelregistry__[self.model_name]
            if self.cache:
                return model.from_cache(instance._values.get(self.name))
            return model.get_by_id(instance._values.get(self.name))
        return instance._values.get(self.name)


class NamedDescriptorResolverMetaClass(type):
    """
    A metaclass that discovers field names
    """

    def __new__(cls, classname, bases, class_dict):
        abstract = class_dict.get('__abstract__', False)
        model_name = class_dict.get('__model_name__')

        if not abstract and not model_name:
            for base in bases:
                if hasattr(base, '__model_name__'):
                    model_name = base.__model_name__
                    break
            else:
                raise Exception('__model_name__ not defined for model')

        fields = set([])
        eager_fields = set([])
        for base in bases:
            if hasattr(base, '_fields'):
                fields |= set(base._fields)
            if hasattr(base, '_eager_fields'):
                eager_fields |= set(base._eager_fields)

        fields |= class_dict.get('_fields', set([]))
        eager_fields |= class_dict.get('_eager_fields', set([]))

        # Iterate through the new class' __dict__ to:
        #
        # * update all recognised NamedDescriptor member names
        # * find lazy loaded fields
        # * find eager_loaded fields
        for name, attr in class_dict.items():
            if isinstance(attr, BaseType):
                attr.name = name
                fields.add(name)
                if attr.eager:
                    eager_fields.add(name)

        class_dict['_eager_fields'] = eager_fields
        class_dict['_fields'] = fields | eager_fields

        # Call super and continue class creation
        rv = type.__new__(cls, classname, bases, class_dict)
        if not abstract:
            rv.__modelregistry__[model_name] = rv
        return rv


class ModificationTrackingDict(dict):
    """
    A change tracking dictionary
    """

    def __init__(self, *args, **kwargs):
        self.changes = set([])
        super(ModificationTrackingDict, self).__init__(*args, **kwargs)

    def __setitem__(self, key, val):
        if key not in self or self[key] != val:
            self.changes.add(key)
        dict.__setitem__(self, key, val)

    def update(self, *args, **kwargs):
        """
        Update does not call __setitem__ by default
        """
        for k, v in dict(*args, **kwargs).items():
            self[k] = v


def return_instances(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        query = args[0]
        map_fn = query.instance_class
        for record in function(*args, **kwargs):
            yield map_fn(record) if map_fn else record
    return wrapper


def return_instance(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        query = args[0]
        result = function(*args, **kwargs)
        if result is None:
            return None
        if query.instance_class:
            return query.instance_class(**result)
        else:
            return result
    return wrapper


class classproperty(object):    # NOQA
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class Query(object):
    """
    A sqlalchemy like query object giving developers familiar primitives.

    The method are limited to what are reasonable over an API.
    """

    def __init__(self, model, instance_class=None):
        self.rpc_model = model
        self.instance_class = instance_class or None
        self.domain = []
        self._limit = None
        self._offset = None
        self._order_by = None
        self.active_only = True

    @property
    def fields(self):
        return self.instance_class and tuple(self.instance_class._fields) or \
                None

    def __copy__(self):
        """
        Change the copy behavior of query.

        Maintain references to model and instance class while building a new
        list for domain and order by
        """
        newone = type(self)(self.rpc_model, self.instance_class)

        # immutable types
        newone._limit = self._limit
        newone._offset = self._offset
        newone.active_only = self.active_only

        # Duplicate the lists
        if self._order_by:
            newone._order_by = self._order_by[:]
        newone.domain = self.domain[:]
        return newone

    @property
    def context(self):
        "Return the context to execute the query"
        return {
            'active_test': self.active_only,
        }

    def _copy(self):
        "Internal method to make copies of the query"
        return copy(self)

    @return_instances
    def all(self):
        """
        Return the results represented by this Query as a list.

        .. versionchanged:: 0.10.0

            Returns an iterator that lazily loads
            records instead of fetching thousands
            of records at once.
        """
        return self.rpc_model.search_read_all(
            self.domain,
            self._order_by,
            self.fields,
            context=self.context,
            offset=self._offset or 0,
            limit=self._limit,
        )

    def count(self):
        "Return a count of rows this Query would return."
        return self.rpc_model.search_count(
            self.domain, context=self.context
        )

    def exists(self):
        """
        A convenience method that returns True if a record
        satisfying the query exists
        """
        return self.rpc_model.search_count(
            self.domain, context=self.context
        ) > 0

    def show_active_only(self, state):
        """
        Set active only to true or false on a copy of this query
        """
        query = self._copy()
        query.active_only = state
        return query

    def filter_by(self, **kwargs):
        """
        Apply the given filtering criterion to a copy of this Query, using
        keyword expressions.
        """
        query = self._copy()
        for field, value in kwargs.items():
            query.domain.append(
                (field, '=', value)
            )
        return query

    def filter_by_domain(self, domain):
        """
        Apply the given domain to a copy of this query
        """
        query = self._copy()
        query.domain = domain
        return query

    @return_instance
    def first(self):
        """
        Return the first result of this Query or None if the result
        doesn't contain any row.
        """
        results = self.rpc_model.search_read(
            self.domain, None, 1, self._order_by, self.fields,
            context=self.context
        )
        return results and results[0] or None

    @return_instance
    def get(self, id):
        """
        Return an instance based on the given primary key identifier,
        or None if not found.

        This returns a record whether active or not.
        """
        ctx = self.context.copy()
        ctx['active_test'] = False
        results = self.rpc_model.search_read(
            [('id', '=', id)],
            None, None, None, self.fields,
            context=ctx
        )
        return results and results[0] or None

    def limit(self, limit):
        """
        Apply a LIMIT to the query and return the newly resulting Query.
        """
        query = self._copy()
        query._limit = limit
        return query

    def offset(self, offset):
        """
        Apply an OFFSET to the query and return the newly resulting Query.
        """
        query = self._copy()
        query._offset = offset
        return query

    @return_instance
    def one(self):
        """
        Return exactly one result or raise an exception.

        Raises fulfil_client.exc.NoResultFound if the query selects no rows.
        Raises fulfil_client.exc.MultipleResultsFound if multiple rows are
        found.
        """
        results = self.rpc_model.search_read(
            self.domain, 2, None, self._order_by, self.fields,
            context=self.context
        )
        if not results:
            raise fulfil_client.exc.NoResultFound
        if len(results) > 1:
            raise fulfil_client.exc.MultipleResultsFound
        return results[0]

    def order_by(self, *criterion):
        """
        apply one or more ORDER BY criterion to the query and
        return the newly resulting Query

        All existing ORDER BY settings can be suppressed by passing None -
        this will suppress any ORDER BY configured on mappers as well.
        """
        query = self._copy()
        query._order_by = criterion
        return query

    def delete(self):
        """
        Delete all records matching the query.

        Warning: This is a desctructive operation.

        Not every model allows deletion of records and several models
        even restrict based on status. For example, deleting products
        that have been transacted is restricted. Another example is sales
        orders which can be deleted only when they are draft.

        If deletion fails, a server error is thrown.
        """
        ids = self.rpc_model.search(self.domain, context=self.context)
        if ids:
            self.rpc_model.delete(ids)

    def archive(self):
        """
        Archives (soft delete) all the records matching the query.

        This assumes that the model allows archiving (not many do - especially
        transactional documents).

        Internal implementation sets the active field to False.
        """
        ids = self.rpc_model.search(self.domain, context=self.context)
        if ids:
            self.rpc_model.write(ids, {'active': False})


@six.add_metaclass(NamedDescriptorResolverMetaClass)
class Model(object):
    """
    Active record design pattern for RPC models.
    """

    __abstract__ = True

    fulfil_client = None
    cache_backend = None
    cache_expire = None

    id = IntType()

    def __init__(self, values=None, id=None, **kwargs):
        values = values or {}
        values.update(kwargs)

        if id is not None:
            values['id'] = id

        # Now create a modification tracking dictionary
        self._values = ModificationTrackingDict(values)

    @classmethod
    def get_cache_key(cls, id):
        "Return a cache key for the given id"
        return '%s:%s:%s' % (
            cls.fulfil_client.subdomain,
            cls.__model_name__,
            id
        )

    @property
    def cache_key(self):
        return self.get_cache_key(self.id)

    @classmethod
    def from_cache_multi(cls, ids, ignore_misses=False):
        """
        Check if a record is in cache. If it is, load from there, if not
        load the record and then cache it, but in bulk.

        For performance, you can opt to ignore fetching records that are
        not already on the cache. While this can give you a performance
        boost, this may result in some or more records missing. Use with
        care, you've been warned!

        :param ignore_misses: If True, then the returned set will not
                              include records that are not already in
                              cache.
        """
        if not ids:
            return []
        results = []
        misses = []
        if not cls.cache_backend:
            misses = ids
        else:
            cached_values = cls.cache_backend.mget(map(cls.get_cache_key, ids))
            for id, cached_value in zip(ids, cached_values):
                if cached_value:
                    results.append(cls(id=id, values=loads(cached_value)))
                else:
                    misses.append(id)

        if misses:
            cache_logger.warn(
                "MISS::MULTI::%s::%s" % (cls.__model_name__, misses)
            )

        if misses and not ignore_misses:
            # Get the records in bulk for misses
            rows = cls.rpc.read(misses, tuple(cls._fields))
            for row in rows:
                record = cls(id=row['id'], values=row)
                record.store_in_cache()
                results.append(record)

        return sorted(results, key=lambda r: ids.index(r.id))

    @classmethod
    def from_cache(cls, id):
        """
        Check if a record is in cache. If it is load from there, if not
        load the record and then cache it.
        """
        if isinstance(id, (list, tuple)):
            message = "For list and ids use from_cache_multi"
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return cls.from_cache_multi(id)

        key = cls.get_cache_key(id)
        cached_value = cls.cache_backend and cls.cache_backend.get(key)

        if cached_value:
            cache_logger.debug("HIT::%s" % key)
            return cls(id=id, values=loads(cached_value))

        cache_logger.warn("MISS::%s" % key)
        record = cls(id=id)
        record.refresh()
        record.store_in_cache()
        return record

    def store_in_cache(self):
        """
        Save the values to a cache.
        """
        if self.cache_backend:
            self.cache_backend.set(
                self.cache_key, dumps(self._values), self.cache_expire
            )

    def invalidate_cache(self):
        if self.cache_backend:
            self.cache_backend.delete(self.cache_key)

    @classmethod
    def from_ids(cls, ids):
        """
        Create multiple active resources at once
        """
        return list(map(cls, cls.rpc.read(ids, tuple(cls._eager_fields))))

    @property
    def changes(self):
        """
        Return a set of changes
        """
        return dict([
            (field_name, self._values[field_name])
            for field_name in self._values.changes
        ])

    @classproperty
    def query(cls):     # NOQA
        return Query(cls.get_rpc_model(), cls)

    @property
    def has_changed(self):
        "Return True if the record has changed"
        return len(self._values) > 0

    @classproperty
    def rpc(cls):       # NOQA
        "Returns an RPC client for the Fulfil.IO model with same name"
        return cls.get_rpc_model()

    @classmethod
    def get_rpc_model(cls):
        "Returns an instance of the model record"
        return cls.fulfil_client.model(cls.__model_name__)

    @classmethod
    def get_rpc_record(cls, id):
        "Returns an instance for Fulfil.IO Client Record"
        return cls.fulfil_client.record(cls.__model_name__, id)

    @classmethod
    def get_by_id(cls, id):
        "Given an integer ID, fetch the record from fulfil.io"
        return cls(values=cls.rpc.read([id], tuple(cls._eager_fields))[0])

    def delete(self):
        """
        Delete the record
        """
        return self.rpc.delete([self.id])

    def refresh(self):
        """
        Refresh a record by fetching again from the API.
        This also resets the modifications in the record.
        """
        self.invalidate_cache()

        assert self.id, "Cannot refresh unsaved record"
        self._values = ModificationTrackingDict(
            self.rpc.read([self.id], tuple(self._fields))[0]
        )

    def save(self):
        "Save as a new record if there is no id, or update record with id"
        if self.id:
            if self.changes:
                self.rpc.write([self.id], self.changes)
        else:
            self.id = self.rpc.create([self._values])[0]

        # Either way refresh the record after saving
        self.refresh()

        return self

    def __eq__(self, other):
        if other is None:
            return False
        if other.__model_name__ != self.__model_name__:
            # has to be of the same model
            return False
        if self.id and (other.id != self.id):
            # If the record has an ID the other one should
            # have the same.
            return False
        if not self.id and (self._values != other._values):
            # Unsaved records are same only if _values
            # of both are the same.
            return False
        return True

    @property
    def __url__(self):
        "Return the API URL for the record"
        return '/'.join([
            self.rpc.client.base_url,
            self.__model_name__,
            six.text_type(self.id)
        ])

    @property
    def __client_url__(self):
        "Return the Client URL for the record"
        return '/'.join([
            self.rpc.client.host,
            'client/#/model',
            self.__model_name__,
            six.text_type(self.id)
        ])


def model_base(fulfil_client, cache_backend=None, cache_expire=10 * 60):
    """
    Return a Base Model class that binds to the fulfil client instance and
    the cache instance.

    This design is inspired by the declarative base pattern in SQL Alchemy.
    """
    return type(
        'BaseModel',
        (Model,),
        {
            'fulfil_client': fulfil_client,
            'cache_backend': cache_backend,
            'cache_expire': cache_expire,
            '__abstract__': True,
            '__modelregistry__': {},
        },
    )
