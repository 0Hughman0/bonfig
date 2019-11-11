.. _quickstart:

Quickstart
==========

Installation
------------

To install Bonfig simply run::

    pip install bonfig

Note that Bonfig requires Python version 3.4 or greater, and has no external dependencies.


Getting Started
---------------

Basic Bonfig
~~~~~~~~~~~~

Here is a super basic Bonfig:

>>> from bonfig import Bonfig, Store
>>> class Config(Bonfig):
...     store = Store()
...     A = store.Field('a value')
...     B = store.Field(10, name='Berty')

We create a Bonfig by declaring a class that inherits from the baseclass :py:class:`.Bonfig`.

Then we say we want to store configuration values in an attribute called `store` by assigning a :py:class:`.Store` to
its value.

Following from that we create Fields `A` and `B` whose values we'll store in our `store`, and we
set `B`'s name to `'Berty'`.

So now we can create an instance of `Config`:

>>> c = Config()

And we can fetch parameters from that instance:

>>> c.A
'a value'
>>> c.B
10

By default, Bonfig instances are created and then 'frozen', meaning that parameters cannot be set:

>>> c.A = 'Overwrite'
TypeError: 'mappingproxy' object does not support item assignment

However you can prevent the freezing process by setting keyword argument `frozen` to false when creating your Bonfig
instance.

>>> c = Config(frozen=False)
>>> c.A = 'Overwrite'
>>> c.A
'Overwrite'

Bonfig also plays well with inheritance, for example if we wanted to extend `Config` with a few more attributes, that's
no problem:

>>> class ExtraConfig(Config):
...     extra_store = Store()
...     C = extra_store.Field(3.14159)
...
>>> c = ExtraConfig()
>>> c.A
'a value'
>>> c.C
3.14159

Using Different Stores
~~~~~~~~~~~~~~~~~~~~~~

So far, nothing has really happened that you can't do with a regular class.

But let's look at our `ExtConfig` instance `c` let's check out the values of `store` and `extra_store`:

>>> c.store
mappingproxy({'A': 'a value', 'Berty': 10})
>>> c.extra_store
mappingproxy({'C': 3.14159})

We can see that the values of our `Fields` are actually stored in their respective stores. Oh yes, and the key by which
`c.B` is stored by is `'Berty'` as we set all the way up the top (I knew there was a reason)!

Despite first impressions, there is no magic here, it's just Python. Once our Config has been defined, behind the scenes, Bonfig sets up
2 additional class attributes:

>>> ExtraConfig.__fields__
{<Field 'A' stored in store: val=a value, default=None>,
 <Field 'Berty' stored in store: val=10, default=None>,
 <Field 'C' stored in extra_store: val=3.14159, default=None>}
>>> ExtraConfig.__store_attrs__
{'extra_store', 'store'}

Upon initialisation of our Config, these are used by :py:meth:`.Bonfig.load`, which replaces the `Store` class attributes with
dictionaries as instance attributes of the same name:

.. code:: python

    ...     def load(self, *args, **kwargs):
    ...         for store_attr in self.__store_attrs__:
    ...             setattr(self, store_attr, {})

Each field knows which store it belongs to, and where its value is stored, so when you ask an instance for a `Field`
value it's actually just looking it up in its store.

You might wonder why go to all this fuss to control where attribute values are stored, however this makes sense if you
want to start loading and storing values from various places.

For example, perhaps you want to load values from JSON, whilst others are fixed for your configuration. By overloading
the :py:meth:`.Bonfig.load` method, we can initialise :py:class:`.Field` values from this JSON:

>>> import json
>>> class JSONBonfig(Bonfig):
...     json_store = Store()
...     A = json_store.Field()  # Leaving val blank ensures values loaded in load won't be overwritten during Field.initialise
...     dict_store = Store()
...     B = dict_store.Field(360)
...
...     def load(self):
...         self.dict_store = {}
...         self.json_store = json.loads('{"A": 180}')

And now we can seamlessly access attributes loaded in completely different ways on our configuration:

>>> c = JSONBonfig()
>>> c.A
180
>>> c.B
360

Sections
~~~~~~~~

A common format for loading configurations is the `.ini` format. These files can be parsed using the standard
`configparser` module, storing them as a dictionary like object - `configparser.ConfigParser`.

In the above examples, our `Store` is converted into a dictionary, however, we can very easily modify this behaviour by
overloading the `load` method. Bonfig really doesn't care *what* the store ends up being as all it does is try to use
`__getitem__` and `__setitem__`. So if your object can do that, it'll work as a store for `Fields`.
As it happens `configparser.ConfigParser` objects fit the bill, as such they work great as Stores.

However, `.ini` files require each value to be looked up both by a key and a section.

Bonfig can help you out with this by providing the :py:class:`.Section` type, that make it easier to build up hierarchical
structures:

>>> import configparser
>>> class INIConfig(Bonfig):
...     store = Store()
...     SECTION = store.Section()
...     A = SECTION.Field()
...
...     def load(self):
...         self.store = configparser.ConfigParser()
...         self.store.read_string("[SECTION]\nA = Value")
...
>>> ini = INIConfig(frozen=False)  # Don't implicitly turn store into MappingProxy

And looking at `ini` expectedly we see:

>>> ini.A
'Value'
>>> ini.store
<configparser.ConfigParser at 0x14927ee9470>

But how does `c.A` find its value `c.store`? Well we know it *could* find it like:

>>> ini.store['SECTION']['A']

And in-fact this is exactly what `INIConfig.A` does! Every `Field` has an attribute :py:attr:`.Field.keys`:

>>> INIConfig.A.keys
['SECTION', 'A']

When a `Field` fetches its value, Bonfig will try each key in this list heading deeper into a Store until it runs out
of keys, when it will return the value found. Any `Field` created by a `Section` will have that section's name prepended
to its `keys` attribute.

Typed Fields
~~~~~~~~~~~~

Going back to the `.ini` example, the values found in `configparser.ConfigParser` objects can only be strings, which
can cause issues:

>>> class INI2Config(INIConfig):
...     NUM = INIConfig.SECTION.Field()
...     def load(self):
...         self.store = configparser.ConfigParser()
...         self.store.read_string("[SECTION]\nkey = Value\nNUM = 123")
>>> c = INI2Config(frozen=False)
>>> c.NUM
'123'  # meh

Luckily, Bonfig provides the specialised `Field` types - :py:class:`.IntField`, :py:class:`.FloatField`,
:py:class:`.BoolField`, :py:class:`.DatetimeField` and :py:class`.PathField`.

These convert values *from* their given type to strings as they are inserted into their `Store` (using a method called
`pre_set`), and then convert them back *into* their given type as after they're fetched from their `Store` (using a method
called `post_get`). This means these types can still be used in configurations, even if their `Store` is only compatible
with strings:

>>> class FixedINI(INI2Config):
...     NUM = INI2Config.SECTION.IntField()
>>> c = FixedINI(frozen=False)
>>> c.NUM
123  # Woo!

Bonfig Initialisation Arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The final useful bit of Bonfig that I think is really worth knowing about is that you can pass positional and keyword
arguments to :py:meth:`.Bonfig.load`:

>>> class Argumentative(Bonfig):
...     store = Store()
...     A = store.Field()
...     B = store.Field()
...
...     def load(self, a, b):
...         self.store = {'A': a,
...                       'B': b}
...
>>> c = Argumentative('foo', 'bar')
>>> c.A
'foo'
>>> c.B
'bar'

Any arguments provided to `__init__` are passed on to `load` (apart from `frozen`!).

Going Easier on the Eyes
~~~~~~~~~~~~~~~~~~~~~~~~

In an effort to make your Bonfigs look a bit nicer, you can use `Stores` and `Sections` as context managers which
creates a nice visual indent making visible where a section starts and ends. Additionally, it can get a bit tedious
writing `store.X`, `section.Y` all the time, so you can also use the `as` keyword to provide an alias for them. All of
this can help tidy up complex Bonfigs.

>>> class Long(Bonfig):
...     store = Store()
...
...     with store.Section('Alphabety') as A:
...         Aa = A.Field('a')
...         Ab = A.Field('b')
...         Ac = A.Field('c')
...         Ad = A.Field('d')
...
...         with store.Section() as B:
...             ABa = B.Field('e')
...             ABb = B.Field('f')
...             ABc = B.Field('g')
...             ABd = B.Field('h')
...
...     super_long_store_attr = Store()
...
...     with super_long_store_attr as s:
...         FINALLY = s.Field('What a major keystroke saver!')
...
>>> c = Long()
>>> c.store
mappingproxy({'Alphabety': {'Aa': 'a', 'Ab': 'b', 'Ac': 'c', 'Ad': 'd'},
 'B': {'ABa': 'e', 'ABb': 'f', 'ABc': 'g', 'ABd': 'h'}})
>>> c.super_long_store_attr
mappingproxy({'FINALLY': 'What a major keystroke saver!'})
