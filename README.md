# Bonfig

    pip install bonfig

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
* Pull in values from various sources into one neatly packaged class.
* Get all the power that comes with classes built into your configurations - polymorphism, custom methods and custom initialisation.
* Sleep safe in the knowledge your config won't change unexpectedly with configuration with `Bonfig.freeze`.
* Ready made serialisation and deserialisation with custom `Fields` - `IntField`, `FloatField`, `BoolField` and `DatetimeField`, with [tools to help you easily define your own](https://0hughman0.github.io/bonfig/api.html#bonfig.fields.FieldDict.add).

Please checkout the project docs for more information: https://0hughman0.github.io/bonfig/index.html

