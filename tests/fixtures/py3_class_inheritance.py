class Foo(object):
    pass


class Bar:
    pass


class Fnord(Foo, Bar):
    pass


class FooSub(metaclass=Foo):
    pass
