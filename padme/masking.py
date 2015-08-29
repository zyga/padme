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

import logging

from padme import proxy

try:
    from collections import UserDict
except ImportError:
    from padme._collections import UserDict

__all__ = ('masking_proxy',)

_logger = logging.getLogger('padme')


class MaskedAttributeError(AttributeError):

    """Exception raised when a masked attribute is accessed."""


class MaskedKeyError(KeyError):

    """Exception raised when a masked key is accessed."""


class weakref_allowed_property(property):

    """A subclass of property that can be weakly referenced."""


class masking_proxy(proxy):

    """
    A specialized proxy that hides the presence of arbitrary attributes.

    This proxy class can be used to create a proxy which exposes a subset
    of the original object. The original intent of this class was to return
    a proxy that is constrained to the set stable API methods. Methods that
    are not stable can be effectively hidden. The original object is still
    correctly tracked so any mutable state can be easily accessed without
    any additional penalty or synchronization.
    """

    def __new__(proxy_cls, proxiee, masked=(), *args, **kwargs):
        """
        Create a new instance of ``proxy()`` wrapping ``proxiee``.

        :param proxiee:
            The object to proxy
        :param masked:
            A set of attributes to mask as if they didn't exist
        :returns:
            An instance of new subclass of ``proxy`` with injected meta-class
            proxy_meta[cls] where cls is the type of proxiee.
        """
        _logger.debug(
            "%s.__new__ with proxiee: %r, masked %r (args: %r, kwargs %r)",
            proxy_cls.__name__, proxiee, masked, args, kwargs)
        proxy_obj = super(masking_proxy, proxy_cls).__new__(
            proxy_cls, proxiee, *args, **kwargs)
        # Remember the set of masked attributes
        proxy.state(proxy_obj)._masked = frozenset(masked)
        return proxy_obj

    def __init__(proxy_obj, proxiee, masked=()):
        _logger.debug(
            "%s.__init__ with proxiee: %r, masked: %r",
            type(proxy_obj).__name__, proxiee, masked)

    def __getattr__(self, name):
        is_masked = proxy.state(self)._masked
        if is_masked:
            _logger.debug("%s.__getattr__ %r (masked)",
                          type(self).__name__, name)
            # XXX: Without this Python 2.7.9 seems to leak a reference
            # to self. It might be a bug in python.
            del self
            raise MaskedAttributeError(name)
        return super(masking_proxy, self).__getattr__(name)

    def __getattribute__(self, name):
        if name in proxy.state(self)._masked:
            _logger.debug("%s.__getattribute__ %r (masked)",
                          type(self).__name__, name)
            raise MaskedAttributeError(name)
        return super(masking_proxy, self).__getattribute__(name)

    def __setattr__(self, name, value):
        if name in proxy.state(self)._masked:
            _logger.debug("%s.__setattr__ %r (masked)",
                          type(self).__name__, name)
            raise MaskedAttributeError(name)
        return super(masking_proxy, self).__setattr__(name, value)

    def __delattr__(self, name):
        if name in proxy.state(self)._masked:
            _logger.debug("%s.__delattr__ %r (masked)",
                          type(self).__name__, name)
            raise MaskedAttributeError(name)
        return super(masking_proxy, self).__delattr__(name)

    def __dir__(self):
        proxiee = proxy.original(self)
        _logger.debug("__dir__ on proxiee (%r) (with masking)", proxiee)
        masked = proxy.state(self)._masked
        return [name for name in super(masking_proxy, self).__dir__()
                if name not in masked]

    @proxy.direct
    @weakref_allowed_property
    def __dict__(self):
        proxiee = proxy.original(self)
        _logger.debug("__dict__ on proxiee (%r) (with masking)", proxiee)
        return MaskingDict(proxiee.__dict__, proxy.state(self)._masked)


class MaskingDict(UserDict):

    """
    Dictionary that stores, but hides, some keys.

    .. note::
        Unlike the base UserDict class, this implementation _does_ store
        the initial dictionary data and keeps it around. If the original
        dictionary is modified then all the changes will remain "live"
        in the masked dictionary.

    >>> data = {'name': 'Bob', 'password': 'secret'}
    >>> masked_data = MaskingDictionary(data, {'password'})
    >>> masked_data
    {'name': 'Bob'}
    """

    def __init__(self, data, masked):
        self.data = data
        self._masked = frozenset(masked)

    def __contains__(self, key):
        if key in self._masked:
            return False
        return super(MaskingDict, self).__contains__(key)

    def __delitem__(self, key):
        if key in self._masked:
            raise MaskedKeyError(key)
        return super(MaskingDict, self).__delitem__(key)

    def __getitem__(self, key):
        if key in self._masked:
            raise MaskedKeyError(key)
        return super(MaskingDict, self).__getitem__(key)

    def __len__(self):
        return len(set(self.data.keys()) - self._masked)

    def __iter__(self):
        for key in self.data:
            if key not in self._masked:
                yield key

    def __repr__(self):
        return repr({
            key: value
            for key, value in self.data.items() if key not in self._masked
        })

    def __setitem__(self, key, value):
        if key in self._masked:
            raise MaskedKeyError(key)
        return super(MaskingDict, self).__setitem__(key, value)
