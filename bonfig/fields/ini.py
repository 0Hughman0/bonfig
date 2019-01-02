from bonfig.fields.base import BaseField, FieldDict, str_bool
from bonfig.fields.field import Section


class INIField(BaseField):
    """
    Subclass of Field whereby data is stored in a `configparser.ConfigParser` object named `parser`.

    Parameters
    ----------
    section : str
        name of section option belongs to.7
    name : str
        name of parameter option. (optional - defaults to variable name assigned to)
    default : obj
        value to default to!

    Notes
    -----
    Differs slightly from normal `Field` in that rather that taking the more general `path`, you have to provide a
    name and a section, in order to work with `ConfigParser`

    Rather than putting in the same section each time, you can make a `INISection` object...

    Omitting default will result in no values being entered in the data attr upon initialisation, which might
    make the structure of the data attr look a bit weird until you fill it up with stuff.
    """

    _store_attr = 'ini'

    def __init__(self, section, default=None, name=None):
        self.section = section
        self.default = default
        self.name = name

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name

    def initialise(self, bonfig):
        store = self.get_store(bonfig)
        if self.section not in store:
            store[self.section] = {}
        if self.default:
            self.get_store(bonfig)[self.section][self.name] = self.pre_set(self.default)

    def _get_value(self, store):
        return store[self.section][self.name]

    def _set_value(self, store, value):
        store[self.section][self.name] = value


INIfields = FieldDict(INIField)
INIIntField = INIfields.make_quick('INIIntField', int, str)
INIFloatField = INIfields.make_quick('INIFloatField', float, str)
INIBoolField = INIfields.make_quick('INIBoolField', str_bool, str)


class INISection(Section):
    """
    Convenience class for building up `Bonfig`s. Corresponds to 'sections' in `configparser.ConfigParser` objects.

    Parameters
    ----------
    name : str
        name of section

    Examples
    --------
    CSections make building up these configs a bit nicer:

    >>> class MyConfig(Bonfig):
    >>>     output = INISection('Output')
    >>>     A = output.INIField('a', default='foo')
    >>>     B = output.INIField('b', default='bar')
    >>> c = MyConfig()
    >>> c.d
    <configparser.ConfigParser at 0x231b53f5eb8>
    >>> c.d._sections #  peer inside the config parser!
    OrderedDict([('Output', OrderedDict([('a', 'foo'), ('b', 'bar')]))])

    All `INIfields` are available as attributes of the CSection instance, and the `section` parameter will implicitly be
    set.
    """

    field_types = INIfields

    def __init__(self, name):
        if not isinstance(name, str):
            raise TypeError("INISections have to be at the top level for ConfigParser configurations, so name has to be"
                            "as string")
        super().__init__(name)

    def wrap_field(self, cls):
        """
        fill in section parameter as self for any class!
        """

        def wrapped_py_field(default=None, name=None, **kwargs):
            return cls(self.name, default, name, **kwargs)

        return wrapped_py_field
