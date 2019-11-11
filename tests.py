import pytest
import datetime
import pathlib

from bonfig import Bonfig, Store
from bonfig.fields import fields, Field, Section


def test_section():

    class Config(Bonfig):
        s = Store()
        A = s.Section()
        B = s.Section()

        C = B.Section()
        D = C.Section()

        a = A.Field('Aa')
        b = B.Field('Bb')
        c = C.Field('Cc')
        d = D.Field('Dd')

    c = Config()

    assert c.A.keys == ['A']
    assert c.A.name == 'A'

    assert c.B.keys == ['B']
    assert c.B.name == 'B'

    assert c.C.keys == ['B', 'C']
    assert c.C.name == 'C'

    assert c.D.keys == ['B', 'C', 'D']
    assert c.D.name == 'D'

    assert c.s == {'A': {'a': 'Aa'},
                   'B': {'b': 'Bb',
                         'C': {'c':'Cc',
                               'D': {'d': 'Dd'}}}}


def test_env_field():
    import os
    os.environ['TEST'] = 't'

    class TestBonfig(Bonfig):
        env = Store()
        denv = Store()
        a = env.Field(name='TEST')
        b = env.Field(name='BEST', default='fallback')
        c = denv.Field(name='TEST')
        e = denv.Field(name='BEST', default='fallback')

        def load(self):
            self.env = dict(os.environ) # a copy
            self.denv = os.environ # the real thing!

    c = TestBonfig(frozen=False)

    assert c.a == 't'
    assert c.b == 'fallback'
    assert c.c == 't'
    assert c.e == 'fallback'

    os.environ['Test'] = 'changed'
    os.environ['Best'] = 'also changed'
    assert c.a == 't'
    assert c.b == 'fallback'
    assert c.c == 'changed'
    assert c.e == 'also changed'


def test_custom_field():
    @fields.add
    class ListField(Field):

        def __init__(self, val=None, default=None, name=None, *, _store=None, _section=None, sep=', '):
            super().__init__(val, default=default, name=name, _store=_store, _section=_section)
            self.sep = sep

        def _post_get(self, val):
            return val.split(self.sep)

        def _pre_set(self, val):
            return self.sep.join(val)

    todd = ['1', '2', '3']
    teven = ['2', '4', '6']

    class TestBonfig(Bonfig):
        d = Store()
        odd = d.ListField(todd)
        lists = d.Section()
        even = lists.ListField(val=teven)

    c = TestBonfig()

    assert c.d['odd'] == "1, 2, 3"
    assert c.odd == todd

    assert c.d['lists']['even'] == "2, 4, 6"
    assert c.even == teven


def test_ini():
    import configparser

    class TestBonfig(Bonfig):
        ini = Store()

        A = ini.Section()
        a = A.Field()
        b = A.Field()

        def load(self):
            self.ini = configparser.ConfigParser()
            self.ini.read_string("[A]\na = one\nb=two")

    c = TestBonfig()

    assert c.a == 'one'
    assert c.b == 'two'


def test_inherit():
    class BaseConfig(Bonfig):
        s = Store()
        a = s.Field('a')
        b = s.Field('b', name='manual b')

    class AddFields(BaseConfig):
        c = BaseConfig.s.Field('c')
        d = BaseConfig.s.Field('d')

    c = AddFields()
    assert c.a == 'a'
    assert c.b == 'b'
    assert c.c == 'c'
    assert c.d == 'd'

    class OverwriteFields(AddFields):
        a = BaseConfig.s.Field('not a')
        c = AddFields.s.Field('not c')

    c = OverwriteFields()
    assert c.a == 'not a'
    assert c.b == 'b'
    assert c.c == 'not c'
    assert c.d == 'd'

    assert OverwriteFields.__fields__ == set((OverwriteFields.a, BaseConfig.b, OverwriteFields.c, AddFields.d))

    class SecondInherit(OverwriteFields):
        c = BaseConfig.s.Field('still not c')

    c = SecondInherit()
    assert c.a == 'not a'
    assert c.b == 'b'
    assert c.c == 'still not c'
    assert c.d == 'd'
    assert SecondInherit.__fields__ == set((OverwriteFields.a, BaseConfig.b, SecondInherit.c, AddFields.d))


def test_load():
    class TestConfig(Bonfig):
        d = Store()
        a = d.Field()
        b = d.Field()

        def load(self, *args, **kwargs):
            self.d = {'a': args[0],
                      'b': kwargs['b']}

    c = TestConfig('one', b='two')

    assert c.a == 'one'
    assert c.b == 'two'


def test_withmad():
    # As shortener
    class A(Bonfig):
        store = Store()

        with store as s:
            a = s.Field('A')
            section = s.Section()
            with section as sec:
                b = sec.Field('B')

    class B(Bonfig):
        with Store() as store:
            a = store.Field('A')

            with store.Section() as section:
                b = section.Field('B')

    class C(Bonfig):
        store = Store()

        a = store.Field('A')

        section = store.Section()
        b = section.Field('B')

    ca, cb, cc = A(), B(), C()

    cs = [ca, cb, cc]
    Cs = [A, B, C]

    for c, C in zip(cs, Cs):
        assert c.__store_attrs__ == {'store'}
        assert c.a == 'A'
        assert c.b == 'B'
        assert C.a.keys == ['a']
        assert C.b.keys == ['section', 'b']


def test_special_fields():
    class Config(Bonfig):
        s = Store()
        A = s.Field('a')
        B = s.IntField(100)
        C = s.FloatField(1.75)
        D = s.BoolField(False)
        E = s.DatetimeField(datetime.datetime(2010, 10, 10), fmt='%d/%m/%y')
        F = s.PathField("TestDir")

    c = Config()

    assert c.A == 'a'
    assert c.B == 100
    assert c.C == 1.75
    assert c.D is False
    assert c.E == datetime.datetime.strptime("10/10/10", "%d/%m/%y")
    assert c.F == pathlib.Path("TestDir")

    assert c.s['A'] == 'a'
    assert c.s['B'] == '100'
    assert c.s['C'] == '1.75'
    assert c.s['D'] == 'False'
    assert c.s['E'] == "10/10/10"
    assert c.s['F'] == "TestDir"


def test_field_operators():
    class Config(Bonfig):
        s = Store()

        A = s.Field("A")
        B = A + 'B'
        AB = A + B

        C = s.PathField('Home')
        D = C / 'SubDir'
        CD = C / D

        E = s.IntField(5)
        F = E + 8
        EF = E + F

    c = Config()

    assert c.A == 'A'
    assert c.B == "AB"
    assert c.AB == 'AAB'

    assert c.C == pathlib.Path('Home')
    assert c.D == pathlib.Path('Home') / 'SubDir'
    assert c.CD == pathlib.Path('Home') / 'Home' / 'Subdir'

    assert c.E == 5
    assert c.F == 13
    assert c.EF == 18


def test_exceptions():
    with pytest.raises(AttributeError, match='Foo'):
        class Config(Bonfig):
            store = Store()
            a = store.Foo

    with pytest.raises(ValueError, match="Parameter store cannot be None"):
        class Config(Bonfig):
            a = Field()

    with pytest.raises(ValueError, match="Store must be set for Sections."):
        class Config(Bonfig):
            a = Section()


def test_freeze():

    class Config(Bonfig):
        s = Store()
        a = s.Field(1)
        b = s.Field(2)

    c = Config()

    assert c.a == 1
    assert c.b == 2

    with pytest.raises(TypeError):
        c.a = 4

    import configparser

    class TestBonfig(Bonfig):
        ini = Store()

        A = ini.Section()
        a = A.Field()
        b = A.Field()

        def load(self):
            self.ini = configparser.ConfigParser()
            self.ini.read_string("[A]\na = one\nb=two")

    c = TestBonfig()

    assert c.a == 'one'
    assert c.b == 'two'

    with pytest.raises(TypeError):
        c.a = 'not one'

    class ThreeLevels(Bonfig):
        s = Store()
        A = s.Section()
        a = A.Field('a')

        B = A.Section()
        b = B.Field('b')

        C = B.Section()
        c = C.Field('c')

    c = ThreeLevels()

    with pytest.raises(TypeError):
        c.a = 'not a'

    with pytest.raises(TypeError):
        c.b = 'not b'

    with pytest.raises(TypeError):
        c.c = 'not c'
