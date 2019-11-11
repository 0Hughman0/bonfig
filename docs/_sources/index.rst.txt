.. Bonfig documentation master file, created by
   sphinx-quickstart on Thu Dec 27 23:28:20 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _home:

Welcome to Bonfig's documentation!
==================================


.. code:: python

   >>> from Bonfig import Bonfig, Store
   >>> import json
   >>> class Config(Bonfig):
   ...     store = Store()
   ...     pi = store.FloatField()
   ...     def load(self):
   ...         self.store = json.loads('{"pi": 3.14159}')
   >>>
   >>> conf = Config()
   >>> conf.pi
   3.14159
   >>> conf.store
   mappingproxy({'pi': 3.14159})


Stop writing your configurations as dictionaries and strange floating dataclasses, make them `Bonfigs` and make use of
a whole bunch of great features:

* Declare your configurations as easy to read classes.
* Get all the power that comes with classes built into your configurations - polymorphism, custom methods and custom initialisation.
* Sleep safe in the knowledge your config won't change unexpectedly.
* Ready made serialisation and deserialisation using out the box `Fields` - `IntField`, `FloatField`, `BoolField`, `DatetimeField` and `PathField`.


Sound good? Get started at :ref:`quickstart`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   cheatsheet
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
