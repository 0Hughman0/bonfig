# Bonfig

    >>> import os, json, configparser
    >>> from bonfig import Bonfig, Store
    >>>
    >>> class Config(Bonfig):
    ...     with Store() as basic:
    ...         VERSION = basic.Field('0.2')
    ...
    ...     with Store() as secrets:
    ...         CREDENTIALS = secrets.Field(default="XXXXXX-XX")
    ...         PIN = secrets.IntField(default=1234)
    ...
    ...     with Store() as data:
    ...         SAMPLE = data.Field()
    ...         AVERAGE = data.FloatField()
    ...
    ...     with Store() as prefs:
    ...         with prefs.Section('LINES') as lines:
    ...             X_MARKER = lines.Field()
    ...             SHOW = lines.BoolField()
    ...
    ...         with prefs.Section('META') as meta:
    ...             DATE = meta.DatetimeField(name='start', fmt='%d/%m/%y')
    ...
    ...     def load(self, fn):
    ...         self.basic = {}
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
    >>> c = Config(frozen=False)  # create a mutable version
    >>> c.AVERAGE = 365.2
    >>> c.AVERAGE
    365.2


Stop writing your configurations as dictionaries and strange floating dataclasses, make them `Bonfigs` and make use of
a whole bunch of great features:

* Declare your configurations as easy to read classes.
* Pull in values from various sources into one neatly packaged class.
* Get all the power that comes with classes built into your configurations - polymorphism, custom methods and custom initialisation.
* Sleep safe in the knowledge your config won't change unexpectedly with configuration with `Bonfig.freeze`.
* Ready made serialisation and deserialisation with custom `Fields` - `IntField`, `FloatField`, `BoolField` and `DatetimeField`, with [tools to help you easily define your own](https://0hughman0.github.io/bonfig/api.html#bonfig.fields.FieldDict.add).

## Installation

    pip install bonfig

Please checkout the project docs for more information: https://0hughman0.github.io/bonfig/index.html

