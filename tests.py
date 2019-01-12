import pytest

from bonfig import Bonfig, Store, Field, Section, fields


def test_section():

    class ConfigA(Bonfig):
        s = Store()
        A = s.Section()
        B = s.Section()

        C = B.SubSection()
        D = C.SubSection()

        a = A.Field('Aa')
        b = B.Field('Bb')
        c = C.Field('Cc')
        d = D.Field('Dd')

        def load(self):
            self.s = {}

    class ConfigB(Bonfig):
        s = Store()

        A = s.Section('A')
        B = s.Section('B')
        C = s.Section('C', supsection='B')
        D = s.Section('D', supsection=('B', 'C'))

        a = A.Field('Aa')
        b = B.Field('Bb')
        c = C.Field('Cc')
        d = D.Field('Dd')

        def load(self, *args, **kwargs):
            self.s = {}

    ca = ConfigA()
    cb = ConfigB()

    for c in (ca, cb):
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


def test_set_name_func_field():

    class TestBonfigA(Bonfig):

        a_ = Field(1, store='d', name='a')
        b_ = Field(2, store='d', name='b', section=Section(store='d', name='Sec A'))
        c_ = Field(3, store='d', name='c', section=Section(store='d', supsection='Sec A', name='Sub B'))

        def load(self):
            self.d = {}

    class TestBonfigB(Bonfig):
        d = Store()

        a = d.Field(1)

        s_a = d.Section(name='Sec A')
        b = s_a.Field(2)

        sub_b = s_a.SubSection(name='Sub B')
        c = sub_b.Field(3)

        def load(self):
            self.d = {}

    a = TestBonfigA()
    b = TestBonfigB()

    assert a.d['a'] == b.d['a']
    assert a.d['Sec A']['b'] == b.d['Sec A']['b']
    assert a.d['Sec A']['Sub B']['c'] == b.d['Sec A']['Sub B']['c']

    assert a.a_ == b.a
    assert a.b_ == b.b
    assert a.c_ == b.c


def test_lock():
    class TestBonfigA(Bonfig):
        d = Store()
        a = d.Field(1)

        def load(self):
            self.d = {}

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

    c = TestBonfig()

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

        def __init__(self, val=None, store=None, default=None, section=None, name=None, sep=', '):
            super().__init__(val, store=store, default=default, section=section, name=name)
            self.sep = sep

        def post_get(self, val):
            return val.split(self.sep)

        def pre_set(self, val):
            return self.sep.join(val)

    todd = ['1', '2', '3']
    teven = ['2', '4', '6']

    class TestBonfig(Bonfig):
        d = Store()
        odd = d.ListField(todd)
        lists = d.Section()
        even = lists.ListField(val=teven)

        def load(self, *args, **kwargs):
            self.d = {}

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
        d = Store()
        a = d.Field('a')

        def load(self):
            self.d = {}

    class SubConfig(BaseConfig):
        b = BaseConfig.d.Field('b')

    c = SubConfig()
    assert c.a == 'a'
    assert c.b == 'b'

    class OverloadConfig(SubConfig):
        b = SubConfig.d.Field('not b')

    c = OverloadConfig()
    assert c.b == 'not b'


def test_load():
    class TestConfig(Bonfig):
        d = Store()
        a = d.Field()
        b = d.Field()

        def load(self, *args, **kwargs):
            self.d = {'a': args[0],
                      'b': kwargs['b']}

    c = TestConfig(False, 'one', b='two')

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

        def load(self):
            self.store = {}

    class B(Bonfig):
        with Store() as store:
            a = store.Field('A')

            with store.Section() as section:
                b = section.Field('B')

        def load(self):
            self.store = {}


    class C(Bonfig):
        store = Store()

        a = store.Field('A')

        section = store.Section()
        b = section.Field('B')

        def load(self):
            self.store = {}

    ca, cb, cc = A(), B(), C()

    cs = [ca, cb, cc]
    Cs = [A, B, C]

    for c, C in zip(cs, Cs):
        assert c.__fields__.keys() == {'store'}
        assert c.a == 'A'
        assert c.b == 'B'
        assert C.a.keys == ['a']
        assert C.b.keys == ['section', 'b']
