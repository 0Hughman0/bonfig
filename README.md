# Bonfig

## Installation

    pip install bonfig

Bonfig aims to provide a more beautiful way to create and use configurations.

The two core ideas are:

    1. Enable the creation of configurations using a class declaration.
    2. Things are less stressful when the underlying data in a configuration is kept serialisable

Bonfig works with `configparser` to make creating configs fun:

    from bonfig import PyBonfig

    class MyConfig(PyBonfig):

        output = PySection('Output')
        a = output.PyField(default='foo')
        b = output.PyFloatField(default=3.1416)
        c = output.PyIntField(default=6543)

    c = MyConfig()
    print(c.a) # -> 'a'
    print(c.c) # -> 3.1416
    c.c = 325
    print(c.c) # -> 325

(Note that for Python < 3.6 all Fields have to be named explicitly - see
[here](https://docs.python.org/3/reference/datamodel.html#object.__set_name__))

Hidden inside the `PyBonfig` instance is a `ConfigParser` object storing all the info, which is easily accessible, with
`d`.

    >>> c.d
    <configparser.ConfigParser at 0x231b5403208>
    >>> c.d._sections # peer inside config parser
    OrderedDict([('Output',
              OrderedDict([('a', 'foo'), ('b', '3.1316'), ('c', '325')]))])



As you can see, internally, the data is always stored as strings. Some 'ready-made' field types that implicitly convert
values to and from strings as they are 'get' and 'set' are provided: IntField, FloatField and BoolField.

Custom 'get' and 'set' behaviour is simple to achieve by subclassing `Field` and using the `pre_set` and `post_get`
hooks:

    @pyfields.add # makes available to PySection objects
    class PyTimeField(PyField):

        def post_get(self, val):
            return datetime.time(int(val))

        def pre_set(self, val):
            return str(val.hour)

    class MyConfig(PyBonfig):

        output = PySection('Output')
        a = output.PyField(default='foo')
        t = output.PyTimeField(default=datetime.time(21))

    c = MyConfig()
    print(c.t) # -> datetime.time(21, 0)

Some shortcuts to creating your own field classes are provided, check out `fields.make_quick` and `pyfields.make_quick`
in `bonfig.py`!

Pleasingly, Bonfig plays nicely with inheritance so you can do cool stuff like:

    class MyBaseConfig(PyBonfig):

        basic = PySection('Basic')
        a = basic.PyField(default='loopy')

    class MyExtendedConfig(MyBaseConfig):

        extra = PySection('Extra')
        b = extra.PyField(default='bar')

    c = MyExtendedConfig()
    c.d._sections # -> OrderedDict([('Extra', OrderedDict([('b', 'bar')])),
             ('Basic', OrderedDict([('a', 'loopy')]))])


If you don't want to use a config parser to store your data, the `Bonfig` class just uses a plain ol' dictionary, which
makes more hierarchical structures possible. (The 'Py' prefix has been used to indicate using `configparser` internally,
and as such is a specialisation of the `Bonfig` class)

Finally, accessing environment variables is also catered for, just use the `EnvField` (works for both `Bonfig` and
`PyBonfigs`):

    class EnvConfig(Bonfig):

        SECRET_KEY = EnvField(default='fallback') # or add name='SECRET_KEY' for Python < 3.6

Check out the docstrings and examples folder for more info.
