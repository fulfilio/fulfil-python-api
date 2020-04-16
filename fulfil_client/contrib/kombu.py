# -*- coding: utf-8 -*-
"""
Serialization extension for Kombu, the underlying library
used by Celery for asynchronous tasks.

https://docs.celeryproject.org
/projects/kombu/en/stable/userguide/serialization.html

This is used in setuptools to register custom endpoint
"""
from fulfil_client.serialization import dumps, loads, CONTENT_TYPE


register_args = (
    dumps, loads, CONTENT_TYPE, 'utf-8'
)
