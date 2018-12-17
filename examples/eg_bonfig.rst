Using Bonfig and Fields/ Sections
=================================

In order for your Config to initalise properly, you need to inherit from Bonfig.

.. code:: python

    class BasicConfig(Bonfig):

        # Sections group fields together
        output = Section('Output')

        # You can explicitly set the name of your Field, as well as a default value
        A = output.Field('foo', 'A Really Long Descriptive Name')
        # Omitting the name, it will default to the variable name you assigned it to e.g. in this case B (for Python >= 3.4)
        B = output.Field('bar')
        # Specialised subclasses of Field are available that are able to serialise and deserialise values.
        C = output.IntField('c')

        # or without using a Section object:
        #
        separate = Field(('Out on a limb', 'lonely'), val='hmmm')

    c = BasicConfig()
    print(c.d) # {'Output': {'A Really Long Descriptive Name': 'foo', 'B': 'bar'}, 'Out on a limb': {'lonely': 'hmmm'}}
    c.C = 1353
    print(c.C) # 1353
    print(c.d) # {'Output': {'A Really Long Descriptive Name': 'foo', 'B': 'bar', 'c': '1353'}, 'Out on a limb': {'lonely': 'hmmm'}}


Writing a custom Field
======================

.. code:: python
    # Creating a custom PyField
    @fields.add  # this line adds ListField to a dictionary that `Section` looks in when you do Section.ListField
    class ListField(Field):

        def __init__(self, path, val=None, sep=', '):
            super().__init__(path, val)
            self.sep = sep

        def post_get(self, val):
            return val.split(self.sep)

        def pre_set(self, val):
            return self.sep.join(val)


    class CustomConfig(BasicConfig):
        lists = Section('lists')
        even = lists.ListField('even')
        odd = lists.ListField(val=['1', '3', '5', '7', '9'])


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
    class LayeredConfig(Bonfig):

    top = Field(1, ('Val'))
    middle = Field(2, ('Top', 'Val'))
    bottom = Field(3, ('Top', 'Middle', 'Val'))


    >>> c = LayeredConfig()
    >>> c.d
    {'Val': 1, 'Top': {'Val': 2, 'Middle': {'Val': 3}}}
