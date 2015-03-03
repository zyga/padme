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
"""
:mod:`padme.tests` -- tests for padme.

======================================

This package contains unit tests for padme. You don't want to use it directly
and it can get changed at any time without notice.
"""
from __future__ import print_function, absolute_import, unicode_literals

import doctest
import operator
import sys

if sys.version_info[0:2] >= (3, 4):
    import unittest
    from unittest import mock
else:
    import unittest2 as unittest
    import mock


# https://code.google.com/p/mock/issues/detail?id=247
# or http://bugs.python.org/issue23569
if sys.version_info[0] == 3 and '__div__' in mock._all_magics:
    mock._magics.remove('__div__')
    mock._magics.remove('__rdiv__')
    mock._magics.remove('__idiv__')
    mock._all_magics.remove('__div__')
    mock._all_magics.remove('__rdiv__')
    mock._all_magics.remove('__idiv__')
if sys.version_info[0] == 3 and '__truediv__' not in mock._all_magics:
    mock._magics.add('__truediv__')
    mock._magics.add('__rtruediv__')
    mock._magics.add('__itruediv__')
    mock._all_magics.add('__truediv__')
    mock._all_magics.add('__rtruediv__')
    mock._all_magics.add('__itruediv__')

# http://bugs.python.org/issue23568
if 'divmod' not in mock.numerics:
    mock._magics.add('__rdivmod__')
    mock._all_magics.add('__rdivmod__')
from padme import _logger
from padme import proxy
from padme import unproxied


# XXX: Set to True for revelation
reality_is_broken = False


def load_tests(loader, tests, ignore):
    """ Load doctests for padme (part of unittest test discovery protocol). """
    import padme
    tests.addTests(
        doctest.DocTestSuite(padme, optionflags=doctest.REPORT_NDIFF))
    return tests


def setUpModule():
    """ Module-level setup function (part of unittest protocol). """
    if reality_is_broken:
        import logging
        logging.basicConfig(level=logging.DEBUG)


class proxy_as_function(unittest.TestCase):

    """ Tests for uses of proxy() as factory for proxy objects.  """

    def setUp(self):
        """ Per-test-case setup function. """
        if reality_is_broken:
            print()
            _logger.debug("STARTING")
            _logger.debug("[%s]", self._testMethodName)
        self.obj = mock.MagicMock(name='obj')
        self.proxy = proxy(self.obj)

    def tearDown(self):
        """ Per-test-case teardown function. """
        if reality_is_broken:
            _logger.debug("DONE")

    # NOTE: order of test methods matches implementation

    def test_repr(self):
        """ Verify that repr/__repr__ is redirected to the proxiee. """
        self.assertEqual(repr(self.proxy), repr(self.obj))
        self.assertEqual(self.proxy.__repr__(), repr(self.obj))

    def test_str(self):
        """ Verify that str/__str__ is redirected to the proxiee. """
        self.assertEqual(str(self.proxy), str(self.obj))
        self.assertEqual(self.proxy.__str__(), str(self.obj))

    @unittest.skipUnless(sys.version_info[0] == 3, "requires python 3")
    def test_bytes(self):
        """ Verify that bytes/__bytes__ is redirected to the proxiee. """
        # NOTE: bytes() is unlike str() or repr() in that it is not a function
        # that converts an arbitrary object into a bytes object.  We cannot
        # just call it on a random object. What we must do is implement
        # __bytes__() on a new class and use instances of that class.
        class C(object):
            def __bytes__(self):
                return b'good'
        self.obj = C()
        self.proxy = proxy(self.obj)
        self.assertEqual(bytes(self.proxy), bytes(self.obj))
        self.assertEqual(self.proxy.__bytes__(), bytes(self.obj))

    def test_format(self):
        """ Verify that format/__format__ is redirected to the proxiee. """
        self.assertEqual(format(self.proxy), format(self.obj))
        self.assertEqual(self.proxy.__format__(""), format(self.obj))

    def test_lt(self):
        """ Verify that < /__lt__ is redirected to the proxiee. """
        # NOTE: MagicMock is not ordered so let's just use an integer
        self.obj = 0
        self.proxy = proxy(self.obj)
        self.assertLess(self.proxy, 1)
        self.assertLess(self.obj, 1)

    def test_le(self):
        """ Verify that <=/ __le__ is redirected to the proxiee. """
        # NOTE: MagicMock is not ordered so let's just use an integer
        self.obj = 0
        self.proxy = proxy(self.obj)
        self.assertLessEqual(self.proxy, 0)
        self.assertLessEqual(self.proxy, 1)
        self.assertLessEqual(self.obj, 0)
        self.assertLessEqual(self.obj, 1)

    def test_eq(self):
        """ Verify that == /__eq__ is redirected to the proxiee. """
        self.assertEqual(self.proxy, self.obj)
        self.obj.__eq__.assert_called_once_with(self.obj)
        self.assertEqual(self.obj, self.obj)

    def test_ne(self):
        """ Verify that != /__ne__ is redirected to the proxiee. """
        other = object()
        self.assertNotEqual(self.proxy, other)
        self.obj.__ne__.assert_called_once_with(other)
        self.assertNotEqual(self.obj, object())

    def test_gt(self):
        """ Verify that > /__gt__ is redirected to the proxiee. """
        # NOTE: MagicMock is not ordered so let's just use an integer
        self.obj = 0
        self.proxy = proxy(self.obj)
        self.assertGreater(self.proxy, -1)
        self.assertGreater(self.obj, -1)

    def test_ge(self):
        """ Verify that >= /__ge__ is redirected to the proxiee. """
        # NOTE: MagicMock is not ordered so let's just use an integer
        self.obj = 0
        self.proxy = proxy(self.obj)
        self.assertGreaterEqual(self.proxy, 0)
        self.assertGreaterEqual(self.proxy, -1)
        self.assertGreaterEqual(self.obj, 0)
        self.assertGreaterEqual(self.obj, -1)

    @unittest.skipUnless(sys.version_info[0] == 2, "requires python 2")
    def test_cmp(self):
        """ Verify that cmp /__cmp__ is redirected to the proxiee. """
        class C(object):
            def __cmp__(self, other):
                return -1
        self.obj = C()
        self.proxy = proxy(self.obj)
        other = object()
        self.assertEqual(cmp(self.proxy, other), cmp(self.obj, other))
        self.assertEqual(self.proxy.__cmp__(other), cmp(self.obj, other))

    def test_hash(self):
        """ Verify that hash /__hash__ is redirected to the proxiee. """
        self.assertEqual(hash(self.proxy), hash(self.obj))
        self.assertEqual(self.proxy.__hash__(), hash(self.obj))

    @unittest.skipUnless(sys.version_info[0] == 3, "requires python 3")
    def test_bool(self):
        """ Verify that bool /__bool__ is redirected to the proxiee. """
        self.assertEqual(bool(self.proxy), bool(self.obj))
        self.assertEqual(self.proxy.__bool__(), bool(self.obj))

    @unittest.skipUnless(sys.version_info[0] == 2, "requires python 2")
    def test_nonzero(self):
        """ Verify that bool /__nonzero__ is redirected to the proxiee. """
        self.assertEqual(bool(self.proxy), bool(self.obj))
        self.assertEqual(self.proxy.__nonzero__(), bool(self.obj))

    @unittest.skipUnless(sys.version_info[0] == 2, "requires python 2")
    def test_unicode(self):
        """ Verify that unicode /__unicode__ is redirected to the proxiee. """
        self.assertEqual(unicode(self.proxy), unicode(self.obj))
        self.assertEqual(self.proxy.__unicode__(), unicode(self.obj))

    def test_attr_get(self):
        """ Verify that attribute reads are redirected to the proxiee. """
        self.assertIs(self.proxy.attr, self.obj.attr)

    def test_attr_set(self):
        """ Verify that attribute writes are redirected to the proxiee. """
        value = mock.Mock(name='value')
        self.proxy.attr = value
        self.assertIs(self.obj.attr, value)

    def test_attr_del(self):
        """ Verify that attribute deletes are redirected to the proxiee. """
        del self.proxy.attr
        with self.assertRaises(AttributeError):
            self.obj.attr

    def test_dir(self):
        """ Verify that dir / __dir__ is redirected to the proxiee. """
        self.assertEqual(dir(self.proxy), dir(self.obj))
        self.assertEqual(self.proxy.__dir__(), dir(self.obj))

    def test_descriptor_methods(self):
        """ Verify that __{get,set,delete}__ are redirected to the proxiee. """
        property_proxy = proxy(property)

        class C(object):
            _ok = "default"

            @property_proxy
            def ok(self):
                return self._ok

            @ok.setter
            def ok(self, value):
                self._ok = value

            @ok.deleter
            def ok(self):
                del self._ok
        obj = C()
        self.assertEqual(obj._ok, "default")
        # __set__ assigns the new value
        obj.ok = True
        self.assertTrue(obj._ok)
        # __get__ returns the current value
        self.assertTrue(obj.ok)
        # __delete__ removes the current value
        del obj.ok
        self.assertEqual(obj._ok, "default")

    def test_call(self):
        """ Verify that __call__ is redirected to the proxiee. """
        self.assertEqual(self.proxy(), self.obj())
        self.assertEqual(self.proxy.__call__(), self.obj())

    def test_len(self):
        """ Verify that len / __len__ is redirected to the proxiee. """
        self.assertEqual(len(self.proxy), len(self.obj))
        self.assertEqual(self.proxy.__len__(), len(self.obj))

    @unittest.skipUnless(sys.version_info[0:2] >= (3, 4),
                         "requires python 3.4")
    def test_length_hint(self):
        """ Verify that __length_hint__ is redirected to the proxiee. """
        # NOTE: apparently MagicMock doesn't support this method
        class C(object):
            def __length_hint__(self):
                return 42
        self.obj = C()
        self.proxy = proxy(self.obj)
        self.assertEqual(
            operator.length_hint(self.proxy), operator.length_hint(self.obj))
        self.assertEqual(
            self.proxy.__length_hint__(), operator.length_hint(self.obj))

    def test_getitem(self):
        """ Verify that [] / __getitem__ is redirected to the proxiee. """
        self.assertEqual(self.proxy['item'], self.obj['item'])
        self.assertEqual(self.proxy.__getitem__('item'), self.obj['item'])

    def test_setitem_v1(self):
        """ Verify that []= is redirected to the proxiee. """
        # NOTE: MagicMock doesn't store item assignment
        self.obj = ["old"]
        self.proxy = proxy(self.obj)
        self.proxy[0] = "new"
        self.assertEqual(self.obj[0], "new")

    def test_setitem_v2(self):
        """ Verify that __setitem__ is redirected to the proxiee. """
        # NOTE: MagicMock doesn't store item assignment
        self.obj = ["old"]
        self.proxy = proxy(self.obj)
        self.proxy.__setitem__(0, "value")
        self.assertEqual(self.obj[0], "value")

    def test_delitem(self):
        """ Verify that del[] / __delitem__ is redirected to the proxiee. """
        obj = {'k': 'v'}
        del proxy(obj)['k']
        self.assertEqual(obj, {})
        obj = {'k': 'v'}
        proxy(obj).__delitem__('k')
        self.assertEqual(obj, {})

    def test_iter(self):
        """ Verify that iter / __iter__ is redirected to the proxiee. """
        # NOTE: MagicMock.__iter__ needs to return a deterministic iterator as
        # by default a new iterator is returned each time.
        self.obj.__iter__.return_value = iter([])
        self.assertEqual(iter(self.proxy), iter(self.obj))
        self.assertEqual(self.proxy.__iter__(), iter(self.obj))

    def test_reversed(self):
        """ Verify that __reversed__ is redirected to the proxiee. """
        # NOTE: apparently MagicMock.doesn't support __reversed__ so we fall
        # back to the approach with a custom class. The same comment, as above,
        # for __iter__() applies though.
        with self.assertRaises(AttributeError):
            self.obj.__reversed__.return_value = reversed([])

        class C(object):
            reversed_retval = iter([])

            def __reversed__(self):
                return self.reversed_retval
        self.obj = C()
        self.proxy = proxy(self.obj)
        self.assertEqual(reversed(self.proxy), reversed(self.obj))
        self.assertEqual(self.proxy.__reversed__(), reversed(self.obj))

    def test_contains(self):
        """ Verify that __contains__ is redirected to the proxiee. """
        item = object()
        self.assertEqual(item in self.proxy, item in self.obj)
        self.assertEqual(self.proxy.__contains__(item), item in self.obj)
        self.assertEqual(self.proxy.__contains__(item), False)
        self.obj.__contains__.return_value = True
        self.assertEqual(item in self.proxy, item in self.obj)
        self.assertEqual(self.proxy.__contains__(item), item in self.obj)
        self.assertEqual(self.proxy.__contains__(item), True)

    # TODO, tests and implementation for all the numeric methods

    def test_context_manager_methods_v1(self):
        """ Verify that __enter__ and __exit__ are redirected. """
        with self.proxy:
            pass
        self.obj.__enter__.assert_called_once_with()
        self.obj.__exit__.assert_called_once_with(None, None, None)

    def test_context_manager_methods_v2(self):
        """ Verify that redirecting __exit__ passes right arguments. """
        exc = Exception("boom")
        with self.assertRaisesRegex(Exception, "boom"):
            with self.proxy:
                try:
                    raise exc
                except:
                    traceback = sys.exc_info()[2]
                    raise
        self.obj.__enter__.assert_called_once_with()
        # XXX: it's called with (Exception, exc, traceback) but I don't know
        # how to reach the traceback here
        self.obj.__exit__.assert_called_once_with(Exception, exc, traceback)

    def test_hasattr_parity(self):
        """ verify that hasattr() behaves the same for original and proxy. """
        class C(object):
            pass
        special_methods = '''
            __del__
            __repr__
            __str__
            __bytes__
            __format__
            __lt__
            __le__
            __eq__
            __ne__
            __gt__
            __ge__
            __cmp__
            __hash__
            __bool__
            __nonzero__
            __unicode__
            __getattr__
            __getattribute__
            __setattr__
            __delattr__
            __dir__
            __get__
            __set__
            __delete__
            __call__
            __len__
            __length_hint__
            __getitem__
            __setitem__
            __delitem__
            __iter__
            __reversed__
            __contains__
            __enter__
            __exit__
        '''.split()
        for obj in [C(), 42, property(lambda x: x), int, None]:
            self.obj = obj
            self.proxy = proxy(self.obj)
            for attr in special_methods:
                self.assertEqual(
                    hasattr(self.obj, attr),
                    hasattr(self.proxy, attr),
                    "attribute presence mismatch on attr %r and object %r" % (
                        attr, self.obj))

    def test_isinstance(self):
        """ Verify that isinstance() checks work. """
        # NOTE: this method tests the metaclass
        self.assertIsInstance(self.obj, type(self.obj))
        self.assertIsInstance(self.proxy, type(self.obj))

    def test_issubclass(self):
        """ Verify that issubclass() checks work. """
        # NOTE: this method tests the metaclass
        # NOTE: mock doesn't support subclasscheck
        # NOTE: str ... below is just for python 2.7
        # (__future__.unicode_literals is in effect)
        obj = str("something other than mock")
        self.assertTrue(issubclass(str, type(obj)))
        self.assertTrue(issubclass(str, type(proxy(obj))))

    def test_class(self):
        """ Verify that proxy_obj.__class__ is redirected to the proxiee. """
        self.assertEqual(self.proxy.__class__, self.obj.__class__)
        # NOTE: The proxy cannot hide the fact, that it is a proxy
        self.assertNotEqual(type(self.proxy), type(self.obj))


class proxy_as_class(unittest.TestCase):

    """ Tests for uses of proxy() as a base class for specialized proxies. """

    def setUp(self):
        """ Per-test-case setup function. """
        if reality_is_broken:
            print()
            _logger.debug("STARTING")
            _logger.debug("[%s]", self._testMethodName)

    def tearDown(self):
        """ Per-test-case teardown function. """
        if reality_is_broken:
            _logger.debug("DONE")

    def test_proxy_subclass(self):
        """ Verify that basic @unproxied use case works. """
        # NOTE: bring your comb, because this is the extra-hairy land
        class censored(proxy):

            @unproxied
            def __str__(self):
                return "*" * len(super(censored, self).__str__())
        self.assertTrue(issubclass(censored, proxy))
        self.assertEqual(str(censored("freedom")), "*******")
        self.assertEqual(censored("freedom").__str__(), "*******")
