#!/usr/bin/env python
# Copyright 2015 Canonical Ltd.
# Written by:
#   Daniel Manrique <daniel.manrique@canonical.com>
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
Example for using ``proxy()`` to compute checksum of written data.

This example shows how one can take and existing object which is not easy to
subclass correctly (unless you know the internals of the python io stack at the
particular version you are interested in) and uses a proxy to intercept the
write method to keep track of the data written to the file.

The method works correctly on any file-like object that has a write method, it
also doens't require multiple definitions, the one ``written_hash_proxy`` does
everything needed for all file-like classes.
"""
from __future__ import print_function

import hashlib
import argparse
try:
    import urllib2 as requestlib
except:
    from urllib import request as requestlib

from padme import proxy


class written_hash_proxy(proxy):

    """
    Proxy for file-like objects that maintain a hash of written data.

    For example, this allows to substitute sys.stdout with a version
    that keeps track of the hash of everything written.

        >>> import sys
        >>> stdout = written_hash_proxy(sys.stdout)

    The created proxy stdout has extra state accessible via the
    ``proxy.state()`` helper function:

        >>> proxy.state(stdout).digest.hexdigest
        <Magic stuff>

    The write method is intercepted via ``@proxy.direct`` to automatically
    update the digest:

        >>> stdout.write("hello")
        hello
        >>> proxy.state(stdout).digest.hexdigest
        blargh
    """

    def __init__(self, proxiee, name='md5'):
        """
        Initialize a fresh written_hash_proxy.

        :param proxiee:
            The object that the proxy will wrap (ignored)
        :param name:
            Name of the hashing algorithm to use.

        This method just sets up the desired digest object.
        """
        # Use a proxy.state(self) to create a state attribute unique to this
        # proxy object and store the hash of the data written so far. This
        # state attribute will never clash with anything that the original
        # object happens to have internally.
        proxy.state(self).digest = hashlib.new(name)

    @proxy.direct
    def write(self, data):
        """
        Intercepted method for writing data.

        :param data:
            Data to write
        :returns:
            Whatever the original method returns
        :raises:
            Whatever the original method raises

        This method updates the internal digest object with with the new data
        and then proceeds to call the original write method.
        """
        # Intercept the write method (that's what @direct does) and both write
        # the data using the original write method (using proxiee(self).write)
        # and update the hash of the data written so far (using
        # proxy.state(self).digest).
        proxy.state(self).digest.update(data)
        return proxy.original(self).write(data)


def main():
    """ Main function of this example. """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--digest', default="md5", help="Digest to use",
        choices=sorted(
            getattr(hashlib, 'algorithms', None)
            or hashlib.algorithms_available))
    parser.add_argument(
        '--url', default="http://example.org", help="URL to load")
    parser.add_argument(
        '-o', '--output', type=argparse.FileType('wb'), metavar='FILE',
        default='-', help="Where to write the retrieved conentent")
    opts = parser.parse_args()
    request = requestlib.Request(opts.url)
    reader = requestlib.urlopen(request)
    stream = written_hash_proxy(
        opts.output.buffer if hasattr(opts.output, 'buffer') else opts.output,
        name=opts.digest)
    for chunk in reader:
        stream.write(chunk)
    stream.flush()
    print("{} of {} is {}".format(
        proxy.state(stream).digest.name, opts.url,
        proxy.state(stream).digest.hexdigest()))


if __name__ == '__main__':
    main()
