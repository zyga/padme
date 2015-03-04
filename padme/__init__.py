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
:mod:`padme` -- a mostly transparent proxy class for Python.

============================================================

Padme, named after the Star Wars (tm) character, is a library for creating
proxy objects out of any other python object.

The resulting object is as close to mimicking the original as possible. Some
things are impossible to fake in CPython so those are highlighted below. All
other operations are silently forwarded to the original.

Terminology
-----------

.. glossary:

proxy:
    An intermediate object that is used in place of some original object.

proxiee:
    The original object hidden behind one or more proxies.

Basic features
--------------

Let's consider a simple example:

    >>> pets = [str('cat'), str('dog'), str('fish')]
    >>> pets_proxy = proxy(pets)
    >>> pets_proxy
    ['cat', 'dog', 'fish']
    >>> isinstance(pets_proxy, list)
    True
    >>> pets_proxy.append(str('rooster'))
    >>> pets
    ['cat', 'dog', 'fish', 'rooster']

By default, a proxy object is not that interesting. What is more interesting is
the ability to create subclasses that change a subset of the behavior. For
implementation simplicity such methods need to be decorated with
``@proxy.direct``.

Let's consider a crazy proxy that overrides the ``__repr__()`` method to censor
the word 'cat'. This is how it can be implemented:

    >>> class censor_cat(proxy):
    ...     @proxy.direct
    ...     def __repr__(self):
    ...         return repr(proxy.original(self)).replace(
    ...             str('cat'), str('***'))

Now let's create a proxy for our pets collection and see how it looks like:

    >>> pets_proxy = censor_cat(pets)
    >>> pets_proxy
    ['***', 'dog', 'fish', 'rooster']

As before, all other aspects of the proxy behave the same way. All of the
methods work and are forwarded to the original object. The type of the proxy
object is correct, event the meta-class of the object is correct (this matters
for ``issubclass()``, for instance).

Accessing the original object
-----------------------------

At any time one can access the original object hidden behind any proxy by using
the :meth:`proxy.original()` function. For example:

    >>> obj = 'hello world'
    >>> proxy.original(proxy(obj)) is obj
    True

Accessing proxy state
---------------------

At any time the state of any proxy object can be accessed using the
:meth:`proxy.state()` function. The state object behaves as a regular object
with attributes. It can be used to add custom state to an object that cannot
hold it, for example:

    >>> obj = 42
    >>> obj.foo = 42
    Traceback (most recent call last):
        ...
    AttributeError: 'int' object has no attribute 'foo'
    >>> obj = proxy(obj)
    >>> obj.foo = 42
    Traceback (most recent call last):
        ...
    AttributeError: 'int' object has no attribute 'foo'
    >>> proxy.state(obj).foo = 42
    >>> proxy.state(obj).foo
    42

Using the @proxy.direct decorator
---------------------------------

The ``@proxy.direct`` decorator can be used to disable the automatic
pass-through behavior that is exhibited by any proxy object. In practice we can
use it to either intercept and substitute an existing functionality or to add a
new functionality that doesn't exist in the original object.

First, let's write a custom proxy class for the ``bool`` class (which cannot be
used as a base class anymore) and change the core functionality.

    >>> class nay(proxy):
    ...
    ...     @proxy.direct
    ...     def __nonzero__(self):
    ...         return not bool(proxiee(self))
    ...
    ...     @proxy.direct
    ...     def __bool__(self):
    ...         return not bool(proxiee(self))

    >>> bool(nay(True))
    False
    >>> bool(nay(False))
    True
    >>> if nay([]):
    ...     print("It works!")
    It works!

Now, let's write a different proxy class that will add some new functionality

Here, the self_aware_proxy class gives any object a new property, ``is_proxy``
which always returns ``True``.

    >>> class self_aware_proxy(proxy):
    ...     @proxy.direct
    ...     def is_proxy(self):
    ...         return True
    >>> self_aware_proxy('hello').is_proxy()
    True

Limitations
-----------

There are only two things that that give our proxy away.

The ``type()`` function:

    >>> type(pets_proxy)  # doctest: +ELLIPSIS
    <class '...censor_cat[list]'>

And the ``id`` function (and anything that checks object identity):

    >>> pets_proxy is pets
    False
    >>> id(pets) == id(pets_proxy)
    False

That's it, enjoy. You can read the unit tests for additional interesting
details of how the proxy class works. Those are not covered in this short
introduction.

.. note::
    There are a number of classes and meta-classes but the only public
    interface is the :class:`proxy` class and the :meth:`proxy.direct`
    decorator.  See below for examples.

Deprecated 1.0 APIs
-------------------

If you've used Padme before you may have seen ``@unproxied()`` and
``proxiee()``.  They are still here but ``@unproxied`` is now spelled
``@proxy.direct`` and ``proxiee()`` is now ``proxy.original()``. This was done
to allow all of Padme to be used from the one :class:`proxy` class.
"""
from __future__ import print_function, absolute_import, unicode_literals

import logging
import operator
import sys

__author__ = 'Zygmunt Krynicki'
__email__ = 'zygmunt.krynicki@canonical.com'
__version__ = '1.1.1'
__all__ = (str('proxy'), )

_logger = logging.getLogger("padme")


class proxy_meta(type):

    """
    Meta-class for all proxy types.

    This meta-class is responsible for gathering the __unproxied__ attributes
    on each created class. The attribute is a frozenset of names that will not
    be forwarded to the ``proxiee`` but instead will be looked up on the proxy
    itself.
    """

    def __new__(mcls, name, bases, ns, *args, **kwargs):
        _logger.debug(
            "%s.__new__ with name: %r, bases: %r (args: %r, kwargs %r)",
            mcls.__name__, name, bases, args, kwargs)
        unproxied_set = set()
        for base in bases:
            if hasattr(base, '__unproxied__'):
                unproxied_set.update(base.__unproxied__)
        for ns_attr, ns_value in ns.items():
            if getattr(ns_value, 'unproxied', False):
                unproxied_set.add(ns_attr)
        if unproxied_set:
            _logger.debug(
                "proxy type %r will pass-thru %r", name, unproxied_set)
        ns['__unproxied__'] = frozenset(unproxied_set)
        # _logger.debug("injecting fresh _c_registry into %s", name)
        ns['_c_registry'] = {}
        cls = super(proxy_meta, mcls).__new__(mcls, name, bases, ns)
        cls._untyped_base = cls
        return cls

    def __getitem__(proxy_cls, proxiee_cls):
        proxy_cls = proxy_cls._untyped_base
        if not isinstance(proxiee_cls, type):
            raise ValueError("proxiee_cls must be a type")
        if proxiee_cls not in proxy_cls._m_registry:
            typed_proxy_meta = make_typed_proxy_meta(proxiee_cls)
            proxy_cls._m_registry[proxiee_cls] = typed_proxy_meta
        else:
            typed_proxy_meta = proxy_cls._m_registry[proxiee_cls]
        if proxiee_cls not in proxy_cls._c_registry:
            typed_proxy_cls = metaclass(typed_proxy_meta)(
                proxy_cls, str('{}[{}]').format(
                    proxy_cls.__name__, proxiee_cls.__name__))
            proxy_cls._c_registry[proxiee_cls] = typed_proxy_cls
        else:
            typed_proxy_cls = proxy_cls._c_registry[proxiee_cls]
        typed_proxy_cls._untyped_base = proxy_cls
        return typed_proxy_cls


def make_typed_proxy_meta(proxiee_cls):
    """

    Make a new proxy meta-class for the specified class of proxiee objects.

    .. note::

        Had python had an easier way of doing this, it would have been spelled
        as ``proxy_meta[cls]`` but I didn't want to drag pretty things into
        something nobody would ever see.

    :param proxiee_cls:
        The type of the that will be proxied
    :returns:
        A new meta-class that lexically wraps ``proxiee`` and ``proxiee_cls``
        and subclasses :class:`proxy_meta`.
    """
    def __instancecheck__(mcls, instance):
        # NOTE: this is never called in practice since
        # proxy(obj).__class__ is really obj.__class__.
        _logger.debug("__instancecheck__ %r on %r", instance, proxiee_cls)
        return isinstance(instance, proxiee_cls)

    def __subclasscheck__(mcls, subclass):
        # This is still called though since type(proxy(obj)) is
        # something else
        _logger.debug("__subclasscheck__ %r on %r", subclass, proxiee_cls)
        return issubclass(proxiee_cls, subclass)

    name = str('proxy_meta[{}]').format(proxiee_cls.__name__)
    bases = (proxy_meta,)
    ns = {
        '__doc__': """
        Meta-class for all proxies type-bound to type {}.

        This class implements two methods that participate in instance and
        class checks: ``__instancecheck__`` and ``__subclasscheck__``.
        """.format(proxiee_cls.__name__),
        '__instancecheck__': __instancecheck__,
        '__subclasscheck__': __subclasscheck__
    }
    return proxy_meta(name, bases, ns)


def _get_proxiee(proxy_obj):
    return object.__getattribute__(proxy_obj, '_original')


def _set_proxiee(proxy_obj, proxiee):
    return object.__setattr__(proxy_obj, '_original', proxiee)


def _get_unproxied(proxy):
    return type(proxy).__unproxied__


# All augmented assignment methods. We need to know those to let use intercept
# __getattribute__ access to them. Normally it is safe to directly call methods
# on the original object but augmented assignment a (op)= b actually changes a
# and we need to make sure that a proxy object is returned there.
_imethods = set([
    '__iadd__',
    '__isub__',
    '__imul__',
    '__itruediv__',
    '__ifloordiv__',
    '__imod__',
    '__ipow__',
    '__ilshift__',
    '__irshift__',
    '__iand__',
    '__ixor__',
    '__ior__',
])
if sys.version_info[0] == 2:
    _imethods.add('__idiv__')

_imethods = frozenset(_imethods)


def _imethod(self, other, name, op):
    """
    Shared implementation of __iFUNC__ method.

    :param self:
        A proxy_base instance
    :param other:
        Any right-hand-side value
    :param name:
        Name of the __iFUNC__
    :param op:
        Appropriate operator.__iFUNC__ operator
    :returns:
        self
    """
    proxiee_old = proxiee_new = _get_proxiee(self)
    _logger.debug("%s on proxiee (%r)", name, proxiee_old)
    # NOTE: This _may_ or _may not be_ calling __iFUNC__
    # as the proxiee may not support it in the first place
    proxiee_new = op(proxiee_old, other)
    if proxiee_new is not proxiee_old:
        # NOTE: all of the augmented assignment methods handle the case where
        # the __iFUNC__ method returns something other than self. To maintain
        # the illusion that the proxy is not there the internal proxiee
        # reference is changed to the new proxiee.
        _logger.debug("%s creates new %s (%r)",
                      name, type(self).__name__, proxiee_new)
        return type(self)(proxiee_new)
    return self


class proxy_base(object):

    """
    Base class for all proxies.

    This class implements the bulk of the proxy work by having a lot of dunder
    methods that delegate their work to a ``proxiee`` object. The ``proxiee``
    object must be available as the ``__proxiee__`` attribute on a class
    deriving from ``base_proxy``. Apart from ``__proxiee__`, the
    ``__unproxied__`` attribute, which should be a frozenset, must also be
    present in all derived classes.

    In practice, the two special attributes are injected via
    ``boundproxy_meta`` created by :func:`make_boundproxy_meta()`. This class
    is also used as a base class for the tricky :class:`proxy` below.

    NOTE: Look at ``pydoc3 SPECIALMETHODS`` section titled ``Special method
    lookup`` for a rationale of why we have all those dunder methods while
    still having __getattribute__()
    """

    # NOTE: the order of methods below matches that of ``pydoc3
    # SPECIALMETHODS``. The "N/A to instances" text means that it makes no
    # sense to add proxy support to the specified method because that method
    # makes no sense on instances. Proxy is designed to intercept access to
    # *objects*, not construction of such objects in the first place.

    # N/A to instances: __new__

    # N/A to instances: __init__

    def __del__(self):
        """
        No-op object delete method.

        .. note::
            This method is handled specially since it must be called after an
            object becomes unreachable. As long as the proxy object itself
            exits, it holds a strong reference to the original object.
        """

    def __repr__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__repr__ on proxiee (%r)", proxiee)
        return repr(proxiee)

    def __str__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__str__ on proxiee (%r)", proxiee)
        return str(proxiee)

    def __bytes__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__bytes__ on proxiee (%r)", proxiee)
        return bytes(proxiee)

    def __format__(self, format_spec):
        proxiee = _get_proxiee(self)
        _logger.debug("__format__ on proxiee (%r)", proxiee)
        return format(proxiee, format_spec)

    def __lt__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__lt__ on proxiee (%r)", proxiee)
        return proxiee < other

    def __le__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__le__ on proxiee (%r)", proxiee)
        return proxiee <= other

    def __eq__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__eq__ on proxiee (%r)", proxiee)
        return proxiee == other

    def __ne__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__ne__ on proxiee (%r)", proxiee)
        return proxiee != other

    def __gt__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__gt__ on proxiee (%r)", proxiee)
        return proxiee > other

    def __ge__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__ge__ on proxiee (%r)", proxiee)
        return proxiee >= other

    if sys.version_info[0] == 2:
        # NOTE: having it in python3 is harmless but it's handled by
        # __getattribute__ already
        def __cmp__(self, other):
            proxiee = _get_proxiee(self)
            _logger.debug("__cmp__ on proxiee (%r)", proxiee)
            return cmp(proxiee, other)

    def __hash__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__hash__ on proxiee (%r)", proxiee)
        return hash(proxiee)

    # NOTE: __bool__ is spelled as __nonzero__ in pre-3K world
    # See PEP:`3100` for details.
    if sys.version_info[0] == 3:
        def __bool__(self):
            proxiee = _get_proxiee(self)
            _logger.debug("__bool__ on proxiee (%r)", proxiee)
            return bool(proxiee)
    else:
        def __nonzero__(self):
            proxiee = _get_proxiee(self)
            _logger.debug("__nonzero__ on proxiee (%r)", proxiee)
            return bool(proxiee)

    if sys.version_info[0] == 2:
        def __unicode__(self):
            proxiee = _get_proxiee(self)
            _logger.debug("__unicode__ on proxiee (%r)", proxiee)
            return unicode(proxiee)

    def __getattr__(self, name):
        proxiee = _get_proxiee(self)
        _logger.debug("__getattr__ %r on proxiee (%r)", name, proxiee)
        return getattr(proxiee, name)

    def __getattribute__(self, name):
        is_unproxied = name in _get_unproxied(self)
        is_imethod = name in _imethods
        if is_unproxied:
            _logger.debug("%s.__getattribute__ %r on proxy itself (direct)",
                          type(self).__name__, name)
            return object.__getattribute__(self, name)
        elif is_imethod:
            _logger.debug(
                "%s.__getattribute__ %r on proxy itself (augmented"
                " assignment)", type(self).__name__, name)
            proxiee = _get_proxiee(self)
            object.__getattribute__(proxiee, name)
            return object.__getattribute__(self, name)
        else:
            proxiee = _get_proxiee(self)
            _logger.debug("%s.__getattribute__ %r on proxiee (%r)",
                          type(self).__name__, name, proxiee)
            return getattr(proxiee, name)

    def __setattr__(self, name, value):
        if name not in _get_unproxied(self):
            proxiee = _get_proxiee(self)
            _logger.debug("__setattr__ %r on proxiee (%r)", name, proxiee)
            setattr(proxiee, name, value)
        else:
            _logger.debug("__setattr__ %r on proxy itself (direct)", name)
            object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name not in _get_unproxied(self):
            proxiee = _get_proxiee(self)
            _logger.debug("__delattr__ %r on proxiee (%r)", name, proxiee)
            delattr(proxiee, name)
        else:
            _logger.debug("__delattr__ %r on proxy itself (direct)", name)
            object.__delattr__(self, name)

    def __dir__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__dir__ on proxiee (%r)", proxiee)
        return dir(proxiee)

    def __get__(self, instance, owner):
        proxiee = _get_proxiee(self)
        _logger.debug("__get__ on proxiee (%r)", proxiee)
        return proxiee.__get__(instance, owner)

    def __set__(self, instance, value):
        proxiee = _get_proxiee(self)
        _logger.debug("__set__ on proxiee (%r)", proxiee)
        proxiee.__set__(instance, value)

    def __delete__(self, instance):
        proxiee = _get_proxiee(self)
        _logger.debug("__delete__ on proxiee (%r)", proxiee)
        proxiee.__delete__(instance)

    def __call__(self, *args, **kwargs):
        proxiee = _get_proxiee(self)
        _logger.debug("__call__ on proxiee (%r)", proxiee)
        return proxiee(*args, **kwargs)

    def __len__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__len__ on proxiee (%r)", proxiee)
        return len(proxiee)

    if sys.version_info[0:2] >= (3, 4):
        def __length_hint__(self):
            proxiee = _get_proxiee(self)
            _logger.debug("__length_hint__ on proxiee (%r)", proxiee)
            return proxiee.__length_hint__()

    def __getitem__(self, item):
        proxiee = _get_proxiee(self)
        _logger.debug("__getitem__ on proxiee (%r)", proxiee)
        return proxiee[item]

    def __setitem__(self, item, value):
        proxiee = _get_proxiee(self)
        _logger.debug("__setitem__ on proxiee (%r)", proxiee)
        proxiee[item] = value

    def __delitem__(self, item):
        proxiee = _get_proxiee(self)
        _logger.debug("__delitem__ on proxiee (%r)", proxiee)
        del proxiee[item]

    def __iter__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__iter__ on proxiee (%r)", proxiee)
        return iter(proxiee)

    def __reversed__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__reversed__ on proxiee (%r)", proxiee)
        return reversed(proxiee)

    def __contains__(self, item):
        proxiee = _get_proxiee(self)
        _logger.debug("__contains__ on proxiee (%r)", proxiee)
        return item in proxiee

    # NOTE: __{get,set,del}slice__() methods are not implemented as they are
    # not used anymore by anything, AFAIK

    # all basic numeric methods

    def __add__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__add__ on proxiee (%r)", proxiee)
        return proxiee + other

    def __sub__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__sub__ on proxiee (%r)", proxiee)
        return proxiee - other

    def __mul__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__mul__ on proxiee (%r)", proxiee)
        return proxiee * other

    if sys.version_info[0:2] >= (3, 5):
        def __matmul__(self, other):
            proxiee = _get_proxiee(self)
            _logger.debug("__matmul__ on proxiee (%r)", proxiee)
            # NOTE: this is equivalent to ``proxiee @ other`` but we cannot use
            # this syntax as long as 3.4 and earlier have to be supported.
            return operator.matmul(proxiee, other)

    if sys.version_info[0] == 2:
        def __div__(self, other):
            proxiee = _get_proxiee(self)
            _logger.debug("__div__ on proxiee (%r)", proxiee)
            return operator.div(proxiee, other)

    def __truediv__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__truediv__ on proxiee (%r)", proxiee)
        return operator.truediv(proxiee, other)

    def __floordiv__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__floordiv__ on proxiee (%r)", proxiee)
        return proxiee // other

    def __mod__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__mod__ on proxiee (%r)", proxiee)
        return proxiee % other

    def __divmod__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__divmod__ on proxiee (%r)", proxiee)
        return divmod(proxiee, other)

    def __pow__(self, other, modulo=None):
        proxiee = _get_proxiee(self)
        _logger.debug("__pow__ on proxiee (%r)", proxiee)
        return pow(proxiee, other, modulo)

    def __lshift__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__lshift__ on proxiee (%r)", proxiee)
        return proxiee << other

    def __rshift__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rshift__ on proxiee (%r)", proxiee)
        return proxiee >> other

    def __and__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__and__ on proxiee (%r)", proxiee)
        return proxiee & other

    def __xor__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__xor__ on proxiee (%r)", proxiee)
        return proxiee ^ other

    def __or__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__or__ on proxiee (%r)", proxiee)
        return proxiee | other

    # all reversed numeric methods

    def __radd__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__radd__ on proxiee (%r)", proxiee)
        return other + proxiee

    def __rsub__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rsub__ on proxiee (%r)", proxiee)
        return other - proxiee

    def __rmul__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rmul__ on proxiee (%r)", proxiee)
        return other * proxiee

    if sys.version_info[0:2] >= (3, 5):
        def __rmatmul__(self, other):
            proxiee = _get_proxiee(self)
            _logger.debug("__rmatmul__ on proxiee (%r)", proxiee)
            # NOTE: this is equivalent to ``proxiee @ other`` but we cannot use
            # this syntax as long as 3.4 and earlier have to be supported.
            return operator.matmul(other, proxiee)

    if sys.version_info[0] == 2:
        def __rdiv__(self, other):
            proxiee = _get_proxiee(self)
            _logger.debug("__rdiv__ on proxiee (%r)", proxiee)
            return operator.__div__(other, proxiee)

    def __rtruediv__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rtruediv__ on proxiee (%r)", proxiee)
        return operator.__truediv__(other, proxiee)

    def __rfloordiv__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rfloordiv__ on proxiee (%r)", proxiee)
        return other // proxiee

    def __rmod__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rmod__ on proxiee (%r)", proxiee)
        return other % proxiee

    def __rdivmod__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rdivmod__ on proxiee (%r)", proxiee)
        return divmod(other, proxiee)

    def __rpow__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rpow__ on proxiee (%r)", proxiee)
        return pow(other, proxiee)

    def __rlshift__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rlshift__ on proxiee (%r)", proxiee)
        return other << proxiee

    def __rrshift__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rrshift__ on proxiee (%r)", proxiee)
        return other >> proxiee

    def __rand__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rand__ on proxiee (%r)", proxiee)
        return other & proxiee

    def __rxor__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rxor__ on proxiee (%r)", proxiee)
        return other ^ proxiee

    def __ror__(self, other):
        proxiee = _get_proxiee(self)
        _logger.debug("__rrshift__ on proxiee (%r)", proxiee)
        return other | proxiee

    # all augmented assignment numeric methods

    def __iadd__(self, other):
        return _imethod(self, other, '__iadd__', operator.iadd)

    def __isub__(self, other):
        return _imethod(self, other, '__isub__', operator.isub)

    def __imul__(self, other):
        return _imethod(self, other, '__imul__', operator.imul)

    if sys.version_info[0:2] >= (3, 5):
        def __imatmul__(self, other):
            return _imethod(self, other, '__imatmul__', operator.imatmul)

    if sys.version_info[0] == 2:
        def __idiv__(self, other):
            return _imethod(self, other, '__idiv__', operator.idiv)

    def __itruediv__(self, other):
        return _imethod(self, other, '__itruediv__', operator.itruediv)

    def __ifloordiv__(self, other):
        return _imethod(self, other, '__ifloordiv__', operator.ifloordiv)

    def __imod__(self, other):
        return _imethod(self, other, '__imod__', operator.imod)

    def __ipow__(self, other, modulo=None):
        assert modulo is None
        return _imethod(self, other, '__ipow__', operator.ipow)

    def __ilshift__(self, other):
        return _imethod(self, other, '__ilshift__', operator.ilshift)

    def __irshift__(self, other):
        return _imethod(self, other, '__irshift__', operator.irshift)

    def __iand__(self, other):
        return _imethod(self, other, '__iand__', operator.iand)

    def __ixor__(self, other):
        return _imethod(self, other, '__ixor__', operator.ixor)

    def __ior__(self, other):
        return _imethod(self, other, '__ior__', operator.ior)

    # all miscellaneous numeric methods

    def __neg__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__neg__ on proxiee (%r)", proxiee)
        return - proxiee

    def __pos__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__pos__ on proxiee (%r)", proxiee)
        return + proxiee

    def __abs__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__abs__ on proxiee (%r)", proxiee)
        return abs(proxiee)

    def __invert__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__invert__ on proxiee (%r)", proxiee)
        return ~ proxiee

    # Helpers for built-ins: complex(), int(), float() and round()

    def __complex__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__complex__ on proxiee (%r)", proxiee)
        return complex(proxiee)

    def __int__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__int__ on proxiee (%r)", proxiee)
        return int(proxiee)

    if sys.version_info[0] == 2:
        def __long__(self):
            proxiee = _get_proxiee(self)
            _logger.debug("__long__ on proxiee (%r)", proxiee)
            return long(proxiee)

    def __float__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__float__ on proxiee (%r)", proxiee)
        return float(proxiee)

    if sys.version_info[0] == 3:
        def __round__(self, n):
            proxiee = _get_proxiee(self)
            _logger.debug("__float__ on proxiee (%r)", proxiee)
            return round(proxiee, n)

    if sys.version_info[0] == 2:
        def __oct__(self):
            proxiee = _get_proxiee(self)
            _logger.debug("__oct__ on proxiee (%r)", proxiee)
            return oct(proxiee)

        def __hex__(self):
            proxiee = _get_proxiee(self)
            _logger.debug("__hex__ on proxiee (%r)", proxiee)
            return hex(proxiee)

    def __index__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__index__ on proxiee (%r)", proxiee)
        return operator.index(proxiee)

    if sys.version_info[0] == 2:
        def __coerce__(self, other):
            proxiee = _get_proxiee(self)
            _logger.debug("__coerce__ on proxiee (%r)", proxiee)
            return coerce(proxiee, other)

    def __enter__(self):
        proxiee = _get_proxiee(self)
        _logger.debug("__enter__ on proxiee (%r)", proxiee)
        return proxiee.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        proxiee = _get_proxiee(self)
        _logger.debug("__exit__ on proxiee (%r)", proxiee)
        return proxiee.__exit__(exc_type, exc_value, traceback)


class proxy_state(object):

    """
    Support class for working with proxy state.

    This class implements simple attribute-based access methods. It is normally
    instantiated internally for each proxy object. You don't want to fuss with
    it manually, instead just use :meth:`proxy.state()` function to access it.
    """

    def __init__(self, proxy_obj):
        proxy_dict = object.__getattribute__(proxy_obj, '__dict__')
        object.__setattr__(self, '__dict__', proxy_dict)

    def __repr__(self):
        return "<{}.{} object at {:#x} with state {!r}>".format(
            __name__, self.__class__.__name__, id(self), self.__dict__)


class metaclass(object):

    """
    Support decorator for Python-agnostic meta-class injection.

    The following snippet illustrates how to use this decorator:

    >>> class my_meta(type):
    ...     METACLASS_WORKS = True
    >>> @metaclass(my_meta)
    ... class my_cls(object):
    ...     pass
    >>> assert my_cls.METACLASS_WORKS
    """

    def __init__(self, mcls):
        self.mcls = mcls

    def __call__(self, cls, name=None):
        # NOTE: the name is not changed so that sphinx doesn't think this is an
        # alias of some other object. This is pretty weird but important.
        if name is None:
            name = cls.__name__
        bases = (cls,)
        ns = {
            # Patch-in __doc__ so that various help systems work better
            '__doc__': cls.__doc__,
        }
        _logger.debug("metaclass(%s)(%s, name=%r)",
                      self.mcls.__name__, cls.__name__, name)
        return self.mcls(name, bases, ns)


@metaclass(proxy_meta)
class proxy(proxy_base):

    """
    A mostly transparent proxy type.

    The proxy class can be used in two different ways. First, as a callable
    ``proxy(obj)``. This simply returns a proxy for a single object.

        >>> truth = [str('trust no one')]
        >>> lie = proxy(truth)

    This will return an instance of a new ``proxy`` sub-class which for all
    intents and purposes, to the extent possible in CPython, forwards all
    requests to the original object.

    One can still examine the proxy with some ways::

        >>> lie is truth
        False
        >>> type(lie) is type(truth)
        False

    Having said that, the vast majority of stuff will make the proxy behave
    identically to the original object.

        >>> lie[0]
        'trust no one'
        >>> lie[0] = str('trust the government')
        >>> truth[0]
        'trust the government'

    The second way of using the ``proxy`` class is as a base class. In this
    way, one can actually override certain methods. To ensure that all the
    dunder methods work correctly please use the ``@proxy.direct`` decorator on
    them.

        >>> import codecs
        >>> class crypto(proxy):
        ...
        ...     @proxy.direct
        ...     def __repr__(self):
        ...         return codecs.encode(
        ...             super(crypto, self).__repr__(), "rot_13")

    With this weird class, we can change the repr() of any object we want to be
    ROT-13 encoded. Let's see:

        >>> orig = [str('ala ma kota'), str('a kot ma ale')]
        >>> prox = crypto(orig)

    We can sill access all of the data through the proxy:

        >>> prox[0]
        'ala ma kota'

    But the whole repr() is now a bit different than usual:

        >>> prox
        ['nyn zn xbgn', 'n xbg zn nyr']
    """

    # Registry of known typed_proxy_meta objects
    _m_registry = {}

    # There is a corresponding _c_registry but it is reset for each proxy
    # subclass by proxy_meta.

    def __new__(proxy_cls, proxiee, *args, **kwargs):
        """
        Create a new instance of ``proxy()`` wrapping ``proxiee``.

        :param proxiee:
            The object to proxy
        :returns:
            An instance of new subclass of ``proxy`` with injected meta-class
            proxy_meta[cls] where cls is the type of proxiee.
        """
        _logger.debug(
            "%s.__new__ with proxiee: %r (args: %r, kwargs %r)",
            proxy_cls.__name__, proxiee, args, kwargs)
        proxiee_cls = type(proxiee)
        typed_proxy_cls = proxy_cls[proxiee_cls]
        proxy_obj = object.__new__(typed_proxy_cls)
        state = proxy_state(proxy_obj)
        # _logger.debug("%s.__new__ inserted _original into instance",
        #               proxy_cls.__name__)
        state._original = proxiee
        # _logger.debug("%s.__new__ is about to return", proxy_cls.__name__)
        return proxy_obj

    def __init__(proxy_obj, proxiee):
        """
        Initialize a fresh proxy instance specific to ``proxiee``.

        :param proxiee:
            The object to proxy
        """
        _logger.debug(
            "%s.__init__ with proxiee: %r", type(proxy_obj).__name__, proxiee)

    @staticmethod
    def direct(fn):
        """
        Mark a method as not-to-be-proxied.

        This decorator can be used inside :class:`proxy` sub-classes. Please
        consult the documentation of ``proxy`` for details.

        In practical terms there are two reasons one can use ``proxy.direct``.

        - First, as a way to change the behaviour of a proxy. In this mode a
          method that already exists on the proxied object is intercepted and
          custom code is executed. The custom code can still call the original,
          if desired, by using the :meth:`proxy.original()` function to access
          the original object
        - Second, as a way to introduce new functionality to an object. In that
          sense the resulting proxy will be less transparent as all
          ``proxy.direct`` methods are explicitly visible and available to
          access but this may be exactly what is desired in some situations.

        For additional details on how to use this decorator, see the
        documentation of the :mod:`padme` module.
        """
        fn.unproxied = True
        _logger.debug("function %r marked as unproxied/direct", fn)
        return fn

    @staticmethod
    def original(proxy_obj):
        """
        Return the :term:`proxiee` hidden behind the given proxy.

        :param proxy:
            An instance of :class:`proxy` or its subclass.
        :returns:
            The original object that the proxy is hiding.

        This function can be used to access the object hidden behind a proxy.
        This is useful when access to original object is necessary, for
        example, to implement an method decorated with ``@proxy.direct``.

        In the following example, we cannot use ``super()`` to get access to
        the append method because the proxy does not really subclass the list
        object.  To override the ``append`` method in a way that allows us to
        still call the original we must use the :meth:`proxy.original()`
        function::

            >>> class verbose_list(proxy):
            ...     @proxy.direct
            ...     def append(self, item):
            ...         print("Appending:", item)
            ...         proxy.original(self).append(item)

        Now that we have a ``verbose_list`` class, we can use it to see that it
        works as expected:

            >>> l = verbose_list([])
            >>> l.append(42)
            Appending: 42
            >>> l
            [42]
        """
        state = proxy_state(proxy_obj)
        return state._original

    @staticmethod
    def state(proxy_obj):
        """
        Support function for accessing the state of a proxy object.

        The main reason for this function to exist is to facilitate creating
        stateful proxy objects. This allows you to put state on objects that
        cannot otherwise hold it (typically built-in classes or classes using
        ``__slots__``) and to keep the state invisible to the original object
        so that it cannot interfere with any future APIs.

        To use it, just call it on any proxy object and use the return value as
        a normal object you can get/set attributes on. For example:

            >>> life = proxy(42)

        We cannot set attributes on integer instances:

            >>> life.foo = True
            Traceback (most recent call last):
                ...
            AttributeError: 'int' object has no attribute 'foo'

        But we can do that with a proxy around the integer object.

            >>> proxy.state(life).foo = True
            >>> proxy.state(life).foo
            True
        """
        return proxy_state(proxy_obj)


# 1.0 backwards-compatibility aliases
unproxied = proxy.direct
proxiee = proxy.original
