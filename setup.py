#!/usr/bin/env python
# Copyright 2015 Canonical Ltd.
# Written by:
#   Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
#
# This file is part of Padme.
#
# Padme is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3,
# as published by the Free Software Foundation.
#
# Padme is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Padme.  If not, see <http://www.gnu.org/licenses/>.

import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')


setup(
    name='padme',
    version='1.1.1',
    description='Padme is a mostly transparent proxy class for Python',
    long_description=readme + '\n\n' + history,
    author='Zygmunt Krynicki',
    author_email='me@zygoon.pl',
    url='https://github.com/zyga/padme',
    packages=['padme'],
    package_dir={'padme': 'padme'},
    include_package_data=True,
    license="LGPLv3",
    zip_safe=True,
    keywords='padme proxy',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        ('License :: OSI Approved :: GNU Lesser General Public License v3'
         ' (LGPLv3)'),
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    tests_require=([
        'unittest2' if sys.version_info[0] == 2 else 'unittest2py3k',
        'mock'] if sys.version_info[:2] <= (3, 3) else None),
    test_suite='padme.tests',
)
