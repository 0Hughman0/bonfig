# Bonfig

    from Bonfig import Bonfig, Store
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
* Sleep safe in the knowledge your config won't change unexpectedly.
* Ready made serialisation and deserialisation with readmade custom `Fields` - `IntField`, `FloatField`, `BoolField` and `DatetimeField`.

## Installation

    pip install bonfig

Please checkout the project on github for more information: https://0hughman0.github.io/bonfig/index.html

