# -*- coding: utf-8 -*-
"""
Serialization extension for Kombu, the underlying library
used by Celery for asynchronous tasks.

https://docs.celeryproject.org
/projects/kombu/en/stable/userguide/serialization.html

This is used in setuptools to register custom endpoint
"""
from fulfil_client.client import dumps, loads


register_args = (
    dumps, loads,
    'application/vnd.fulfil.v2+json', 'utf-8'
)
