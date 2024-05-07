# -*- coding: UTF-8 -*-
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import json
from fulfil_client.serialization import (
    dumps,
    loads,
)

import pytest

# name, python object, v2 serialization, v3 serialization
SPECIFICATION = {
    "datetime": {
        "python_object": datetime(2020, 1, 1, 10, 20, 30, 10),
        "v1": {
            "__class__": "datetime",
            "year": 2020,
            "month": 1,
            "day": 1,
            "hour": 10,
            "minute": 20,
            "second": 30,
            "microsecond": 10,
        },
        "v2": {
            "__class__": "datetime",
            "year": 2020,
            "month": 1,
            "day": 1,
            "hour": 10,
            "minute": 20,
            "second": 30,
            "microsecond": 10,
            "iso_string": "2020-01-01T10:20:30.000010",
        },
        "v3": {
            "__class__": "datetime",
            "iso_string": "2020-01-01T10:20:30.000010",
        },
    },
    "date": {
        "python_object": date(2020, 1, 1),
        "v1": {
            "__class__": "date",
            "year": 2020,
            "month": 1,
            "day": 1,
        },
        "v2": {
            "__class__": "date",
            "year": 2020,
            "month": 1,
            "day": 1,
            "iso_string": "2020-01-01",
        },
        "v3": {
            "__class__": "date",
            "iso_string": "2020-01-01",
        },
    },
    "time": {
        "python_object": time(10, 20, 30, 15),
        "v1": {
            "__class__": "time",
            "hour": 10,
            "minute": 20,
            "second": 30,
            "microsecond": 15,
        },
        "v2": {
            "__class__": "time",
            "hour": 10,
            "minute": 20,
            "second": 30,
            "microsecond": 15,
            "iso_string": "10:20:30.000015",
        },
        "v3": {
            "__class__": "time",
            "iso_string": "10:20:30.000015",
        },
    },
    "timedelta": {
        "python_object": timedelta(hours=25),
        "v1": {
            "__class__": "timedelta",
            "seconds": 90000,
        },
        "v2": {
            "__class__": "timedelta",
            "seconds": 90000,
            "iso_string": "P1DT1H",
        },
        "v3": {
            "__class__": "timedelta",
            "iso_string": "P1DT1H",
        },
    },
    "decimal": {
        "python_object": Decimal("101.123456789"),
        "v1": {
            "__class__": "Decimal",
            "decimal": "101.123456789",
        },
        "v2": {
            "__class__": "Decimal",
            "decimal": "101.123456789",
        },
        "v3": {
            "__class__": "Decimal",
            "decimal": "101.123456789",
        },
    },
}


PARAMS = []
V3_PARAMS = []
for klass, spec in SPECIFICATION.items():
    PARAMS.extend(
        [
            pytest.param(spec["python_object"], spec["v1"], id="{}.v1".format(klass)),
            pytest.param(spec["python_object"], spec["v2"], id="{}.v2".format(klass)),
            pytest.param(spec["python_object"], spec["v3"], id="{}.v3".format(klass)),
        ]
    )
    V3_PARAMS.append(
        pytest.param(spec["python_object"], spec["v3"], id="{}.v3".format(klass)),
    )


@pytest.mark.parametrize("python_object,serialized_object", V3_PARAMS)
def test_serialization_v3(python_object, serialized_object):
    """
    Test the serialization v3 works
    """
    # Create a dict from the serialized representation of the fulfil object
    deserialized_hash = json.loads(dumps(python_object))
    for key, value in serialized_object.items():
        assert key in deserialized_hash
        assert deserialized_hash[key] == value


@pytest.mark.parametrize("python_object,serialized_object", PARAMS)
def test_deserialization(python_object, serialized_object):
    """
    Deserializing the object should return the python object
    """
    assert python_object == loads(json.dumps(serialized_object))
