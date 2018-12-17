import json

from bonfig.core import BaseField, BaseIOStore, FieldDict
from bonfig.fields.field import Field, Section


class JSONStore(dict, BaseIOStore):

    def __init__(self, parent):
        super().__init__()
        BaseIOStore.__init__(self, parent)

    dumps = BaseIOStore._method_chainify()(json.dumps)
    dump = BaseIOStore._method_chainify()(json.dump)

    load = BaseIOStore._method_chainify(True)(json.load)
    loads = BaseIOStore._method_chainify(True)(json.loads)


class JSONField(Field):
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

    _store_attr = 'json'

    def create_store(self, parent):
        return JSONStore(parent)

    def initialise(self, bonfig):
        dd = bonfig.json
        d = dd
        for key in self.path[:-1]:
            try:
                d = d[key]
            except KeyError:
                d[key] = {}
                d = d[key]
        bonfig.d = dd
        self._set_value(getattr(bonfig, self._store_attr), self.pre_set(self.val))

JSONfields = FieldDict(JSONField)
JSONIntField = JSONfields.make_quick('JSONIntField', int, str)
JSONFloatField = JSONfields.make_quick('JSONFloatField', float, str)
JSONBoolField = JSONfields.make_quick('JSONBoolField', bool, str)


class JSONSection(Section):
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

    field_types = JSONfields
