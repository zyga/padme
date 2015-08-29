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

from padme.masking import masking_proxy


__all__ = ('get_api', 'get_private_api', 'get_public_proxy')


def get_api(obj):
    """
    Get the complete API of a given object or class.

    :param obj:
        A class or object to introspect
    :returns:
        A set of attributes that constitute the API of the given class.

    When called with a class dynamic instance attributes are *not* discovered.
    It is strongly recommended to include a list of such attributes in the
    non-standard class-attribute ``__attributes__``.
    """
    api = set(dir(obj))
    if hasattr(obj, '__slots__'):
        api |= frozenset(obj.__slots__)
    if hasattr(obj, '__attributes__'):
        api |= frozenset(obj.__attributes__)
    return api


def get_private_api(obj, *ifaces):
    """
    Get the private API of a given object not exposed through public interfaces.

    :param obj:
        A class or object to introspect
    :param ifaces:
        A list of interface classes that describe some public API.
    :returns:
        A set of attributes that constitute the private API of the object
        that are not exposes by any of the specified interfaces.
    """
    api = get_api(obj)
    for iface in ifaces:
        api -= get_api(iface)
    return api


def get_public_proxy(obj, *ifaces):
    """
    Get a proxy exposing just the public API of a given object.

    :param obj:
        The object in question
    :param ifaces:
        The list of interfaces to expose on the given object. Typically
        this will be a list of interface-like classes.
    :returns:
        A new proxy to ``obj`` that masks (hides) all of the attributes
        not exposed by at least one interface listed in ``ifaces``.
    """
    return masking_proxy(obj, get_private_api(obj, *ifaces))
