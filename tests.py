import pytest

from bonfig import Bonfig
from bonfig.fields import *


def test_set_name_func_field():

    class TestBonfigA(Bonfig):
        a = Field(1, 'a')
        b = Field(2, ('A', 'b'))

        c = INIField('A', default='val')

    class TestBonfigB(Bonfig):
        a = Field(1)
        b = Field(2, ('A', None))

        c = INIField('A', default='val')

    a = TestBonfigA()
    b = TestBonfigB()

    assert a.d['a'] == b.d['a'], "name paths are not equivalent using __set_name__ mech"
    assert a.d['A']['b'] == b.d['A']['b'], "list paths are not equivalent using __set_name__ mech"
    assert a.ini == b.ini
    assert a.ini['A']['c'] == a.ini['A']['c']


def test_lock():
    class TestBonfigA(Bonfig):
        a = Field('a', 1)
        b = Field(('b', 'c'), 4)
    c = TestBonfigA(locked=True)

    with pytest.raises(RuntimeError):
        c.a = 123

    c.unlock()

    c.a = 123
    assert c.a == 123

    c.lock()

    with pytest.raises(RuntimeError):
        c.a = 1

    assert c.locked is True

    with c:
        assert c.locked is False
        c.a = 300

    assert c.locked is True
    assert c.a == 300


def test_env_field():
    import os
    os.environ['Test'] = 't'

    class TestBonfig(Bonfig):
        a = EnvField('Test')
        b = EnvField('Best', default='fallback')
        c = EnvField('Test', dynamic=True)
        d = EnvField('Best', default='fallback', dynamic=True)

    c = TestBonfig()

    assert c.a == 't'
    assert c.b == 'fallback'
    assert c.c == 't'
    assert c.d == 'fallback'

    os.environ['Test'] = 'changed'
    os.environ['Best'] = 'also changed'
    assert c.a == 't'
    assert c.b == 'fallback'
    assert c.c == 'changed'
    assert c.d == 'also changed'


def test_combo():
    import os
    os.environ['c'] = 'foo'

    class ComboConfig(Bonfig):
        a = Field(val='foo')
        b = INIField('Sec A', default='foo')
        c = EnvField()

    c = ComboConfig()

    assert c.d == {'a': 'foo'}
    assert c.a == 'foo'
    assert c.ini['Sec A']['b'] == 'foo'
    assert c.b == 'foo'
    assert c.environ['c'] == 'foo'
    assert c.c == 'foo'


def test_sections():

    class TestBonfigA(Bonfig):

        A = Section('A')

        a = A.Field('ta')
        b = A.IntField(1)
        c = A.FloatField(0.1)
        e = A.BoolField(False)

    class TestBonfigB(Bonfig):

        a = Field('ta', ('A', 'a'))
        b = IntField(1, ('A', 'b'))
        c = FloatField(0.1, ('A', 'c'))
        e = BoolField(False, ('A', 'e'))

    a = TestBonfigA()
    b = TestBonfigB()

    assert a.d == b.d

    class TestBonfigA(Bonfig):

        A = INISection('A')

        a = A.INIField(default='a')
        b = A.INIIntField(default=1)
        c = A.INIFloatField(default=0.1)
        e = A.INIBoolField(default=False)

    class TestBonfigB(Bonfig):

        a = INIField('A', default='a')
        b = INIIntField('A', default=1)
        c = INIFloatField('A', default=0.1)
        e = INIBoolField('A', default=False)


    a = TestBonfigA()
    b = TestBonfigB()

    assert a.ini == b.ini


def test_custom_field():
    @fields.add
    class ListField(Field):

        def __init__(self, path=None, val=None, sep=', '):
            super().__init__(path, val)
            self.sep = sep

        def post_get(self, val):
            return val.split(self.sep)

        def pre_set(self, val):
            return self.sep.join(val)

    todd = ['1', '2', '3']
    teven = ['2', '4', '6']

    class TestBonfig(Bonfig):
        odd = ListField(todd)
        lists = Section('lists')
        even = lists.ListField(val=teven)

    c = TestBonfig()

    assert c.d['odd'] == "1, 2, 3"
    assert c.odd == todd

    assert c.d['lists']['even'] == "2, 4, 6"
    assert c.even == teven