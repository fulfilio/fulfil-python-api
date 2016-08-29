# -*- coding: utf-8 -*-
# pylint: disable=D102
"""
Test fulfilio data structures

pylint option block-disable
"""
import pytest

from fulfil_client.model import ModificationTrackingDict, Query, StringType


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
        dict
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
def module_model(Model):
    class ModuleModel(Model):
        __model_name__ = 'ir.module.module'
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
