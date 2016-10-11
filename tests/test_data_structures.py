# -*- coding: utf-8 -*-
# pylint: disable=D102
"""
Test fulfilio data structures

pylint option block-disable
"""
import pytest
import random
from decimal import Decimal
from babel.numbers import format_currency

from money import Money
from fulfil_client.model import (
    ModificationTrackingDict, Query, StringType, MoneyType
)


@pytest.fixture
def mtd():
    """
    Return a sample Modification Tracking Dictionary
    """
    return ModificationTrackingDict({
        'a': 'apple',
        'b': 'box',
        'l': [1, 2, 3],
    })


class TestModificationTrackingDict(object):

    def test_no_changes_on_initial_dict(self, mtd):
        assert len(mtd.changes) == 0

    def test_no_changes_on_same_value(self, mtd):
        mtd['a'] = 'apple'  # nothing changes
        assert len(mtd.changes) == 0

    def test_no_changes_on_same_value_on_update(self, mtd):
        mtd.update({'a': 'apple'})
        assert len(mtd.changes) == 0

    def test_changes_on_setter(self, mtd):
        mtd['b'] = 'ball'   # big change
        assert len(mtd.changes) == 1
        assert 'b' in mtd.changes

    def test_changes_on_update(self, mtd):
        mtd.update({'b': 'ball'})   # big change
        assert len(mtd.changes) == 1
        assert 'b' in mtd.changes

    def test_changes_on_new_key(self, mtd):
        mtd['c'] = 'cat'
        assert len(mtd.changes) == 1
        assert 'c' in mtd.changes


@pytest.fixture
def query(client):
    return Query(
        client.model('res.user'),
    )


class TestQuery(object):

    def test_copyability_of_query(self, query):
        query._copy()

    def test_query_first(self, query):
        assert query.first()

    def test_query_count(self, query):
        assert query.count()

    def test_query_all(self, query):
        assert query.all()


@pytest.fixture
def res_user_model(Model):
    class ResUserModel(Model):
        __model_name__ = 'res.user'
        name = StringType()
    return ResUserModel


@pytest.fixture
def sale_order_model(Model):
    class SaleOrderModel(Model):
        __model_name__ = 'sale.sale'
        _eager_fields = set(['currency.code'])

        number = StringType()
        total_amount = MoneyType('currency_code')

        @property
        def currency_code(self):
            return self._values['currency.code']

    return SaleOrderModel


@pytest.fixture
def product_model(Model):
    class ProductModel(Model):
        __model_name__ = 'product.product'

        list_price = MoneyType('currency_code')

        @property
        def currency_code(self):
            return 'USD'

    return ProductModel


@pytest.fixture
def contact_model(Model):
    class ContactModel(Model):
        __model_name__ = 'party.party'

        name = StringType()
        credit_limit_amount = MoneyType('currency_code')

        @property
        def currency_code(self):
            return 'USD'
    return ContactModel


@pytest.fixture
def module_model(Model):
    class ModuleModel(Model):
        __model_name__ = 'ir.module'
        name = StringType()
    return ModuleModel


class TestModel(object):

    def test_model_change_tracking(self, res_user_model):
        user = res_user_model.query.first()
        user.name = user.name
        assert not bool(user.changes)

        user.name = "Not real name"
        assert 'name' in user.changes

    def test_equality_of_saved_records(self, res_user_model):
        user = res_user_model.query.first()
        user_again = res_user_model.query.get(user.id)
        assert user == user_again

    def test_inequality_of_saved_records(self, res_user_model, module_model):
        assert res_user_model.query.first() != module_model.query.first()

    def test_inequality_of_changed_models(self, res_user_model):
        user = res_user_model.query.first()
        user_again = res_user_model.query.get(user.id)
        user.display_name = "something else"
        assert user == user_again


class TestMoneyType(object):

    def test_display_format(self, sale_order_model):
        order = sale_order_model.query.first()
        assert isinstance(order.total_amount, Money)
        assert isinstance(order.total_amount.amount, Decimal)
        assert order.total_amount.format('en_US') == format_currency(
            order._values['total_amount'],
            currency=order._values['currency.code'],
            locale='en_US'
        )
        assert order.total_amount.format('fr_FR') == format_currency(
            order._values['total_amount'],
            currency=order._values['currency.code'],
            locale='fr_FR'
        )

    def test_setting_values(self, product_model):
        product = product_model.query.first()

        new_price = Decimal(random.choice(xrange(1, 1000)))
        product.list_price = new_price
        product.save()

        list_price = product_model.query.first().list_price
        assert list_price.amount == new_price
        assert list_price.currency == 'USD' # hard coded in model property

    def test_none(self, contact_model):

        contact = contact_model.query.first()

        contact.credit_limit_amount = None
        contact.save()

        credit_limit = contact.query.first().credit_limit_amount
        assert credit_limit == None

        contact.credit_limit_amount = Decimal('100000')
        contact.save()

        credit_limit = contact.query.first().credit_limit_amount
        assert credit_limit.amount == Decimal('100000')
        assert credit_limit.currency == 'USD' # hard coded in model property
