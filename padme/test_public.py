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
from __future__ import print_function, absolute_import, unicode_literals

import sys

if sys.version_info[0:2] >= (3, 4):
    import unittest
else:
    import unittest2 as unittest

from padme.public import get_api
from padme.public import get_private_api


class Person(object):

    """A simple person class."""

    __attributes__ = ('name', 'age')

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Person {!r}>".format(self.name)


class IPerson(object):

    """Public api of a person."""

    @property
    def name(self):
        """Full name of the person."""


class FunctionTests(unittest.TestCase):

    def test_get_api(self):
        self.assertIn('name', get_api(Person))
        self.assertIn('age', get_api(Person))
        self.assertIn('name', get_api(IPerson))
        self.assertNotIn('age', get_api(IPerson))
        self.assertIn('__attributes__', get_api(Person))

    def test_get_private_api(self):
        self.assertEqual(
            get_private_api(Person, IPerson),
            {'age', '__attributes__'})


if __name__ == "__main__":
    unittest.main()
