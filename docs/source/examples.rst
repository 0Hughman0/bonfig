Using Bonfig and Fields/ Sections
=================================

In order for your Config to initalise properly, you need to inherit from Bonfig.

.. code:: python3

    >>> class BasicConfig(Bonfig):
    ...
    ...     output = Section('Output')
    ...
    ...     A = output.Field('foo', 'A Really Long Descriptive Name')
    ...     B = output.Field('bar')
    ...     C = output.IntField('c')
    ...     separate = Field(('Out on a limb', 'lonely'), val='hmmm')
    ...
    >>> c = BasicConfig()
    >>> c.d
    {'Output': {'A Really Long Descriptive Name': 'foo', 'B': 'bar'}, 'Out on a limb': {'lonely': 'hmmm'}}
    >>> c.C = 1353
    >>> c.C
    1353
    >>> c.d
    {'Output': {'A Really Long Descriptive Name': 'foo', 'B': 'bar', 'c': '1353'}, 'Out on a limb': {'lonely': 'hmmm'}}


Writing a custom Field
======================

.. code:: python3

    >>> @fields.add  # this line adds ListField to a dictionary that Section looks in when you do Section.ListField
    >>> class ListField(Field):
    ...
    ...     def __init__(self, path, val=None, sep=', '):
    ...         super().__init__(path, val)
    ...         self.sep = sep
    ...
    ...     def post_get(self, val):
    ...         return val.split(self.sep)
    ...
    ...     def pre_set(self, val):
    ...         return self.sep.join(val)
    ...
    >>> class CustomConfig(BasicConfig):
    ...     lists = Section('lists')
    ...     even = lists.ListField('even')
    ...     odd = lists.ListField(val=['1', '3', '5', '7', '9'])
    ...
    >>> c = CustomConfig()
    >>> c.d
    {'lists': {'odd': '1, 3, 5, 7, 9'},
        'Output': {'A Really Long Descriptive Name': 'foo', 'B': 'bar'},
        'Out on a limb': {'lonely': 'hmmm'}}
    >>> c.even = ['2', '4', '6', '9', '10']
    >>> c.d
    {'lists': {'odd': '1, 3, 5, 7, 9', 'even': '2, 4, 6, 9, 10'},
        'Output': {'A Really Long Descriptive Name': 'foo', 'B': 'bar'},
        'Out on a limb': {'lonely': 'hmmm'}}
    >>> c.even
    ['2', '4', '6', '9', '10']

More hierarchical structures
============================

.. code:: python

    >>> class LayeredConfig(Bonfig):
    ...     top = Field(1, ('Val'))
    ...     middle = Field(2, ('Top', 'Val'))
    ...     bottom = Field(3, ('Top', 'Middle', 'Val'))
    >>> c = LayeredConfig()
    >>> c.d
    {'Val': 1, 'Top': {'Val': 2, 'Middle': {'Val': 3}}}

.. code:: python

    >>> class Config(Bonfig):
    ...     a = Field(12)
    ...     sec = INISection("Section")
    ...     b = sec.INIField("hmmm")
    >>> c = Config()
    >>> c.ini = ConfigParser()
    >>> c.json = json.load()

    >>> class Config(Bonfig):
    ...     a = Field(12)
    ...     sec = INISection("Section")
    ...     b = sec.INIField("hmmm")
    ...
    ...     def load(self):
    ...         self.stores.json.load()
    ...         self.stores.ini.read()

    >>> c = Config().bonstores
    ...         .json.load()
    ...         .ini.read()
    ...         .config
    >>>
    >>> c = Config()
    >>> c.bonstores.json.load()
    >>> c.bonstores.ini.load()
    >>>
    >>> c = Config()
    >>> c.bonstores.json = json.load()
    >>> c.bonstores.ini = configparser.ConfigParser()
    >>> class Config(Bonfig):
    ...     a = Field(12)
    ...     sec = INISection("Section")
    ...     b = sec.INIField("hmmm")
    ...
    ...     def load(self, f):
    ...         self.stores.json.load(f"{f}.json")
    ...         self.stores.ini.read(f"{f}.ini")
    ... c = c(f='config')

