# Bonfig

Bonfig aims to provide a more beautiful way to create and use configurations.

The two core ideas are:

    1. Enable the creation of configurations using a class declaration.
    2. Things are less stressful when the underlying data in a configuration is kept serialisable

Bonfig works with `configparser` to make creating configs fun:

    from bonfig import PyBonfig

    class MyConfig(PyBonfig):

        output = PySection('Output')
        A = output.PyField('a', default='foo')
        B = output.PyField('b', default='bar')
        C = output.PyIntField('c', default=6543)

    c = MyConfig()
    print(c.A) # -> 'a'
    print(c.C) # -> 6543
    c.C = 325
    print(c.C) # -> 325

Hidden inside the `PyBonfig` instance is a `ConfigParser` object storing all the info, which is easily accessible, with
`d`.

    >>> c.d
    <configparser.ConfigParser at 0x231b5403208>
    >>> c.d._sections # peer inside config parser
    OrderedDict([('Output',
              OrderedDict([('a', 'foo'), ('b', 'bar'), ('c', '325')]))])

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
        A = output.PyField('a', default='foo')
        T = output.PyTimeField('t', default=datetime.time(21))

    c = MyConfig()
    print(c.T) # -> datetime.time(21, 0)

Some shortcuts to creating your own field classes are provided, check out `fields.make_quick` and `pyfields.make_quick`
in `bonfig.py`!

Pleasingly, Bonfig plays nicely with inheritance so you can do cool stuff like:

    class MyBaseConfig(PyBonfig):

        basic = PySection('Basic')
        A = basic.PyField('a', default='loopy')

    class MyExtendedConfig(MyBaseConfig):

        extra = PySection('Extra')
        B = extra.PyField('b', default='bar')

    c = MyExtendedConfig()
    c.d._sections # -> OrderedDict([('Extra', OrderedDict([('b', 'bar')])),
             ('Basic', OrderedDict([('a', 'loopy')]))])


If you don't want to use a config parser to store your data, the `Bonfig` class just uses a plain ol' dictionary, which
makes more hierarchical structures possible. (The 'Py' prefix has been used to indicate using `configparser` internally,
and as such is a specialisation of the `Bonfig` class)

Check out the docstrings and examples folder for more info.

