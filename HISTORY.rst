.. :changelog:

History
=======

1.1.1 (2015-03-04)
------------------
* Add general support for **Python 2.7**.
* All numeric methods are now supported with some methods
  exclusive to Python 2.x (``__div__()``, ``__coerce__()``,
  ``__oct__()``, ``__hex__()``).
* Add support for the new matrix multiplication operator ``@``.
* Make ``__nonzero__()`` and ``__unicode__()`` exlusive to Python 2.x.
* Make ``__bool__()`` and ``__bytes__()`` exclusive to Python 3.x.
* Make ``__length_hint()`` exclusive to Python 3.4.
* Add support for the ``__cmp__()`` method, exclusive to Python 2.x.
* Add support for accessing the proxied object with the new
  :meth:`~padme.proxy.original()` function.
* Add support for accessing proxy state with the new
  :meth:`~padme.proxy.state()` function.
* De-couple proxy classes from proxied objects, much more lightweight proxy
  design is possible this way (less objects, lower cost to create each new proxy).

1.0 (2014-02-11)
----------------

* First release on PyPI.
* Add a short introduction. 
* Enable travis-ci.org integration.
* Remove numbering of generated meta-classes

2015
----

* Released on PyPI as a part of plainbox as ``plainbox.impl.proxy``
