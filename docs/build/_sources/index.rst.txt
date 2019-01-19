.. Bonfig documentation master file, created by
   sphinx-quickstart on Thu Dec 27 23:28:20 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _home:

Welcome to Bonfig's documentation!
==================================


.. code:: python

   from Bonfig import *
   import configparser
   class INIConfig(Bonfig):
       store = Store()
       SECTION = store.Section()
       A = SECTION.FloatField()

       def load(self):
           self.store = configparser.ConfigParser()
           self.store.read_string("[SECTION]\nA = 3.14159")

Stop writing your configurations as dictionaries and strange floating dataclasses, make them `Bonfigs` and make use of
a whole bunch of great features:

* Declare your configurations as easy to read classes.
* Get all the power that comes with classes built into your configurations - polymorphism, custom methods and custom initialisation.
* Safety considered with configuration lock-ability.
* Ready made serialisation and deserialisation with readmade custom `Fields` - `IntField`, `FloatField`, `BoolField` and `DatetimeField`.


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
