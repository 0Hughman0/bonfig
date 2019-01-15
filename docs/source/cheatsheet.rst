Cheat Sheet
==========

Rather than a cheatsheet, here's a phat Bonfig:

.. code:: python3

    >>> import os, json, configparser
    >>> from bonfig import Bonfig, Store
    >>>
    >>> class Config(Bonfig):
    ...     # Context managers are redundant, but potentially look nicer...?
    ...     with Store() as basic:
    ...         VERSION = basic.Field('0.2')
    ...
    ...     with Store() as secrets:
    ...         # default parameter is used as fallback if Field.name not found in its store
    ...         CREDENTIALS = secrets.Field(default="XXXXXX-XX")
    ...         PIN = secrets.IntField(default=1234)  # convert string value to integer on getting
    ...
    ...     with Store() as data:
    ...         # Leaving val blank means no value is inserted after load
    ...         SAMPLE = data.Field()
    ...         AVERAGE = data.FloatField()  # convert string value to float
    ...
    ...     with Store() as prefs:
    ...         # Prepends all Field.keys belonging to lines with 'LINES'
    ...         with prefs.Section('LINES') as lines:  # Section name manually set to 'LINES'
    ...             X_MARKER = lines.Field()
    ...             SHOW = lines.BoolField()
    ...
    ...         with prefs.Section('META') as meta:
    ...             # fetch from store (prefs) with key 'start'
    ...             DATE = meta.DatetimeField(name='start', fmt='%d/%m/%y')  # fmt is a datetime fmt string
    ...
    ...     def load(self, fn):
    ...         self.basic = {}
    ...         # Taking a copy of os.environ ensures parameter values won't change if env values change!
    ...         self.secrets = dict(os.environ)
    ...
    ...         with open(f"examples/{fn}.json") as f:
    ...             self.data = json.load(f)
    ...
    ...         with open(f"examples/{fn}.ini") as f:
    ...             self.prefs = configparser.ConfigParser()
    ...             self.prefs.read_file(f)
    ...
    >>> c = Config("bonfig")
    >>> c.VERSION
    '0.2'
    >>> c.CREDENTIALS
    "XXXXXX-XX"
    >>> c.AVERAGE
    3.14159
    >>> c.SHOW
    True
    >>> c.DATE
    datetime.datetime(1982, 11, 18, 0, 0)
    >>> c.SHOW = False
    AttributeError: Attempting to mutate attribute SHOW on a locked Bonfig
    >>> c.unlock()
    >>> c.SHOW = False
    >>> c.SHOW
    False
    >>> c.lock()