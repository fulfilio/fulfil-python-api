#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests',
    'money',
    'babel',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='fulfil_client',
    version='0.6.5',
    description="Fulfil REST API Client in Python",
    long_description=readme + '\n\n' + history,
    author="Fulfil.IO Inc.",
    author_email='hello@fulfil.io',
    url='https://github.com/fulfilio/fulfil-python-api',
    packages=[
        'fulfil_client',
    ],
    package_dir={
        'fulfil_client': 'fulfil_client'
    },
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='fulfil_client',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
