.. :changelog:

History
=======

1.1 (YYYY-MM-DD)
----------------
* Add general support for **Python 2.7**.
* Make ``__nonzero__()`` and ``__unicode__()`` exlusive to Python 2.x.
* Make ``__bool__()`` and ``__bytes__()`` exclusive to Python 3.x.
* Make ``__length_hint()`` exclusive to Python 3.4.
* Add support for the ``__cmp__()`` method, exclusive to Python 2.x.
* Add support for accessing the proxied object with the new
  :meth:`~padme.proxy.original()` function.
* Rename the ``padme.unproxied`` decorator to :meth:`~padme.proxy.direct()`

1.0 (2014-02-11)
----------------

* First release on PyPI.
* Add a short introduction. 
* Enable travis-ci.org integration.
* Remove numbering of generated meta-classes

2015
----

* Released on PyPI as a part of plainbox as ``plainbox.impl.proxy``
